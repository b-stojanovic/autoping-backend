# whatsapp_service.py

import os
import httpx
from dotenv import load_dotenv
from template_map import template_map, profession_to_template_type

load_dotenv()

INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL")
INFOBIP_SENDER = os.getenv("INFOBIP_WHATSAPP_NUMBER")

# === Slanje WhatsApp template poruke ===
async def send_whatsapp_template(to_number: str, profession: str, stage: str):
    if not to_number.startswith("+"):
        to_number = f"+{to_number}"

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

    # === Složi payload prema Infobip specifikaciji ===
    template_data = {
        "body": {"placeholders": []}
    }

    # Dodaj gumbe ako postoje
    if buttons:
        template_data["buttons"] = [
            {"type": "QUICK_REPLY", "parameter": b} for b in buttons
        ]

    payload = {
        "messages": [
            {
                "from": INFOBIP_SENDER,
                "to": to_number,
                "content": {
                    "templateName": template_name,
                    "templateData": template_data,
                    "language": "hr"
                }
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
