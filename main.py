# main.py (relevantni dijelovi)

import os, json, requests
from fastapi import FastAPI, HTTPException
from template_utils import get_template_name_by_profession  # ✅ koristi resolver

app = FastAPI()

def _norm_phone(msisdn: str) -> str:
    msisdn = (msisdn or "").replace(" ", "")
    return msisdn if msisdn.startswith("+") else f"+{msisdn}"

async def send_whatsapp_template(phone_number: str, profession: str, stage: str = "pm_intro"):
    phone_number = _norm_phone(phone_number)

    # 🔑 UMJESTO: template_map[template_type][stage]
    try:
        template_name, template_type = get_template_name_by_profession(profession, stage)
    except Exception as e:
        # jasna poruka umjesto 500
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
                    # ⚠️ ako template nema placeholdere → []
                    "body": {"placeholders": []}
                }
            }
        }]
    }

    print(f"[WA][TEMPLATE] stage={stage} type={template_type} name={template_name} → {phone_number}")
    print("[WA][REQ]", json.dumps(payload, ensure_ascii=False))

    resp = requests.post(url, headers=headers, json=payload)
    print("[WA][RES]", resp.status_code, resp.text)
    resp.raise_for_status()
    return {"ok": True}

# primjer handlera
@app.post("/missed-call")
async def handle_missed_call(payload: dict):
    phone = payload["phone_number"]
    profession = payload["profession"]   # "ljudsko" ime
    # ... (tvoj session upsert itd.)
    await send_whatsapp_template(phone, profession, "pm_intro")
    return {"status": "intro_sent"}

