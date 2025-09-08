import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from supabase import create_client, Client
from pydantic import BaseModel

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

    # ⬅️ Ovdje odmah zapišemo plan_id i status "incomplete"
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
# Endpoint: Subscription status
# --------------------------
@router.get("/subscription-status/{business_id}")
def get_subscription_status(business_id: str):
    business = get_business(business_id)

    # Ako nema subscription → trial/free
    if not business.get("stripe_subscription_id"):
        return {
            "status": business["subscription_status"],
            "plan_id": business.get("subscription_plan_id"),
            "trial_ends_at": business.get("trial_ends_at"),
        }

    # Povuci subscription sa Stripe-a
    subscription = stripe.Subscription.retrieve(business["stripe_subscription_id"])
    return {
        "status": subscription.status,
        "current_period_end": subscription.current_period_end,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "plan_id": business.get("subscription_plan_id"),
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

    # 1) Checkout completed → evidentiraj plan, ali možda subscription još nije tu
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        business_id = session["metadata"]["business_id"]
        plan_id = session["metadata"]["plan_id"]

        supabase.table("businesses").update({
            "subscription_status": "incomplete",   # čekamo potvrdu plaćanja
            "subscription_plan_id": plan_id
        }).eq("id", business_id).execute()

    # 2) Subscription created → spremi subscription_id i postavi active
    elif event["type"] == "customer.subscription.created":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]

        supabase.table("businesses").update({
            "subscription_status": subscription["status"],  # obično "active"
            "stripe_subscription_id": subscription["id"]
        }).eq("stripe_customer_id", customer_id).execute()

    # 3) Subscription updated/deleted → sync status
    elif event["type"] in ["customer.subscription.updated", "customer.subscription.deleted"]:
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]

        supabase.table("businesses").update({
            "subscription_status": subscription["status"],
            "stripe_subscription_id": subscription["id"]
        }).eq("stripe_customer_id", customer_id).execute()

    # 4) Invoice paid → dodatna sigurnost da je status active
    elif event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        customer_id = invoice["customer"]

        supabase.table("businesses").update({
            "subscription_status": "active"
        }).eq("stripe_customer_id", customer_id).execute()

    return {"status": "success"}

