import os
import requests
from dotenv import load_dotenv
import json
from template_map import template_map
from template_map import profession_to_template_type

load_dotenv()

INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
INFOBIP_WHATSAPP_NUMBER = os.getenv("INFOBIP_WHATSAPP_NUMBER")  # bez '+'
INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL")

def send_template(phone_number: str, profession: str, stage: str = "pm_intro"):
    phone_number = phone_number.strip().replace(" ", "")
    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"

    template_type = profession_to_template_type.get(profession)
    if not template_type:
        raise ValueError(f"Nepoznata profesija: {profession}")

    template_name = template_map[template_type][stage]

    url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/template"
    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Content-Type": "application/json"
    }

    # Gumbi samo za pm_intro
    buttons = []
    if stage == "pm_intro":
        if template_type == "booking_service":
            buttons = [
                {"type": "QUICK_REPLY", "parameter": "Termini"},
                {"type": "QUICK_REPLY", "parameter": "Pitanje o usluzi"}
            ]
        elif template_type == "emergency_repair":
            buttons = [
                {"type": "QUICK_REPLY", "parameter": "Hitno"},
                {"type": "QUICK_REPLY", "parameter": "Ostali upiti"}
            ]
        elif template_type == "delivery_order":
            buttons = [
                {"type": "QUICK_REPLY", "parameter": "Nova narudžba"},
                {"type": "QUICK_REPLY", "parameter": "Pitanje o dostavi"}
            ]
        elif template_type == "business_query":
            buttons = [
                {"type": "QUICK_REPLY", "parameter": "Poslovni upit"},
                {"type": "QUICK_REPLY", "parameter": "Opće pitanje"}
            ]

    # ⚠️ INFOBIP expects messages array
    data = {
        "messages": [
            {
                "from": INFOBIP_WHATSAPP_NUMBER,
                "to": phone_number,
                "content": {
                    "templateName": template_name,
                    "templateData": {
                        "body": {"placeholders": ["-"]},
                        "language": "hr"
                    }
                }
            }
        ]
    }

    if buttons:
        data["messages"][0]["content"]["templateData"]["buttons"] = buttons

    print(f"📤 Slanje templatea '{template_name}' na {phone_number}")
    print("📦 Payload:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    response = requests.post(url, headers=headers, json=data)
    print("📡 Status:", response.status_code)
    print("🔁 Response:", response.text)

if __name__ == "__main__":
    # TEST primjer
    send_template("+385957762291", "Frizerka / Barber", "pm_intro")
