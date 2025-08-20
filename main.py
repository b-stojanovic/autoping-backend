# main.py

import os
import json
import requests
from fastapi import FastAPI, HTTPException, Request
from template_utils import get_template_name_by_profession  # ✅ koristi resolver

app = FastAPI()

# ========================
# Utils
# ========================

def _norm_phone(msisdn: str) -> str:
    msisdn = (msisdn or "").replace(" ", "")
    return msisdn if msisdn.startswith("+") else f"+{msisdn}"

# ========================
# WhatsApp Template Sender
# ========================

async def send_whatsapp_template(phone_number: str, profession: str, stage: str = "pm_intro"):
    phone_number = _norm_phone(phone_number)

    try:
        template_name, template_type = get_template_name_by_profession(profession, stage)
    except Exception as e:
        print("❌ ERROR in template resolver:", e)
        raise HTTPException(status_code=400, detail=str(e))

    INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
    INFOBIP_WHATSAPP_NUMBER = os.getenv("INFOBIP_WHATSAPP_NUMBER")
    INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL")

    url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/template"
    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "messages": [{
            "from": INFOBIP_WHATSAPP_NUMBER,
            "to": phone_number,
            "content": {
                "templateName": template_name,
                "language": "hr",
                "templateData": {
                    "body": {"placeholders": []}
                }
            }
        }]
    }

    print(f"[WA][TEMPLATE] stage={stage} type={template_type} name={template_name} → {phone_number}")
    print("[WA][REQ]", json.dumps(payload, ensure_ascii=False))

    resp = requests.post(url, headers=headers, json=payload)
    print("[WA][RES]", resp.status_code, resp.text)

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return {"ok": True}

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

    # šaljemo prvu intro poruku
    await send_whatsapp_template(phone, profession, "pm_intro")

    return {"status": "intro_sent", "profession": profession, "phone_number": phone}

