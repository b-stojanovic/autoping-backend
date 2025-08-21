import os
import httpx
from dotenv import load_dotenv
from template_map import template_map, profession_to_template_type
from supabase_service import get_business_by_id  # koristimo da dohvatimo ime obrta

load_dotenv()

INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL")
INFOBIP_SENDER = os.getenv("INFOBIP_WHATSAPP_NUMBER")

# === Slanje WhatsApp template poruke ===
async def send_whatsapp_template(to_number: str, profession: str, stage: str, business_id: str = None):
    # Infobip bolje podnosi bez "+"
    clean_number = to_number.replace("+", "")

    # Dohvati tip templatea prema profesiji
    template_type = profession_to_template_type.get(profession)
    if not template_type:
        raise ValueError(f"Nepoznata profession: {profession}")

    # Dohvati template info
    template_info = template_map.get(template_type, {}).get(stage)
    if not template_info:
        raise ValueError(
            f"Nedostaje template za type='{template_type}', stage='{stage}'. Provjeri template_map."
        )

    # Ako je samo string (stari način), pretvori u dict
    if isinstance(template_info, str):
        template_name = template_info
        buttons = []
    else:
        template_name = template_info["name"]
        buttons = template_info.get("buttons", [])

    print(f"[WA][TEMPLATE] stage={stage} type={template_type} name={template_name} → {to_number}")

    # === Placeholderi (ako postoje) ===
    placeholders = []
    if business_id and "{{1}}" in str(template_info):
        business = get_business_by_id(business_id)
        if business and business.get("name"):
            placeholders.append(business["name"])
        else:
            placeholders.append("Vaš Obrt")

    # === Osnovna struktura poruke ===
    content = {
        "templateName": template_name,
        "templateData": {
            "body": {"placeholders": placeholders or []}
        },
        "language": {
            "policy": "deterministic",
            "code": "hr"
        }
    }

    # Dodaj gumbe ako postoje
    if buttons:
        content["templateData"]["buttons"] = [
            {"type": "QUICK_REPLY", "parameter": b} for b in buttons
        ]

    payload = {
        "messages": [
            {
                "from": INFOBIP_SENDER,
                "to": clean_number,   # bez +
                "messageId": f"autoping-{clean_number}",  # custom ID
                "content": content
            }
        ]
    }

    print(f"[WA][REQ] {payload}")

    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{INFOBIP_BASE_URL}/whatsapp/1/message/template",
            headers=headers,
            json=payload,
        )
        print(f"[WA][RES] {resp.status_code} {resp.text}")
        resp.raise_for_status()
        return resp.json()
