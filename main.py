import os
from fastapi import FastAPI, HTTPException
from whatsapp_service import send_whatsapp_template

app = FastAPI()

# ========================
# Utils
# ========================

def _norm_phone(msisdn: str) -> str:
    msisdn = (msisdn or "").replace(" ", "")
    return msisdn if msisdn.startswith("+") else f"+{msisdn}"

# ========================
# Endpoint
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

    if not phone or not profession:
        raise HTTPException(status_code=400, detail="Missing phone_number or profession in request")

    # šaljemo prvu intro poruku s placeholderima
    await send_whatsapp_template(
        to_number=_norm_phone(phone),
        profession=profession,
        stage="pm_intro",
        business_id=business_id
    )

    return {"status": "intro_sent", "profession": profession, "phone_number": phone}


