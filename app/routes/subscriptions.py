"""
Routes de gestion des abonnements Stripe
Création, gestion et webhooks
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import stripe
from typing import Optional
from datetime import datetime

from app.database import get_db, User, Subscription
from app.routes.auth import get_current_active_user
from app.config import settings

# Configuration Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()

# ========================================
# SCHEMAS
# ========================================

class CheckoutSessionCreate(BaseModel):
    """Création d'une session checkout Stripe"""
    price_id: str  # ID du plan Stripe (starter, pro, enterprise)
    success_url: str
    cancel_url: str


class SubscriptionInfo(BaseModel):
    """Informations d'abonnement"""
    plan_name: str
    status: str
    current_period_end: Optional[datetime]
    analyses_limit: int
    analyses_used: int
    amount: float


# ========================================
# CONFIGURATION DES PLANS
# ========================================

PLANS_CONFIG = {
    "starter": {
        "name": "Starter",
        "analyses_limit": 20,
        "amount": 49.00
    },
    "pro": {
        "name": "Professional",
        "analyses_limit": 100,
        "amount": 149.00
    },
    "enterprise": {
        "name": "Enterprise",
        "analyses_limit": 999999,  # Illimité
        "amount": 499.00
    }
}

# ========================================
# ROUTES
# ========================================

@router.post("/create-checkout-session")
async def create_checkout_session(
    checkout_data: CheckoutSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crée une session Stripe Checkout
    """
    
    try:
        # Créer un customer Stripe si nécessaire
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.full_name,
                metadata={
                    "user_id": current_user.id,
                    "company": current_user.company_name or ""
                }
            )
            
            current_user.stripe_customer_id = customer.id
            await db.commit()
        
        # Créer la session de checkout
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": checkout_data.price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=checkout_data.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=checkout_data.cancel_url,
            metadata={
                "user_id": current_user.id
            }
        )
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur Stripe: {str(e)}"
        )


@router.get("/current")
async def get_current_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Récupère l'abonnement actuel
    """
    
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.status == "active")
    )
    
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        return {
            "has_subscription": False,
            "plan_name": "free",
            "status": "inactive",
            "analyses_limit": 0,
            "analyses_used": current_user.analyses_used
        }
    
    return {
        "has_subscription": True,
        "plan_name": subscription.plan_name,
        "status": subscription.status,
        "current_period_end": subscription.current_period_end,
        "analyses_limit": subscription.analyses_limit,
        "analyses_used": subscription.analyses_used_this_period,
        "amount": subscription.amount
    }


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Annule l'abonnement (fin de période)
    """
    
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.status == "active")
    )
    
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun abonnement actif"
        )
    
    try:
        # Annuler l'abonnement Stripe (à la fin de la période)
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        subscription.cancelled_at = datetime.utcnow()
        await db.commit()
        
        return {
            "message": "Abonnement annulé. Vous gardez l'accès jusqu'à la fin de la période.",
            "valid_until": subscription.current_period_end
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur lors de l'annulation: {str(e)}"
        )


@router.post("/portal")
async def create_portal_session(
    return_url: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Crée une session pour le portail client Stripe
    (pour gérer carte bancaire, factures, etc.)
    """
    
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun compte Stripe associé"
        )
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=return_url
        )
        
        return {"portal_url": portal_session.url}
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erreur Stripe: {str(e)}"
        )


# ========================================
# WEBHOOKS STRIPE
# ========================================

@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Gère les webhooks Stripe
    """
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Gérer les différents événements
    if event["type"] == "checkout.session.completed":
        await handle_checkout_completed(event["data"]["object"], db)
    
    elif event["type"] == "customer.subscription.updated":
        await handle_subscription_updated(event["data"]["object"], db)
    
    elif event["type"] == "customer.subscription.deleted":
        await handle_subscription_deleted(event["data"]["object"], db)
    
    elif event["type"] == "invoice.payment_succeeded":
        await handle_invoice_paid(event["data"]["object"], db)
    
    elif event["type"] == "invoice.payment_failed":
        await handle_invoice_failed(event["data"]["object"], db)
    
    return {"status": "success"}


async def handle_checkout_completed(session, db: AsyncSession):
    """Traite la finalisation d'un checkout"""
    
    user_id = session["metadata"]["user_id"]
    subscription_id = session["subscription"]
    
    # Récupérer l'abonnement Stripe
    stripe_subscription = stripe.Subscription.retrieve(subscription_id)
    
    # Récupérer l'utilisateur
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        return
    
    # Déterminer le plan
    price_id = stripe_subscription["items"]["data"][0]["price"]["id"]
    plan_name = get_plan_name_from_price_id(price_id)
    plan_config = PLANS_CONFIG.get(plan_name, PLANS_CONFIG["starter"])
    
    # Créer l'abonnement dans la DB
    subscription = Subscription(
        user_id=user.id,
        stripe_subscription_id=subscription_id,
        stripe_price_id=price_id,
        plan_name=plan_name,
        amount=plan_config["amount"],
        status=stripe_subscription["status"],
        current_period_start=datetime.fromtimestamp(stripe_subscription["current_period_start"]),
        current_period_end=datetime.fromtimestamp(stripe_subscription["current_period_end"]),
        analyses_limit=plan_config["analyses_limit"],
        analyses_used_this_period=0
    )
    
    db.add(subscription)
    
    # Mettre à jour l'utilisateur
    user.subscription_tier = plan_name
    user.subscription_status = "active"
    user.analyses_limit = plan_config["analyses_limit"]
    user.analyses_used = 0  # Reset au début de l'abonnement
    
    await db.commit()


async def handle_subscription_updated(stripe_subscription, db: AsyncSession):
    """Traite la mise à jour d'un abonnement"""
    
    result = await db.execute(
        select(Subscription)
        .where(Subscription.stripe_subscription_id == stripe_subscription["id"])
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        subscription.status = stripe_subscription["status"]
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_subscription["current_period_end"]
        )
        await db.commit()


async def handle_subscription_deleted(stripe_subscription, db: AsyncSession):
    """Traite la suppression d'un abonnement"""
    
    result = await db.execute(
        select(Subscription)
        .where(Subscription.stripe_subscription_id == stripe_subscription["id"])
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()
        
        # Désactiver l'utilisateur
        user_result = await db.execute(select(User).where(User.id == subscription.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.subscription_status = "cancelled"
            user.analyses_limit = 0
        
        await db.commit()


async def handle_invoice_paid(invoice, db: AsyncSession):
    """Traite le paiement d'une facture"""
    # Reset du quota mensuel
    subscription_id = invoice.get("subscription")
    if subscription_id:
        result = await db.execute(
            select(Subscription)
            .where(Subscription.stripe_subscription_id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            subscription.analyses_used_this_period = 0
            
            user_result = await db.execute(select(User).where(User.id == subscription.user_id))
            user = user_result.scalar_one_or_none()
            if user:
                user.analyses_used = 0
            
            await db.commit()


async def handle_invoice_failed(invoice, db: AsyncSession):
    """Traite l'échec d'un paiement"""
    # Marquer l'abonnement comme en retard
    subscription_id = invoice.get("subscription")
    if subscription_id:
        result = await db.execute(
            select(Subscription)
            .where(Subscription.stripe_subscription_id == subscription_id)
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            subscription.status = "past_due"
            await db.commit()


def get_plan_name_from_price_id(price_id: str) -> str:
    """Détermine le nom du plan depuis le price_id Stripe"""
    # À adapter selon tes price_id réels
    if price_id == settings.STRIPE_STARTER_PRICE_ID:
        return "starter"
    elif price_id == settings.STRIPE_PRO_PRICE_ID:
        return "pro"
    elif price_id == settings.STRIPE_ENTERPRISE_PRICE_ID:
        return "enterprise"
    return "starter"  # Défaut
