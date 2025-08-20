import os
import httpx
from dotenv import load_dotenv
from template_map import template_map, profession_to_template_type
from supabase_service import get_user_state


load_dotenv()

INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL")
INFOBIP_SENDER = os.getenv("INFOBIP_WHATSAPP_NUMBER")

# === Slanje WhatsApp template poruke ===
async def send_whatsapp_template(to_number: str, profession: str, stage: str, business_id: str = None):
    if not to_number.startswith("+"):
        to_number = f"+{to_number}"

    template_type = profession_to_template_type.get(profession)
    if not template_type:
        raise ValueError(f"Nepoznata profession: {profession}")

    template_info = template_map.get(template_type, {}).get(stage)
    if not template_info:
        raise ValueError(f"Nedostaje template za type='{template_type}', stage='{stage}'")

    if isinstance(template_info, str):
        template_name = template_info
        buttons = []
    else:
        template_name = template_info["name"]
        buttons = template_info.get("buttons", [])

    print(f"[WA][TEMPLATE] stage={stage} type={template_type} name={template_name} → {to_number}")

    # === Popuni placeholders ===
    placeholders = []
    if business_id:
        # Ako želiš i dalje ime obrta, možeš dohvatiti ga iz user_states
        state = get_user_state(to_number)
        if state and state.get("profession"):
            placeholders.append(state["profession"])
    else:
        placeholders.append("Vaš Obrt")

    payload = {
        "messages": [
            {
                "from": INFOBIP_SENDER,
                "to": to_number,
                "content": {
                    "templateName": template_name,
                    "templateData": {
                        "body": {"placeholders": placeholders}
                    },
                    "language": "hr"
                }
            }
        ]
    }

    if buttons:
        payload["messages"][0]["content"]["templateData"]["buttons"] = [
            {"type": "QUICK_REPLY", "parameter": b} for b in buttons
        ]

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


    # === Dohvati business_name za placeholder ===
    placeholders = []
    if business_id:
        business = get_business_by_id(business_id)
        if business and business.get("name"):
            placeholders.append(business["name"])
        else:
            placeholders.append("Vaš Obrt")  # fallback placeholder

    # === Složi payload prema Infobip specifikaciji ===
    payload = {
        "messages": [
            {
                "from": INFOBIP_SENDER,
                "to": to_number,
                "content": {
                    "templateName": template_name,
                    "templateData": {
                        "body": {"placeholders": placeholders}
                    },
                    "language": "hr"
                }
            }
        ]
    }

    # Dodaj gumbe ako postoje
    if buttons:
        payload["messages"][0]["content"]["templateData"]["buttons"] = [
            {"type": "QUICK_REPLY", "parameter": b} for b in buttons
        ]

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




