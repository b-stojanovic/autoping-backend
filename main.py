import os
import json
from fastapi import FastAPI, HTTPException, Request
from whatsapp_service import send_whatsapp_template
from state_memory import set_state, get_state, update_step, clear_state
from supabase_service import get_business_by_id, save_request
from stripe_service import router as stripe_router


app = FastAPI()
app.include_router(stripe_router, prefix="/api") 

@app.get("/debug")
def debug():
    import os
    import stripe
    key = os.getenv("STRIPE_SECRET_KEY", "NOT_FOUND")
    stripe.api_key = key
    try:
        price = stripe.Price.retrieve("price_1SxrbdKCvXDoo1ndLif41GvY")
        return {"key_start": key[:20], "price_found": True}
    except Exception as e:
        return {"key_start": key[:20], "error": str(e)}

# ========================
# Utils
# ========================

def _norm_phone(msisdn: str) -> str:
    msisdn = (msisdn or "").replace(" ", "")
    return msisdn if msisdn.startswith("+") else f"+{msisdn}"

# ========================
# Endpoint: Missed call
# ========================

@app.post("/missed-call")
async def handle_missed_call(payload: dict):
    print("📩 Raw /missed-call payload:", payload)

    phone = payload.get("phone_number")
    business_id = payload.get("business_id")
    profession = payload.get("profession")

    print("➡️ phone_number:", phone)
    print("➡️ business_id:", business_id)
    print("➡️ profession:", profession)

    if not phone or not profession or not business_id:
        raise HTTPException(status_code=400, detail="Missing phone_number, business_id or profession")

    # ➡️ Snimi state u Supabase (intro stage)
    set_state(_norm_phone(phone), profession, "intro", business_id)

    # ➡️ Dohvati ime obrta
    business = get_business_by_id(business_id)
    business_name = business["name"] if business else "Naš obrt"

    # ➡️ Pošalji intro poruku (s imenom za placeholder {{1}})
    await send_whatsapp_template(
        to_number=_norm_phone(phone),
        profession=profession,
        stage="pm_intro",
        placeholders=[business_name]  # ✅ ime obrta u poruci
    )

    return {"status": "intro_sent", "profession": profession, "phone_number": phone, "business_name": business_name}

# ========================
# Endpoint: Infobip webhook
# ========================

@app.post("/infobip-webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("📩 Raw /infobip-webhook payload:", json.dumps(data, ensure_ascii=False))

    results = data.get("results", [])
    for result in results:
        from_number = _norm_phone(result.get("from"))
        message = result.get("message", {})
        text = message.get("text", "").strip()
        button_payload = message.get("payload")

        print(f"➡️ From {from_number} | text='{text}' | button={button_payload}")

        # ➡️ Dohvati state iz Supabase
        state = get_state(from_number)
        if not state:
            print("⚠️ Nema state-a za", from_number)
            continue

        profession = state["profession"]
        business_id = state["business_id"]
        step = state["step"]

        if button_payload:
            print("🔘 Kliknut gumb:", button_payload)
            update_step(from_number, "details")

            await send_whatsapp_template(
                to_number=from_number,
                profession=profession,
                stage="pm_details"
            )

        elif step == "details" and text:
            print("📝 Dobiveni detalji od korisnika:", text)

            # ➡️ Spremi zahtjev u requests tablicu
            save_request(
                phone_number=from_number,
                business_id=business_id,
                profession=profession,
                message=text,
                request_type="booking_service"
            )

            # ➡️ Očisti state
            clear_state(from_number)

            # ➡️ Pošalji confirmation template
            await send_whatsapp_template(
                to_number=from_number,
                profession=profession,
                stage="pm_confirmation"
            )

    return {"status": "webhook_processed"}
