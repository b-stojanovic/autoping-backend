# whatsapp_service.py
import os, json, requests
from dotenv import load_dotenv
from template_utils import get_template_name_by_profession

load_dotenv()

INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
INFOBIP_WHATSAPP_NUMBER = os.getenv("INFOBIP_WHATSAPP_NUMBER")  # bez '+'
INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL")

def _norm_phone(msisdn: str) -> str:
    msisdn = (msisdn or "").replace(" ", "")
    return msisdn if msisdn.startswith("+") else f"+{msisdn}"

def send_template(phone_number: str, profession: str, stage: str = "pm_intro"):
    phone_number = _norm_phone(phone_number)

    # 🔑 Ključna linija: dohvati ispravan naziv templata iz ljudske profesije
    template_name, template_type = get_template_name_by_profession(profession, stage)

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
                    # ⚠️ Pošalji točan broj placeholdera; ako ih nema, ostavi []
                    "body": {"placeholders": []}
                }
            }
        }]
    }

    print(f"[WA][TEMPLATE] stage={stage} type={template_type} name={template_name} → {phone_number}")
    print("[WA][REQ]", json.dumps(payload, indent=2, ensure_ascii=False))

    resp = requests.post(url, headers=headers, json=payload)
    print("[WA][RES]", resp.status_code, resp.text)
    resp.raise_for_status()
    return resp.json() if resp.text else {"status": resp.status_code}

