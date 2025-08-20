# whatsapp_service.py

import os
import requests
from dotenv import load_dotenv
from template_map import template_map, profession_to_template_type

load_dotenv()

INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
INFOBIP_WHATSAPP_NUMBER = os.getenv("INFOBIP_WHATSAPP_NUMBER")
INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL")


def resolve_template(profession: str, stage: str) -> dict:
    """
    Vrati template ime i opcionalne gumbe za zadani profession + stage.
    """
    template_type = profession_to_template_type.get(profession)
    if not template_type:
        raise ValueError(f"Nepoznata profession '{profession}' u profession_to_template_type.")

    type_entry = template_map.get(template_type)
    if not type_entry:
        raise ValueError(f"Nema template_type '{template_type}' u template_map.")

    template_name = type_entry.get(stage)
    if not template_name:
        raise ValueError(
            f"Nedostaje template za type='{template_type}', stage='{stage}'. Provjeri template_map."
        )

    buttons = type_entry.get("buttons", [])  # ✅ dinamički gumbe
    return {"template_name": template_name, "buttons": buttons}


async def send_whatsapp_template(to_number: str, profession: str, stage: str, placeholders=None):
    """
    Šalje WhatsApp template poruku korisniku.
    - Dinamički učitava gumbe iz template_map.py
    """
    if not to_number.startswith("+"):
        to_number = f"+{to_number}"

    try:
        tpl = resolve_template(profession, stage)
        template_name = tpl["template_name"]
        buttons = tpl.get("buttons", [])

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

        # Ako postoje gumbe → dodaj u payload
        if buttons:
            data["messages"][0]["content"]["templateData"]["buttons"] = buttons

        headers = {
            "Authorization": f"App {INFOBIP_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/template"
        response = requests.post(url, headers=headers, json=data, timeout=10)

        print(f"📤 Sending template '{template_name}' to {to_number}")
        print("➡️ Payload:", data)
        print("⬅️ Response:", response.status_code, response.text)

        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(f"❌ ERROR in send_whatsapp_template: {e}")
        raise


