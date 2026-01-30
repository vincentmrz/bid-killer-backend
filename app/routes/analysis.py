"""
Routes d'analyse de DCE
Upload, traitement et résultats
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import List, Optional
import os
import PyPDF2
from datetime import datetime
import json

from app.database import get_db, User, DCEAnalysis
from app.routes.auth import get_current_active_user
from app.services.claude_service import claude_service
from app.config import settings

router = APIRouter()

# ========================================
# SCHEMAS
# ========================================

class AnalysisResponse(BaseModel):
    """Réponse d'analyse"""
    id: int
    status: str
    project_name: Optional[str]
    client_name: Optional[str]
    budget_ht: Optional[float]
    deadline: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]


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


# ========================================
# UTILS
# ========================================

async def extract_text_from_pdf(file_path: str) -> str:
    """Extrait le texte d'un PDF"""
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            # Limiter à 50 pages pour éviter timeout
            max_pages = min(len(pdf_reader.pages), 50)
            
            for page_num in range(max_pages):
                page = pdf_reader.pages[page_num]
                text += f"\n[Page {page_num + 1}]\n"
                text += page.extract_text()
            
            return text
    except Exception as e:
        raise Exception(f"Erreur d'extraction PDF: {str(e)}")


async def check_user_quota(user: User) -> bool:
    """Vérifie si l'utilisateur a encore du quota"""
    return user.analyses_used < user.analyses_limit


async def increment_user_quota(user: User, db: AsyncSession):
    """Incrémente l'usage du quota"""
    user.analyses_used += 1
    await db.commit()


# ========================================
# ROUTES
# ========================================

@router.post("/upload", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def upload_dce(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload et démarre l'analyse d'un DCE
    """
    
    # Vérifier le quota
    if not await check_user_quota(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Quota d'analyses épuisé ({current_user.analyses_limit} analyses/mois). Veuillez upgrader votre abonnement."
        )
    
    # Vérifier le type de fichier
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de fichier non supporté. Extensions autorisées: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Vérifier la taille du fichier
    file.file.seek(0, 2)  # Aller à la fin
    file_size = file.file.tell()
    file.file.seek(0)  # Revenir au début
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fichier trop volumineux. Taille max: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # Créer le dossier d'upload si nécessaire
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Sauvegarder le fichier
    file_path = os.path.join(
        settings.UPLOAD_DIR,
        f"{current_user.id}_{datetime.utcnow().timestamp()}_{file.filename}"
    )
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
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
    
    # Lancer l'analyse en arrière-plan (simplifié pour MVP)
    try:
        # Extraire le texte du PDF
        if file_ext == ".pdf":
            extracted_text = await extract_text_from_pdf(file_path)
        else:
            # Pour Excel, à implémenter
            extracted_text = "Extraction Excel non implémentée dans ce MVP"
        
        # Analyser avec Claude
        analysis_result = await claude_service.analyze_dce(extracted_text)
        
        # Mettre à jour l'analyse
        analysis.status = "completed"
        analysis.analysis_result = analysis_result
        analysis.project_name = analysis_result.get("project_info", {}).get("name")
        analysis.client_name = analysis_result.get("project_info", {}).get("client")
        analysis.budget_ht = analysis_result.get("project_info", {}).get("budget_ht")
        
        # Parser la deadline si présente
        deadline_str = analysis_result.get("project_info", {}).get("deadline")
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
        
    except Exception as e:
        # En cas d'erreur, marquer comme failed
        analysis.status = "failed"
        analysis.error_message = str(e)
        await db.commit()
        await db.refresh(analysis)
    
    return AnalysisResponse(
        id=analysis.id,
        status=analysis.status,
        project_name=analysis.project_name,
        client_name=analysis.client_name,
        budget_ht=analysis.budget_ht,
        deadline=analysis.deadline,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at
    )


@router.get("/history", response_model=List[AnalysisResponse])
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupère l'historique des analyses
    """
    
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
    """
    Récupère les détails d'une analyse spécifique
    """
    
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
    """
    Archive une analyse (soft delete)
    """
    
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
