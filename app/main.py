"""
BID-KILLER ENGINE - Backend API
FastAPI application principale
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from app.routes import auth, users, analysis, subscriptions, export_routes
from app.database import init_db, close_db

# ========================================
# LIFECYCLE MANAGEMENT
# ========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    print("🚀 Démarrage de Bid-Killer Engine API...")
    await init_db()
    print("✅ Base de données connectée")
    
    yield
    
    # Shutdown
    print("🛑 Arrêt de Bid-Killer Engine API...")
    await close_db()
    print("✅ Connexions fermées")

# ========================================
# APPLICATION FASTAPI
# ========================================

app = FastAPI(
    title="Bid-Killer Engine API",
    description="API Backend pour l'analyse automatique de DCE BTP",
    version="2.0.0",  # Version mise à jour
    lifespan=lifespan
)

# ========================================
# CORS MIDDLEWARE
# ========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev
        "http://localhost:8080",  # Vue dev
        "https://bid-killer.fr",  # Production
        "https://www.bid-killer.fr",
        "https://app.bid-killer.fr",
        "https://monsieurlanding.fr",  # Client actuel
        "https://www.monsieurlanding.fr",
        "http://monsieurlanding.fr",
        "http://www.monsieurlanding.fr"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# ROUTES
# ========================================

# Health check
@app.get("/")
async def root():
    """Endpoint de santé"""
    return {
        "status": "healthy",
        "service": "Bid-Killer Engine API",
        "version": "2.0.0",
        "message": "API opérationnelle ✅"
    }

@app.get("/health")
async def health_check():
    """Vérification de santé détaillée"""
    return {
        "status": "healthy",
        "database": "connected",
        "api": "operational"
    }

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["Subscriptions"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["DCE Analysis"])
app.include_router(export_routes.router, prefix="/api/export", tags=["Export"])

# ========================================
# ERROR HANDLERS
# ========================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Gestion centralisée des erreurs HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

# ========================================
# MAIN (pour dev local)
# ========================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Hot reload en dev
        log_level="info"
    )
