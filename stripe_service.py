import stripe
import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from supabase import create_client
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import json

# Setup
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_KEY')
)

router = APIRouter(prefix="/stripe", tags=["stripe"])

# Pricing configuration
PRICING_TIERS = {
    "HR": {
        "starter": {
            "stripe_price_id": "price_1S3GBhGxXc2NbVni78GsPggT",  # Replace with actual Stripe PRICE ID (not product ID!)
            "price": 19.99,
            "currency": "EUR",
            "features": [
                "basic_scheduling",
                "sms_notifications", 
                "calendar_integration",
                "max_appointments_100"
            ]
        },
        "pro": {
            "stripe_price_id": "price_hr_pro",
            "price": 39.99,
            "currency": "EUR", 
            "features": [
                "basic_scheduling",
                "sms_notifications",
                "calendar_integration",
                "advanced_scheduling",
                "analytics_dashboard",
                "integrations",
                "max_appointments_500"
            ]
        },
        "business": {
            "stripe_price_id": "price_hr_business",
            "price": 59.99,
            "currency": "EUR",
            "features": [
                "basic_scheduling",
                "sms_notifications", 
                "calendar_integration",
                "advanced_scheduling",
                "analytics_dashboard",
                "integrations",
                "white_label_branding",
                "api_access",
                "priority_support",
                "unlimited_appointments"
            ]
        }
    },
    "RS": {
        "starter": {
            "stripe_price_id": "price_rs_starter",
            "price": 2300,
            "currency": "RSD",
            "features": [
                "basic_scheduling",
                "sms_notifications",
                "calendar_integration", 
                "max_appointments_100"
            ]
        },
        "pro": {
            "stripe_price_id": "price_rs_pro",
            "price": 4600,
            "currency": "RSD",
            "features": [
                "basic_scheduling",
                "sms_notifications",
                "calendar_integration",
                "advanced_scheduling", 
                "analytics_dashboard",
                "integrations",
                "max_appointments_500"
            ]
        },
        "business": {
            "stripe_price_id": "price_rs_business",
            "price": 6900,
            "currency": "RSD",
            "features": [
                "basic_scheduling",
                "sms_notifications",
                "calendar_integration",
                "advanced_scheduling",
                "analytics_dashboard", 
                "integrations",
                "white_label_branding",
                "api_access",
                "priority_support",
                "unlimited_appointments"
            ]
        }
    }
}

# Pydantic models
class SubscriptionRequest(BaseModel):
    business_id: str
    tier: str  # 'starter', 'pro', 'business'
    country: str = "HR"

class WebhookEvent(BaseModel):
    type: str
    data: dict

# Utility functions
async def get_business(business_id: str):
    """Get business from Supabase"""
    try:
        result = supabase.table("businesses").select("*").eq("id", business_id).single().execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=404, detail="Business not found")

async def check_business_features(business_id: str, required_feature: str) -> bool:
    """Check if business has access to a specific feature"""
    business = await get_business(business_id)
    
    # Check trial period first
    if business["subscription_tier"] == "trial":
        trial_end = datetime.fromisoformat(business["trial_ends_at"].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) < trial_end:
            return True  # Trial period = access to all features
        else:
            # Trial expired, need to upgrade
            return False
    
    # Check plan features
    tier = business["subscription_tier"] 
    country = business.get("subscription_country", "HR")
    
    if country not in PRICING_TIERS or tier not in PRICING_TIERS[country]:
        return False
        
    plan_features = PRICING_TIERS[country][tier]["features"]
    return required_feature in plan_features

async def update_business_subscription(business_id: str, updates: dict):
    """Update business subscription data in Supabase"""
    try:
        supabase.table("businesses").update(updates).eq("id", business_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update business: {str(e)}")

# API Endpoints
@router.get("/pricing/{country}")
async def get_pricing(country: str = "HR"):
    """Get pricing information for a country"""
    if country not in PRICING_TIERS:
        raise HTTPException(status_code=400, detail="Unsupported country")
    
    return {
        "country": country,
        "currency": PRICING_TIERS[country]["starter"]["currency"],
        "plans": {
            tier: {
                "price": plan["price"],
                "currency": plan["currency"], 
                "features": plan["features"]
            }
            for tier, plan in PRICING_TIERS[country].items()
        }
    }

@router.post("/create-subscription")
async def create_subscription(request: SubscriptionRequest):
    """Create new subscription for business"""
    try:
        print(f"DEBUG: Starting subscription creation for business_id: {request.business_id}")
        
        # Debug environment variables
        stripe_key = os.getenv('STRIPE_SECRET_KEY')
        print(f"DEBUG: Stripe key exists: {stripe_key is not None}")
        if stripe_key:
            print(f"DEBUG: Stripe key starts with: {stripe_key[:10]}")
        
        # Test Stripe connection first
        print("DEBUG: Testing Stripe API connection...")
        test_customers = stripe.Customer.list(limit=1)
        print("DEBUG: Stripe API connection successful")
        
        # Validate inputs
        if request.country not in PRICING_TIERS:
            raise HTTPException(status_code=400, detail="Unsupported country")
        
        if request.tier not in PRICING_TIERS[request.country]:
            raise HTTPException(status_code=400, detail="Invalid subscription tier")
        
        # Get plan config
        plan_config = PRICING_TIERS[request.country][request.tier]
        print(f"DEBUG: Using price_id: {plan_config['stripe_price_id']}")
        
        # Check if price_id is placeholder
        if plan_config['stripe_price_id'].startswith('price_REPLACE') or plan_config['stripe_price_id'].startswith('price_hr') or plan_config['stripe_price_id'].startswith('price_rs'):
            return {
                "debug": "Please replace placeholder price IDs with real Stripe Price IDs",
                "current_price_id": plan_config['stripe_price_id'],
                "note": "Go to Stripe Dashboard → Products → Copy Price ID (starts with price_)"
            }
            
        # Get business
        print("DEBUG: Getting business from database...")
        business = await get_business(request.business_id)
        print(f"DEBUG: Found business: {business['name']}")
        
        return {"debug": "All checks passed", "business_name": business["name"], "price_id": plan_config['stripe_price_id']}
        
    except stripe.error.StripeError as e:
        print(f"DEBUG: Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        print(f"DEBUG: General error: {str(e)}")
        print(f"DEBUG: Error type: {type(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/subscription-status/{business_id}")
async def get_subscription_status(business_id: str):
    """Get current subscription status for business"""
    try:
        business = await get_business(business_id)
        
        # Check if on trial
        if business["subscription_tier"] == "trial":
            trial_end = datetime.fromisoformat(business["trial_ends_at"].replace('Z', '+00:00'))
            return {
                "status": "trial",
                "tier": "trial",
                "trial_ends_at": business["trial_ends_at"],
                "days_remaining": (trial_end - datetime.now(timezone.utc)).days,
                "features": ["all"]  # Trial has access to everything
            }
        
        # Get subscription from Stripe
        if business.get("subscription_id"):
            stripe_subscription = stripe.Subscription.retrieve(business["subscription_id"])
            
            # Sync status with Supabase if different
            if stripe_subscription.status != business["subscription_status"]:
                await update_business_subscription(business_id, {
                    "subscription_status": stripe_subscription.status
                })
            
            # Get plan features
            tier = business["subscription_tier"]
            country = business.get("subscription_country", "HR")
            features = PRICING_TIERS[country][tier]["features"] if tier in PRICING_TIERS[country] else []
            
            return {
                "status": stripe_subscription.status,
                "tier": tier,
                "current_period_end": stripe_subscription.current_period_end,
                "cancel_at_period_end": stripe_subscription.cancel_at_period_end,
                "features": features,
                "plan_details": PRICING_TIERS[country][tier] if tier in PRICING_TIERS[country] else None
            }
        else:
            return {
                "status": "free",
                "tier": "free", 
                "features": []
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel-subscription/{business_id}")
async def cancel_subscription(business_id: str, cancel_immediately: bool = False):
    """Cancel subscription for business"""
    try:
        business = await get_business(business_id)
        
        if not business.get("subscription_id"):
            raise HTTPException(status_code=400, detail="No active subscription found")
        
        if cancel_immediately:
            # Cancel immediately
            stripe.Subscription.delete(business["subscription_id"])
            await update_business_subscription(business_id, {
                "subscription_status": "canceled",
                "subscription_tier": "free"
            })
            return {"message": "Subscription canceled immediately"}
        else:
            # Cancel at period end
            stripe.Subscription.modify(
                business["subscription_id"],
                cancel_at_period_end=True
            )
            await update_business_subscription(business_id, {
                "subscription_status": "active"  # Still active until period ends
            })
            return {"message": "Subscription will cancel at end of billing period"}
            
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-feature/{business_id}/{feature}")
async def check_feature_access(business_id: str, feature: str):
    """Check if business has access to specific feature"""
    try:
        has_access = await check_business_features(business_id, feature)
        return {
            "business_id": business_id,
            "feature": feature,
            "has_access": has_access
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        
        # Verify webhook signature
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        
        # Handle the event
        if event['type'] == 'invoice.payment_succeeded':
            subscription_id = event['data']['object']['subscription']
            
            # Update subscription status
            subscription = stripe.Subscription.retrieve(subscription_id)
            business_id = subscription.metadata.get('business_id')
            
            if business_id:
                await update_business_subscription(business_id, {
                    "subscription_status": "active"
                })
                
        elif event['type'] == 'invoice.payment_failed':
            subscription_id = event['data']['object']['subscription']
            subscription = stripe.Subscription.retrieve(subscription_id)
            business_id = subscription.metadata.get('business_id')
            
            if business_id:
                await update_business_subscription(business_id, {
                    "subscription_status": "past_due"
                })
                
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            business_id = subscription.metadata.get('business_id')
            
            if business_id:
                await update_business_subscription(business_id, {
                    "subscription_status": "canceled",
                    "subscription_tier": "free"
                })
        
        return {"status": "success"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper endpoint for trial management
@router.post("/extend-trial/{business_id}")
async def extend_trial(business_id: str, days: int):
    """Extend trial period (admin only)"""
    try:
        business = await get_business(business_id)
        
        current_trial_end = datetime.fromisoformat(business["trial_ends_at"].replace('Z', '+00:00'))
        new_trial_end = current_trial_end + timedelta(days=days)
        
        await update_business_subscription(business_id, {
            "trial_ends_at": new_trial_end.isoformat()
        })
        
        return {
            "message": f"Trial extended by {days} days",
            "new_trial_end": new_trial_end.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))