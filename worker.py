"""
Background Worker pour Render.com
Traite les jobs d'analyse en background sans timeout
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# --- CORRECTION DU CHEMIN (Important pour Render) ---
# Cela permet à Python de trouver le dossier 'app'
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# ----------------------------------------------------
from redis import Redis
from rq import Worker, Queue, Connection
from app.database import async_session_maker
from app.services.claude_service_async import ClaudeServiceAsync
from app.services.file_processor import UniversalFileProcessor
from app.services.job_manager import job_manager
from app.database import User, DCEAnalysis
from sqlalchemy import select
from datetime import datetime
import tempfile
import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================================
# CONFIGURATION REDIS avec DEBUG
# ========================================

redis_url = os.getenv('REDIS_URL', '')

# DEBUG : Afficher la valeur de REDIS_URL
logger.info("=" * 60)
logger.info("CONFIGURATION REDIS")
logger.info("=" * 60)
logger.info(f"REDIS_URL env variable: '{redis_url}'")

# Vérifier si REDIS_URL est vide ou invalide
if not redis_url:
    logger.error("❌ ERREUR : REDIS_URL n'est pas défini !")
    logger.error("➡️  SOLUTION : Configure REDIS_URL dans Render Dashboard")
    logger.error("    1. Va sur Dashboard Render")
    logger.error("    2. Clique sur bid-killer-redis (database)")
    logger.error("    3. Copie la Connection String")
    logger.error("    4. Va sur bid-killer-worker")
    logger.error("    5. Environment → Add Environment Variable")
    logger.error("    6. Key: REDIS_URL, Value: redis://red-xxx:6379")
    sys.exit(1)

if not redis_url.startswith(('redis://', 'rediss://', 'unix://')):
    logger.error(f"❌ ERREUR : REDIS_URL invalide : '{redis_url}'")
    logger.error("➡️  REDIS_URL doit commencer par redis:// ou rediss://")
    logger.error("    Exemple valide : redis://red-abc123:6379")
    sys.exit(1)

logger.info(f"✅ REDIS_URL valide détecté")

try:
    redis_conn = Redis.from_url(redis_url)
    # Test de connexion
    redis_conn.ping()
    logger.info(f"✅ Connexion Redis réussie : {redis_url}")
except Exception as e:
    logger.error(f"❌ Impossible de se connecter à Redis : {e}")
    logger.error(f"    URL utilisée : {redis_url}")
    sys.exit(1)

# Services
claude_service = ClaudeServiceAsync()

async def process_analysis_job(job_id: str, file_path: str, filename: str, user_id: int):
    """
    Traite une analyse en background
    Cette fonction tourne dans un worker séparé sans timeout
    """
    logger.info(f"🚀 Worker démarre job {job_id}")
    
    temp_file_path = None
    
    try:
        # Créer session DB async
        async with async_session_maker() as db:
            
            # Étape 1 : Extraction (0% → 5%)
            job_manager.set_progress(job_id, 1, "Extraction des fichiers...")
            logger.info(f"📁 Extraction fichier {filename}")
            
            processor = UniversalFileProcessor()
            extraction_result = await processor.process_file(file_path, filename)
            
            if not extraction_result['success']:
                error_msg = f"Échec extraction : {', '.join(extraction_result['errors'])}"
                job_manager.set_failed(job_id, error_msg)
                return {"status": "failed", "error": error_msg}
            
            extracted_text = extraction_result['extracted_text']
            
            job_manager.set_progress(job_id, 5, "Extraction terminée")
            logger.info(f"✅ Extraction réussie : {len(extracted_text)} chars")
            
            # Étape 2 : Analyse Claude (5% → 95%)
            logger.info(f"🤖 Lancement analyse Claude pour job {job_id}")
            
            result = await claude_service.analyze_dce_async(
                extracted_text,
                job_manager,
                job_id
            )
            
            # Étape 3 : Sauvegarde BDD (95% → 100%)
            job_manager.set_progress(job_id, 98, "Sauvegarde des résultats...")
            
            # Récupérer l'utilisateur
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one()
            
            # Créer l'analyse
            analysis = DCEAnalysis(
                user_id=user_id,
                file_name=filename,
                file_size=Path(file_path).stat().st_size if os.path.exists(file_path) else 0,
                file_type=Path(filename).suffix,
                status="completed",
                analysis_result=result,
                project_name=result.get("project_info", {}).get("name"),
                client_name=result.get("project_info", {}).get("client"),
                budget_ht=result.get("project_info", {}).get("budget_ht"),
                completed_at=datetime.utcnow()
            )
            
            # Parser deadline
            deadline_str = result.get("key_dates", {}).get("submission_deadline")
            if not deadline_str:
                deadline_str = result.get("project_info", {}).get("deadline_submission")
            
            if deadline_str:
                try:
                    analysis.deadline = datetime.fromisoformat(deadline_str)
                except:
                    pass
            
            db.add(analysis)
            
            # Incrémenter quota
            user.analyses_used += 1
            
            await db.commit()
            await db.refresh(analysis)
            
            # Marquer job comme terminé
            result_with_id = {
                "analysis_id": analysis.id,
                **result
            }
            
            job_manager.set_completed(job_id, result_with_id)
            
            logger.info(f"✅ Job {job_id} terminé - Analysis ID {analysis.id}")
            
            return {"status": "completed", "analysis_id": analysis.id}
            
    except Exception as e:
        logger.error(f"❌ Erreur job {job_id}: {e}", exc_info=True)
        job_manager.set_failed(job_id, str(e))
        return {"status": "failed", "error": str(e)}
    
    finally:
        # Nettoyer fichier temporaire
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
                logger.info(f"🗑️ Fichier temporaire supprimé : {file_path}")
            except:
                pass


def run_worker():
    """
    Lance le worker RQ qui écoute la queue
    Cette fonction tourne en continu sur Render
    """
    logger.info("=" * 60)
    logger.info("BACKGROUND WORKER - BID KILLER")
    logger.info("=" * 60)
    logger.info(f"🚀 Démarrage du worker Render")
    logger.info(f"📡 Connexion Redis : {redis_url}")
    
    # Créer la queue
    listen = ['default']
    
    with Connection(redis_conn):
        worker = Worker(list(map(Queue, listen)))
        logger.info(f"👂 Worker écoute sur queues : {listen}")
        worker.work(with_scheduler=True)


if __name__ == '__main__':
    run_worker()
