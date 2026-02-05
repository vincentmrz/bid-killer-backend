"""
Point d'entrée principal de l'application FastAPI
Configuration CORS RENFORCÉE pour monsieurlanding.fr
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.database import engine, Base
from app.routes import auth, users, analysis, subscriptions, export_routes

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    logger.info("🚀 Démarrage de Bid-Killer Engine API...")
    
    # Créer les tables si elles n'existent pas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ Base de données connectée")
    
    yield
    
    logger.info("👋 Arrêt de l'application")

# ========================================
# APPLICATION FASTAPI
# ========================================

app = FastAPI(
    title="Bid-Killer Engine API",
    description="API d'analyse intelligente de DCE BTP",
    version="2.0.0",
    lifespan=lifespan
)

# ========================================
# CONFIGURATION CORS RENFORCÉE
# ========================================

# Liste complète des origines autorisées
ALLOWED_ORIGINS = [
    # Localhost (dev)
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:5173",
    
    # Production
    "https://bid-killer.fr",
    "https://www.bid-killer.fr",
    "https://app.bid-killer.fr",
    
    # Client actuel (IMPORTANT !)
    "https://monsieurlanding.fr",
    "https://www.monsieurlanding.fr",
    "http://monsieurlanding.fr",
    "http://www.monsieurlanding.fr",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Tous les méthodes (GET, POST, PUT, DELETE, OPTIONS)
    allow_headers=["*"],  # Tous les headers
    expose_headers=["*"],  # Expose tous les headers dans la réponse
    max_age=3600,  # Cache preflight pendant 1 heure
)

# ========================================
# ROUTES
# ========================================

@app.get("/")
async def root():
    """Endpoint de santé"""
    return {
        "message": "Bid-Killer API Running",
        "version": "2.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health():
    """Healthcheck pour Railway"""
    return {"status": "ok"}

# Inclure les routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["Subscriptions"])
app.include_router(export_routes.router, prefix="/api/export", tags=["Export"])

# ========================================
# HANDLER D'ERREURS
# ========================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global pour les exceptions"""
    logger.error(f"Erreur non gérée : {str(exc)}")
    return {
        "error": "Une erreur est survenue",
        "detail": str(exc)
    }

# ========================================
# MIDDLEWARE DE LOGGING (optionnel)
# ========================================

@app.middleware("http")
async def log_requests(request, call_next):
    """Log toutes les requêtes"""
    logger.info(f"📥 {request.method} {request.url.path} - Origin: {request.headers.get('origin', 'N/A')}")
    response = await call_next(request)
    logger.info(f"📤 Response status: {response.status_code}")
    return response
