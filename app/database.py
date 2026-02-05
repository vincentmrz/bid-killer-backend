"""
Gestion de la base de données PostgreSQL
Connexion, sessions et modèles SQLAlchemy
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON
from sqlalchemy.sql import func
from datetime import datetime

from app.config import settings

# ========================================
# DATABASE ENGINE
# ========================================

# Convertir URL PostgreSQL pour async
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries en mode debug
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# ========================================
# MODELS
# ========================================

class User(Base):
    """Utilisateurs de la plateforme"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    company_name = Column(String)
    
    # Subscription
    subscription_tier = Column(String, default="free")  # free, starter, pro, enterprise
    subscription_status = Column(String, default="inactive")  # active, inactive, cancelled
    stripe_customer_id = Column(String, unique=True)
    
    # Quotas
    analyses_limit = Column(Integer, default=0)
    analyses_used = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)


class Subscription(Base):
    """Abonnements Stripe"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Stripe
    stripe_subscription_id = Column(String, unique=True)
    stripe_price_id = Column(String)
    
    # Plan details
    plan_name = Column(String)  # starter, pro, enterprise
    amount = Column(Float)  # Montant en euros
    
    # Status
    status = Column(String)  # active, past_due, cancelled, trialing
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    
    # Quotas
    analyses_limit = Column(Integer)
    analyses_used_this_period = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    cancelled_at = Column(DateTime(timezone=True))


class DCEAnalysis(Base):
    """Analyses de DCE effectuées"""
    __tablename__ = "dce_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Fichiers uploadés
    file_name = Column(String)
    file_size = Column(Integer)
    file_type = Column(String)
    
    # Résultats de l'analyse (JSON)
    analysis_result = Column(JSON)
    
    # Métadonnées projet
    project_name = Column(String)
    client_name = Column(String)
    budget_ht = Column(Float)
    deadline = Column(DateTime(timezone=True))
    
    # Status
    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Archivage
    is_archived = Column(Boolean, default=False)


class GeneratedDocument(Base):
    """Documents générés (DOCX, PDF)"""
    __tablename__ = "generated_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("dce_analyses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Document info
    document_type = Column(String)  # docx, pdf, json
    file_path = Column(String)
    file_size = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    downloaded_at = Column(DateTime(timezone=True))
    
    # Expiration (optionnel - auto-delete après X jours)
    expires_at = Column(DateTime(timezone=True))


class AuditLog(Base):
    """Logs d'audit pour traçabilité"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Action
    action = Column(String)  # login, upload, analyze, download, etc.
    resource_type = Column(String)  # user, analysis, document
    resource_id = Column(Integer)
    
    # Détails
    details = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ========================================
# DATABASE FUNCTIONS
# ========================================

async def init_db():
    """Initialise la base de données (crée les tables)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Ferme les connexions"""
    await engine.dispose()


async def get_db() -> AsyncSession:
    """Dependency pour obtenir une session DB"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
