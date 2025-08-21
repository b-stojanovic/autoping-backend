import os
import json
from fastapi import FastAPI, HTTPException, Request
from whatsapp_service import send_whatsapp_template
from supabase_service import save_user_state, get_user_state, clear_user_state, get_business_by_id

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

            # ➡️ Spremi novi state (ali zadrži pravi profession i business_id iz statea!)
            save_user_state(from_number, business_id, profession, "details")

            # ➡️ Pošalji details poruku
            await send_whatsapp_template(
                to_number=from_number,
                profession=profession,   # ✅ sad se koristi pravi profession
                stage="pm_details"
            )

        elif step == "details" and text:
            print("📝 Dobiveni detalji od korisnika:", text)

            # TODO: spremi zahtjev u requests tablicu

            # ➡️ brišemo state jer je flow završen
            clear_user_state(from_number)

            # ➡️ Pošalji confirmation poruku
            await send_whatsapp_template(
                to_number=from_number,
                profession=profession,
                stage="pm_confirmation"
            )

    return {"status": "ok"}
