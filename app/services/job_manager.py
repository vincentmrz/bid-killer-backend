"""
Job Manager pour analyses en background
Permet d'exécuter des analyses longues sans timeout HTTP
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class JobManager:
    """Gestionnaire de jobs d'analyse en background"""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.jobs_dir = Path("/tmp/bid_killer_jobs")
        self.jobs_dir.mkdir(exist_ok=True)
    
    def create_job(self, job_id: str, user_id: str, filename: str) -> Dict[str, Any]:
        """Créer un nouveau job d'analyse"""
        job = {
            "job_id": job_id,
            "user_id": user_id,
            "filename": filename,
            "status": "pending",  # pending, running, completed, failed
            "progress": 0,
            "current_step": "Initialisation...",
            "result": None,
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None
        }
        
        self.jobs[job_id] = job
        self._save_job(job_id)
        
        logger.info(f"📋 Job créé : {job_id} pour {filename}")
        return job
    
    def update_job(self, job_id: str, updates: Dict[str, Any]):
        """Mettre à jour un job"""
        if job_id in self.jobs:
            self.jobs[job_id].update(updates)
            self._save_job(job_id)
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer un job"""
        if job_id in self.jobs:
            return self.jobs[job_id]
        
        # Essayer de charger depuis le fichier
        return self._load_job(job_id)
    
    def set_running(self, job_id: str, step: str = "Analyse en cours..."):
        """Marquer un job comme en cours"""
        self.update_job(job_id, {
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "current_step": step
        })
    
    def set_progress(self, job_id: str, progress: int, step: str):
        """Mettre à jour la progression"""
        self.update_job(job_id, {
            "progress": progress,
            "current_step": step
        })
    
    def set_completed(self, job_id: str, result: Dict[str, Any]):
        """Marquer un job comme terminé"""
        self.update_job(job_id, {
            "status": "completed",
            "progress": 100,
            "current_step": "Analyse terminée",
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        })
    
    def set_failed(self, job_id: str, error: str):
        """Marquer un job comme échoué"""
        self.update_job(job_id, {
            "status": "failed",
            "current_step": "Erreur",
            "error": error,
            "completed_at": datetime.utcnow().isoformat()
        })
    
    def _save_job(self, job_id: str):
        """Sauvegarder un job sur disque"""
        try:
            job_file = self.jobs_dir / f"{job_id}.json"
            with open(job_file, 'w') as f:
                json.dump(self.jobs[job_id], f)
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde job {job_id}: {e}")
    
    def _load_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Charger un job depuis le disque"""
        try:
            job_file = self.jobs_dir / f"{job_id}.json"
            if job_file.exists():
                with open(job_file, 'r') as f:
                    job = json.load(f)
                    self.jobs[job_id] = job
                    return job
        except Exception as e:
            logger.error(f"❌ Erreur chargement job {job_id}: {e}")
        
        return None

# Instance globale
job_manager = JobManager()
