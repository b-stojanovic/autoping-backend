import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from supabase import create_client, Client
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

# Setup Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://autoping.io")

# Setup Supabase
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
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


def get_business_by_customer(customer_id: str):
    """Helper za webhook - dohvati business po stripe_customer_id"""
    result = supabase.table("businesses").select("*").eq("stripe_customer_id", customer_id).single().execute()
    return result.data


def ensure_subscription_row(business_id: str, request_limit: int):
    """Kreiraj ili ažuriraj subscription row za tracking usage-a"""
    existing = supabase.table("subscriptions").select("id").eq("business_id", business_id).single().execute()

    renewal_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    if existing.data:
        # Reset usage pri novoj pretplati
        supabase.table("subscriptions").update({
            "used_request": 0,
            "request_limit": request_limit,
            "renewal_date": renewal_date,
        }).eq("business_id", business_id).execute()
    else:
        # Kreiraj novi row
        supabase.table("subscriptions").insert({
            "business_id": business_id,
            "used_request": 0,
            "request_limit": request_limit,
            "renewal_date": renewal_date,
        }).execute()


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
        supabase.table("businesses").update({
            "stripe_customer_id": stripe_customer_id
        }).eq("id", request.business_id).execute()

    # Zapišemo plan_id i status "incomplete" (čeka plaćanje)
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
            success_url=f"{FRONTEND_URL}/dashboard?payment=success",
            cancel_url=f"{FRONTEND_URL}/payment",
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
        # Dohvati trenutni subscription item ID
        sub = stripe.Subscription.retrieve(business["stripe_subscription_id"])
        item_id = sub["items"]["data"][0]["id"]

        # Modify existing Stripe subscription
        stripe.Subscription.modify(
            business["stripe_subscription_id"],
            cancel_at_period_end=False,
            proration_behavior="create_prorations",
            items=[{
                "id": item_id,
                "price": new_plan["stripe_price_id"],
            }],
        )

        # Update DB
        supabase.table("businesses").update({
            "subscription_plan_id": request.new_plan_id,
            "subscription_status": "active"
        }).eq("id", request.business_id).execute()

        # Update request limit u subscriptions tablici
        new_limit = new_plan.get("request_limit", 0)
        supabase.table("subscriptions").update({
            "request_limit": new_limit
        }).eq("business_id", request.business_id).execute()

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
            success_url=f"{FRONTEND_URL}/dashboard?payment=success",
            cancel_url=f"{FRONTEND_URL}/payment",
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
        try:
            subscription = stripe.Subscription.retrieve(business["stripe_subscription_id"])
            stripe_status = subscription.status
            current_period_end = subscription.current_period_end
            cancel_at_period_end = subscription.cancel_at_period_end
        except stripe.error.InvalidRequestError:
            # Subscription je obrisan na Stripeu
            stripe_status = "cancelled"

    # Subscription tablica (usage tracking)
    sub = {}
    try:
        sub_result = supabase.table("subscriptions").select("*").eq("business_id", business_id).single().execute()
        sub = sub_result.data or {}
    except Exception:
        pass

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
        try:
            plan = get_plan(business["subscription_plan_id"])
            if plan:
                plan_info = {
                    "id": plan["id"],
                    "name": plan.get("name"),
                    "price": plan.get("price"),
                    "request_limit": plan.get("request_limit"),
                }
        except Exception:
            pass

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

    event_type = event["type"]

    # ─── CHECKOUT COMPLETED ───
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        business_id = session["metadata"].get("business_id")
        plan_id = session["metadata"].get("plan_id")
        subscription_id = session.get("subscription")

        if business_id and plan_id:
            # Dohvati plan za request_limit
            try:
                plan = get_plan(plan_id)
                request_limit = plan.get("request_limit", 0)
            except Exception:
                request_limit = 0

            # Update business
            update_data = {
                "subscription_status": "active",
                "subscription_plan_id": plan_id,
            }
            if subscription_id:
                update_data["stripe_subscription_id"] = subscription_id

            supabase.table("businesses").update(update_data).eq("id", business_id).execute()

            # Kreiraj/resetiraj subscription row za usage tracking
            ensure_subscription_row(business_id, request_limit)

    # ─── SUBSCRIPTION CREATED ───
    elif event_type == "customer.subscription.created":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]

        business = get_business_by_customer(customer_id)
        if business:
            supabase.table("businesses").update({
                "subscription_status": subscription["status"],
                "stripe_subscription_id": subscription["id"]
            }).eq("id", business["id"]).execute()

    # ─── SUBSCRIPTION UPDATED / DELETED ───
    elif event_type in ["customer.subscription.updated", "customer.subscription.deleted"]:
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]

        status = subscription["status"]
        if event_type == "customer.subscription.deleted":
            status = "cancelled"

        business = get_business_by_customer(customer_id)
        if business:
            supabase.table("businesses").update({
                "subscription_status": status,
                "stripe_subscription_id": subscription["id"]
            }).eq("id", business["id"]).execute()

    # ─── INVOICE PAID ───
    elif event_type == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        customer_id = invoice["customer"]
        subscription_id = invoice.get("subscription")

        business = get_business_by_customer(customer_id)
        if business:
            supabase.table("businesses").update({
                "subscription_status": "active"
            }).eq("id", business["id"]).execute()

            # Ako je recurring payment (ne prvi), resetiraj usage
            if invoice.get("billing_reason") == "subscription_cycle":
                plan_id = business.get("subscription_plan_id")
                if plan_id:
                    try:
                        plan = get_plan(plan_id)
                        request_limit = plan.get("request_limit", 0)
                        ensure_subscription_row(business["id"], request_limit)
                    except Exception:
                        pass

    # ─── PAYMENT FAILED ───
    elif event_type == "invoice.payment_failed":
        invoice = event["data"]["object"]
        customer_id = invoice["customer"]

        business = get_business_by_customer(customer_id)
        if business:
            supabase.table("businesses").update({
                "subscription_status": "past_due"
            }).eq("id", business["id"]).execute()

    return {"status": "success"}