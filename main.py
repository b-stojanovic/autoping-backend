import os
import json
from fastapi import FastAPI, HTTPException, Request
from whatsapp_service import send_whatsapp_template
from supabase_service import save_user_state, get_user_state, clear_user_state

app = FastAPI()

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

    # ➡️ Snimi state u Supabase
    save_user_state(phone, business_id, profession, "intro")

    # ➡️ Pošalji intro poruku
    await send_whatsapp_template(
        to_number=_norm_phone(phone),
        profession=profession,
        stage="pm_intro",
        business_id=business_id
    )

    return {"status": "intro_sent", "profession": profession, "phone_number": phone}

# ========================
# Endpoint: Infobip webhook
# ========================

@app.post("/infobip-webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("📩 Raw /infobip-webhook payload:", json.dumps(data, ensure_ascii=False))

    results = data.get("results", [])
    for result in results:
        from_number = result.get("from")        # ✅ FIXED (nije u message, nego direktno u result)
        message = result.get("message", {})
        text = message.get("text", "").strip()
        button_payload = message.get("payload")  # ✅ FIXED quick reply payload

        print(f"➡️ From {from_number} | text='{text}' | button={button_payload}")

        # ➡️ Dohvati state iz Supabase
        state = get_user_state(from_number)
        if not state:
            print("⚠️ Nema state-a za", from_number)
            continue

        profession = state["profession"]
        business_id = state["business_id"]
        step = state["step"]

        if button_payload:
            print("🔘 Kliknut gumb:", button_payload)
            save_user_state(from_number, business_id, profession, "details")

            await send_whatsapp_template(
                to_number=from_number,
                profession=profession,
                stage="pm_details",
                business_id=business_id
            )

        elif step == "details" and text:
            print("📝 Dobiveni detalji od korisnika:", text)

            # TODO: spremi zahtjev u requests tablicu

            clear_user_state(from_number)

            await send_whatsapp_template(
                to_number=from_number,
                profession=profession,
                stage="pm_confirmation",
                business_id=business_id
            )

    return {"status": "primljeno"}
