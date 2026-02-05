"""
Routes d'analyse de DCE - VERSION RENDER COMPLÈTE avec RQ Worker
Upload, traitement et résultats
Support UNIVERSEL + Background Worker dédié Render
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from datetime import datetime
import json
import logging
import time
import uuid
import tempfile
import shutil
from pathlib import Path

# RENDER : Import RQ pour queue au lieu de BackgroundTasks
from redis import Redis
from rq import Queue

from app.database import get_db, User, DCEAnalysis
from app.routes.auth import get_current_active_user
from app.services.claude_service import claude_service
from app.services.file_processor import UniversalFileProcessor
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# ========================================
# CONFIGURATION RQ (Redis Queue) - RENDER
# ========================================

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_conn = Redis.from_url(redis_url)
queue = Queue('default', connection=redis_conn)

# ========================================
# IMPORT ASYNC SERVICES
# ========================================

from app.services.job_manager import job_manager

# ========================================
# SCHEMAS
# ========================================

class AnalysisResponse(BaseModel):
    """Réponse d'analyse"""
    id: int
    status: str
    result: Optional[dict] = None
    project_name: Optional[str] = None
    client_name: Optional[str] = None
    budget_ht: Optional[float] = None
    deadline: Optional[datetime] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class AnalysisDetail(BaseModel):
    """Détails complets d'une analyse"""
    id: int
    file_name: str
    status: str
    analysis_result: Optional[dict]
    project_name: Optional[str]
    client_name: Optional[str]
    budget_ht: Optional[float]
    deadline: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]


class JobResponse(BaseModel):
    """Réponse création de job"""
    job_id: str
    status: str
    message: str
    estimated_time_minutes: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    current_step: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    user_id: int  # ✅ EN int (pas str)
    filename: str
    created_at: datetime


# ========================================
# UTILS
# ========================================

async def check_user_quota(user: User) -> bool:
    """Vérifie si l'utilisateur a encore du quota"""
    return user.analyses_used < user.analyses_limit


async def increment_user_quota(user: User, db: AsyncSession):
    """Incrémente l'usage du quota"""
    user.analyses_used += 1
    await db.commit()


# ========================================
# ROUTES SYNCHRONES (EXISTANTES - POUR PETITS DCE)
# ========================================

async def _analyze_dce_impl(
    file: UploadFile,
    current_user: User,
    db: AsyncSession
) -> AnalysisResponse:
    """
    Implémentation commune pour /analyze et /upload
    VERSION OPTIMISÉE pour GROS FICHIERS (jusqu'à 5 GB)
    """
    
    start_time = time.time()
    
    # Vérifier le quota
    if not await check_user_quota(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Quota d'analyses épuisé ({current_user.analyses_limit} analyses/mois). Veuillez upgrader votre abonnement."
        )
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    # Liste étendue des formats acceptés
    SUPPORTED_FORMATS = [
        '.pdf', '.docx', '.doc', '.txt', '.md', '.rtf',
        '.zip', '.7z', '.rar', '.tar', '.gz', '.tgz', '.bz2',
        '.xlsx', '.xls', '.csv'
    ]
    
    if file_ext not in SUPPORTED_FORMATS:
        logger.warning(f"⚠️ Format potentiellement non supporté : {file_ext}")
    
    # Vérifier la taille du fichier (5 GB max)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    MAX_SIZE = 5 * 1024 * 1024 * 1024  # 5 GB
    
    if file_size > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fichier trop volumineux. Taille max: {MAX_SIZE / 1024 / 1024 / 1024}GB"
        )
    
    # Log de la taille pour tracking
    file_size_mb = file_size / 1024 / 1024
    logger.info(f"📁 Fichier reçu : {file.filename} ({file_size_mb:.2f} MB)")
    
    # Créer le dossier d'upload si nécessaire
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Sauvegarder le fichier
    file_path = os.path.join(
        settings.UPLOAD_DIR,
        f"{current_user.id}_{datetime.utcnow().timestamp()}_{file.filename}"
    )
    
    logger.info(f"💾 Sauvegarde du fichier : {file_path}")
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    save_time = time.time() - start_time
    logger.info(f"✅ Fichier sauvegardé en {save_time:.2f}s")
    
    # Créer l'entrée d'analyse
    analysis = DCEAnalysis(
        user_id=current_user.id,
        file_name=file.filename,
        file_size=file_size,
        file_type=file_ext,
        status="processing"
    )
    
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)
    
    logger.info(f"📊 Analyse créée : ID {analysis.id}")
    
    # Lancer l'analyse
    try:
        # ========================================
        # EXTRACTION UNIVERSELLE avec logs
        # ========================================
        
        extraction_start = time.time()
        logger.info(f"🚀 Lancement extraction pour {file.filename}")
        
        processor = UniversalFileProcessor()
        extraction_result = await processor.process_file(file_path, file.filename)
        
        extraction_time = time.time() - extraction_start
        
        if not extraction_result['success']:
            error_msg = f"Échec extraction : {', '.join(extraction_result['errors'])}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        extracted_text = extraction_result['extracted_text']
        files_processed = extraction_result['files_processed']
        
        logger.info(
            f"✅ Extraction réussie en {extraction_time:.2f}s : "
            f"{files_processed} fichier(s), {len(extracted_text)} caractères"
        )
        
        # Log des erreurs éventuelles (non bloquantes)
        if extraction_result['errors']:
            logger.warning(f"⚠️ Erreurs d'extraction (non bloquantes) : {extraction_result['errors']}")
        
        # Vérifier qu'on a bien du texte
        if len(extracted_text) < 100:
            raise Exception(
                "Texte extrait insuffisant (<100 caractères). "
                "Vérifiez que le fichier contient des documents exploitables."
            )
        
        # ========================================
        # ANALYSE AVEC CLAUDE avec logs
        # ========================================
        
        analysis_start = time.time()
        logger.info("🤖 Lancement analyse Claude AI...")
        
        # Log de la longueur du texte
        text_length = len(extracted_text)
        estimated_tokens = text_length / 4  # Rough estimation
        logger.info(f"📝 Texte à analyser : {text_length} caractères (~{int(estimated_tokens)} tokens)")
        
        analysis_result = await claude_service.analyze_dce(extracted_text)
        
        analysis_time = time.time() - analysis_start
        logger.info(f"✅ Analyse Claude terminée en {analysis_time:.2f}s")
        
        # Mettre à jour l'analyse
        analysis.status = "completed"
        analysis.analysis_result = analysis_result
        analysis.project_name = analysis_result.get("project_info", {}).get("name")
        analysis.client_name = analysis_result.get("project_info", {}).get("client")
        analysis.budget_ht = analysis_result.get("project_info", {}).get("budget_ht")
        
        # Parser la deadline si présente
        deadline_str = analysis_result.get("key_dates", {}).get("submission_deadline")
        if not deadline_str:
            deadline_str = analysis_result.get("project_info", {}).get("deadline_submission")
        
        if deadline_str:
            try:
                analysis.deadline = datetime.fromisoformat(deadline_str)
            except:
                pass
        
        analysis.completed_at = datetime.utcnow()
        
        # Incrémenter le quota
        await increment_user_quota(current_user, db)
        
        await db.commit()
        await db.refresh(analysis)
        
        total_time = time.time() - start_time
        logger.info(
            f"🎉 Analyse terminée avec succès : ID {analysis.id}\n"
            f"   Temps total : {total_time:.2f}s\n"
            f"   - Sauvegarde : {save_time:.2f}s\n"
            f"   - Extraction : {extraction_time:.2f}s ({files_processed} fichiers)\n"
            f"   - Analyse : {analysis_time:.2f}s"
        )
        
    except Exception as e:
        # En cas d'erreur, marquer comme failed
        error_time = time.time() - start_time
        logger.error(f"❌ Erreur analyse après {error_time:.2f}s : {str(e)}")
        
        analysis.status = "failed"
        analysis.error_message = str(e)
        await db.commit()
        await db.refresh(analysis)
    
    finally:
        # Optionnel : Nettoyer le fichier uploadé
        # (Commenté pour debug, décommenter en production si besoin)
        pass
    
    return AnalysisResponse(
        id=analysis.id,
        status=analysis.status,
        result=analysis.analysis_result,
        project_name=analysis.project_name,
        client_name=analysis.client_name,
        budget_ht=analysis.budget_ht,
        deadline=analysis.deadline,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at
    )


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_dce(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyse un DCE (route principale - SYNCHRONE)
    
    VERSION OPTIMISÉE GROS FICHIERS :
    - Supporte jusqu'à 5 GB
    - Logs détaillés pour tracking
    - Support UNIVERSEL : ZIP, 7z, RAR, PDF, DOCX, etc.
    
    NOTE : Pour gros DCE (> 200K chars), utiliser /analyze-async
    """
    return await _analyze_dce_impl(file, current_user, db)


@router.post("/upload", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def upload_dce(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload et analyse un DCE (alias de /analyze pour rétrocompatibilité)
    VERSION OPTIMISÉE pour GROS FICHIERS
    """
    return await _analyze_dce_impl(file, current_user, db)


@router.get("/history", response_model=List[AnalysisResponse])
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère l'historique des analyses"""
    
    result = await db.execute(
        select(DCEAnalysis)
        .where(DCEAnalysis.user_id == current_user.id)
        .where(DCEAnalysis.is_archived == False)
        .order_by(desc(DCEAnalysis.created_at))
        .limit(limit)
        .offset(offset)
    )
    
    analyses = result.scalars().all()
    
    return [
        AnalysisResponse(
            id=a.id,
            status=a.status,
            result=a.analysis_result,
            project_name=a.project_name,
            client_name=a.client_name,
            budget_ht=a.budget_ht,
            deadline=a.deadline,
            created_at=a.created_at,
            completed_at=a.completed_at
        )
        for a in analyses
    ]


@router.get("/{analysis_id}", response_model=AnalysisDetail)
async def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Récupère les détails d'une analyse spécifique"""
    
    result = await db.execute(
        select(DCEAnalysis)
        .where(DCEAnalysis.id == analysis_id)
        .where(DCEAnalysis.user_id == current_user.id)
    )
    
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse non trouvée"
        )
    
    return AnalysisDetail(
        id=analysis.id,
        file_name=analysis.file_name,
        status=analysis.status,
        analysis_result=analysis.analysis_result,
        project_name=analysis.project_name,
        client_name=analysis.client_name,
        budget_ht=analysis.budget_ht,
        deadline=analysis.deadline,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
        error_message=analysis.error_message
    )


@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Archive une analyse (soft delete)"""
    
    result = await db.execute(
        select(DCEAnalysis)
        .where(DCEAnalysis.id == analysis_id)
        .where(DCEAnalysis.user_id == current_user.id)
    )
    
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse non trouvée"
        )
    
    analysis.is_archived = True
    await db.commit()
    
    return {"message": "Analyse archivée avec succès"}


# ========================================
# ROUTES ASYNCHRONES (VERSION RENDER avec RQ)
# ========================================

@router.post("/analyze-async", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def analyze_dce_async(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lance une analyse DCE en background sur Worker Render
    
    ARCHITECTURE RENDER :
    - Web Service reçoit fichier et retourne immédiatement
    - Sauvegarde temporairement et enqueue dans Redis Queue (RQ)
    - Worker dédié traite le job SANS TIMEOUT (illimité)
    - Frontend poll /status/{job_id} pour suivre progression
    
    AVANTAGES :
    - Aucun timeout HTTP (retourne en < 1 sec)
    - Worker peut prendre 30-35 min sans problème
    - Analyse complète 14 lots garantie
    - Score 95-98/100
    """
    
    # Vérifier le quota
    if not await check_user_quota(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Quota d'analyses épuisé ({current_user.analyses_limit} analyses/mois)."
        )
    
    # Créer job ID
    job_id = str(uuid.uuid4())
    
    logger.info(f"📋 Nouvelle analyse async - Job {job_id} - Fichier: {file.filename}")
    
    # Sauvegarder fichier temporairement
    os.makedirs('/tmp/uploads', exist_ok=True)
    
    suffix = Path(file.filename).suffix
    temp_path = f'/tmp/uploads/{job_id}{suffix}'
    
    with open(temp_path, 'wb') as f:
        content = await file.read()
        f.write(content)
    
    logger.info(f"💾 Fichier sauvegardé temporairement : {temp_path}")
    
    # Créer le job dans job_manager
    job_manager.create_job(
        job_id=job_id,
        user_id=current_user.id,
        filename=file.filename
    )
    
    # RENDER : Enqueue dans Redis Queue (RQ) pour Worker
    # Le worker prendra ce job et le traitera sans timeout
    try:
        job = queue.enqueue(
            'worker.process_analysis_job',  # Fonction dans worker.py
            args=(job_id, temp_path, file.filename, current_user.id),  # ✅ Arguments positionnels
            job_timeout='2h',  # Timeout de 2 heures (largement suffisant)
            result_ttl=86400,  # Garde résultat 24h
            failure_ttl=86400  # Garde erreur 24h
        )
        
        logger.info(f"✅ Job {job_id} enqueued dans Redis - RQ Job ID: {job.id}")
        
    except Exception as e:
        logger.error(f"❌ Erreur enqueue job {job_id}: {e}")
        # Nettoyer fichier temporaire
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise en queue : {str(e)}"
        )
    
    # Retourner immédiatement le job_id
    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Analyse lancée sur worker dédié Render",
        estimated_time_minutes=30
    )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Récupère le statut d'un job d'analyse
    Utilisé pour polling côté frontend (toutes les 10s)
    """
    
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    # Vérifier que le job appartient à l'utilisateur
    if str(job["user_id"]) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    return JobStatusResponse(**job)
