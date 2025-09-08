import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from supabase import create_client, Client
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

# Setup Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Setup Supabase
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # ⚠️ koristi service role key
)

router = APIRouter(prefix="/stripe", tags=["stripe"])


# --------------------------
# Pydantic modeli
# --------------------------
class CheckoutRequest(BaseModel):
    business_id: str
    plan_id: str


class UpgradeRequest(BaseModel):
    business_id: str
    new_plan_id: str


class RepurchaseRequest(BaseModel):
    business_id: str


# --------------------------
# Helper funkcije
# --------------------------
def get_business(business_id: str):
    result = supabase.table("businesses").select("*").eq("id", business_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Business not found")
    return result.data


def get_plan(plan_id: str):
    result = supabase.table("subscription_plans").select("*").eq("id", plan_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Plan not found")
    return result.data


# --------------------------
# Endpoint: Kreiraj Checkout Session
# --------------------------
@router.post("/create-checkout-session")
def create_checkout_session(request: CheckoutRequest):
    business = get_business(request.business_id)
    plan = get_plan(request.plan_id)

    # Ako nema stripe_customer_id → kreiraj
    stripe_customer_id = business.get("stripe_customer_id")
    if not stripe_customer_id:
        customer = stripe.Customer.create(
            email=business["email"],
            name=business["name"],
            phone=business.get("phone_number"),
            metadata={"business_id": request.business_id},
        )
        stripe_customer_id = customer.id
        supabase.table("businesses").update({"stripe_customer_id": stripe_customer_id}).eq("id", request.business_id).execute()

    # Ovdje odmah zapišemo plan_id i status "incomplete"
    supabase.table("businesses").update({
        "subscription_status": "incomplete",
        "subscription_plan_id": request.plan_id
    }).eq("id", request.business_id).execute()

    # Kreiraj checkout session
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": plan["stripe_price_id"], "quantity": 1}],
            customer=stripe_customer_id,
            metadata={
                "business_id": request.business_id,
                "plan_id": request.plan_id,
            },
            success_url="https://autoping.io/dashboard?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://autoping.io/pricing",
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


# --------------------------
# Endpoint: Upgrade subscription
# --------------------------
@router.post("/upgrade")
def upgrade_subscription(request: UpgradeRequest):
    business = get_business(request.business_id)
    new_plan = get_plan(request.new_plan_id)

    if not business.get("stripe_subscription_id"):
        raise HTTPException(status_code=400, detail="No active subscription to upgrade")

    try:
        # Modify existing Stripe subscription
        stripe.Subscription.modify(
            business["stripe_subscription_id"],
            cancel_at_period_end=False,
            proration_behavior="create_prorations",
            items=[{
                "id": stripe.Subscription.retrieve(business["stripe_subscription_id"]).items.data[0].id,
                "price": new_plan["stripe_price_id"],
            }],
        )

        # Update DB
        supabase.table("businesses").update({
            "subscription_plan_id": request.new_plan_id,
            "subscription_status": "active"
        }).eq("id", request.business_id).execute()

        return {"status": "success", "message": "Subscription upgraded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upgrade subscription: {str(e)}")


# --------------------------
# Endpoint: Repurchase same plan (reset requests)
# --------------------------
@router.post("/repurchase")
def repurchase_subscription(request: RepurchaseRequest):
    business = get_business(request.business_id)

    if not business.get("subscription_plan_id"):
        raise HTTPException(status_code=400, detail="No existing plan to repurchase")

    plan = get_plan(business["subscription_plan_id"])

    try:
        # Reset requests + renewal date (30 days from now)
        new_renewal = datetime.now(timezone.utc) + timedelta(days=30)
        supabase.table("subscriptions").update({
            "used_request": 0,
            "renewal_date": new_renewal.isoformat()
        }).eq("business_id", request.business_id).execute()

        # Kreiraj checkout session za isti plan
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": plan["stripe_price_id"], "quantity": 1}],
            customer=business["stripe_customer_id"],
            metadata={
                "business_id": request.business_id,
                "plan_id": business["subscription_plan_id"],
                "repurchase": "true"
            },
            success_url="https://autoping.io/dashboard?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://autoping.io/pricing",
        )
        return {"checkout_url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to repurchase subscription: {str(e)}")


# --------------------------
# Endpoint: Subscription overview
# --------------------------
@router.get("/overview/{business_id}")
def get_subscription_overview(business_id: str):
    business = get_business(business_id)

    # Stripe podaci
    stripe_status = None
    current_period_end = None
    cancel_at_period_end = None
    if business.get("stripe_subscription_id"):
        subscription = stripe.Subscription.retrieve(business["stripe_subscription_id"])
        stripe_status = subscription.status
        current_period_end = subscription.current_period_end
        cancel_at_period_end = subscription.cancel_at_period_end

    # Subscription tablica
    sub_result = supabase.table("subscriptions").select("*").eq("business_id", business_id).single().execute()
    sub = sub_result.data or {}

    limit = sub.get("request_limit")
    used = sub.get("used_request", 0)

    warning = None
    if limit and limit > 0 and used >= int(limit * 0.8) and used < limit:
        warning = "You are close to your monthly limit"

    can_send = True
    if limit and limit > 0 and used >= limit:
        can_send = False

    # Plan info
    plan_info = None
    if business.get("subscription_plan_id"):
        plan = get_plan(business["subscription_plan_id"])
        if plan:
            plan_info = {
                "id": plan["id"],
                "name": plan.get("name"),
                "price": plan.get("price"),
                "request_limit": plan.get("request_limit"),
            }

    return {
        "business_id": business_id,
        "status": stripe_status or business.get("subscription_status", "inactive"),
        "plan": plan_info,
        "requests": {
            "used": used,
            "limit": limit if limit and limit > 0 else "unlimited",
            "renewal_date": sub.get("renewal_date"),
            "can_send": can_send,
            "warning": warning,
        },
        "stripe": {
            "current_period_end": current_period_end,
            "cancel_at_period_end": cancel_at_period_end,
        },
        "trial_ends_at": business.get("trial_ends_at"),
    }


# --------------------------
# Endpoint: Webhook
# --------------------------
@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        business_id = session["metadata"]["business_id"]
        plan_id = session["metadata"]["plan_id"]

        supabase.table("businesses").update({
            "subscription_status": "incomplete",
            "subscription_plan_id": plan_id
        }).eq("id", business_id).execute()

    elif event["type"] == "customer.subscription.created":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]

        supabase.table("businesses").update({
            "subscription_status": subscription["status"],
            "stripe_subscription_id": subscription["id"]
        }).eq("stripe_customer_id", customer_id).execute()

    elif event["type"] in ["customer.subscription.updated", "customer.subscription.deleted"]:
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]

        supabase.table("businesses").update({
            "subscription_status": subscription["status"],
            "stripe_subscription_id": subscription["id"]
        }).eq("stripe_customer_id", customer_id).execute()

    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        customer_id = invoice["customer"]

        supabase.table("businesses").update({
            "subscription_status": "active"
        }).eq("stripe_customer_id", customer_id).execute()

    return {"status": "success"}
