# whatsapp_service.py

import os
import httpx
from dotenv import load_dotenv
from template_map import template_map, profession_to_template_type

load_dotenv()

INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL")
INFOBIP_WHATSAPP_NUMBER = os.getenv("INFOBIP_WHATSAPP_NUMBER")


# ==============================
# Resolve template by profession
# ==============================
def resolve_template(profession: str, stage: str):
    template_type = profession_to_template_type.get(profession)
    if not template_type:
        raise ValueError(f"❌ No template_type for profession '{profession}'")

    mapping = template_map.get(template_type)
    if not mapping:
        raise ValueError(f"❌ No template mapping for type '{template_type}'")

    template_name = mapping.get(stage)
    if not template_name:
        raise ValueError(f"❌ Stage '{stage}' not found for type '{template_type}'")

    # Ako je u template_map dodan "buttons", povuci ga
    buttons = mapping.get("buttons", [])

    return {
        "template_name": template_name,
        "buttons": buttons
    }


# ==============================
# Send WhatsApp Template Message
# ==============================
async def send_whatsapp_template(to_number: str, profession: str, stage: str, placeholders=None):
    tpl = resolve_template(profession, stage)
    template_name = tpl["template_name"]
    buttons = tpl.get("buttons", [])

    if not to_number.startswith("+"):
        to_number = f"+{to_number}"

    data = {
        "messages": [
            {
                "from": INFOBIP_WHATSAPP_NUMBER,
                "to": to_number,
                "content": {
                    "templateName": template_name,
                    "templateData": {
                        "body": {
                            "placeholders": placeholders or []
                        }
                    },
                    "language": "hr"
                }
            }
        ]
    }

    # ✅ Ako postoje gumbi, dodaj ih u templateData.buttons
    if buttons:
        data["messages"][0]["content"]["templateData"]["buttons"] = [
            {"type": "QUICK_REPLY", "parameter": b} for b in buttons
        ]

    print(f"[WA][TEMPLATE] stage={stage} type={profession} name={template_name} buttons={buttons} → {to_number}")
    print(f"[WA][REQ] {data}")

    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{INFOBIP_BASE_URL}/whatsapp/1/message/template",
            json=data,
            headers=headers
        )

    print(f"[WA][RES] {response.status_code} {response.text}")
    return response


