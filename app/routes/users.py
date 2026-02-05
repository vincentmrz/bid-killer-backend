"""
Routes de gestion des utilisateurs
Profil, paramètres, quotas
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.database import get_db, User
from app.routes.auth import get_current_active_user, get_password_hash

router = APIRouter()

# ========================================
# SCHEMAS
# ========================================

class UserUpdate(BaseModel):
    """Mise à jour profil utilisateur"""
    full_name: Optional[str] = None
    company_name: Optional[str] = None


class PasswordChange(BaseModel):
    """Changement de mot de passe"""
    current_password: str
    new_password: str


class QuotaInfo(BaseModel):
    """Informations sur les quotas"""
    subscription_tier: str
    subscription_status: str
    analyses_limit: int
    analyses_used: int
    analyses_remaining: int
    can_analyze: bool


# ========================================
# ROUTES
# ========================================

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Récupère les informations de l'utilisateur connecté
    Route principale utilisée par le frontend
    """
    analyses_remaining = max(0, current_user.analyses_limit - current_user.analyses_used)
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "company_name": current_user.company_name,
        "subscription_tier": current_user.subscription_tier,
        "subscription_status": current_user.subscription_status,
        "analyses_limit": current_user.analyses_limit,
        "analyses_count": current_user.analyses_used,  # Frontend attend analyses_count
        "analyses_remaining": analyses_remaining,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """
    Récupère le profil complet de l'utilisateur
    Alias de /me pour compatibilité
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "company_name": current_user.company_name,
        "subscription_tier": current_user.subscription_tier,
        "subscription_status": current_user.subscription_status,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }


@router.put("/profile")
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Met à jour le profil utilisateur
    """
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.company_name is not None:
        current_user.company_name = user_update.company_name
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "message": "Profil mis à jour avec succès",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "company_name": current_user.company_name
        }
    }


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change le mot de passe
    """
    from app.routes.auth import verify_password
    
    # Vérifier l'ancien mot de passe
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect"
        )
    
    # Mettre à jour le mot de passe
    current_user.hashed_password = get_password_hash(password_data.new_password)
    
    await db.commit()
    
    return {"message": "Mot de passe modifié avec succès"}


@router.get("/quota", response_model=QuotaInfo)
async def get_quota(current_user: User = Depends(get_current_active_user)):
    """
    Récupère les informations de quota
    """
    analyses_remaining = max(0, current_user.analyses_limit - current_user.analyses_used)
    can_analyze = analyses_remaining > 0
    
    return QuotaInfo(
        subscription_tier=current_user.subscription_tier,
        subscription_status=current_user.subscription_status,
        analyses_limit=current_user.analyses_limit,
        analyses_used=current_user.analyses_used,
        analyses_remaining=analyses_remaining,
        can_analyze=can_analyze
    )


@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Supprime le compte utilisateur (soft delete)
    """
    # Soft delete - désactiver le compte
    current_user.is_active = False
    current_user.subscription_status = "cancelled"
    
    await db.commit()
    
    return {"message": "Compte désactivé avec succès"}
