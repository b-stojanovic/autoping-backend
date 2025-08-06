from fastapi import FastAPI, Request
from dotenv import load_dotenv
from datetime import datetime
import os
import httpx
from template_map import template_map, profession_to_template_type
from state_memory import set_state, get_state, update_step, clear_state

load_dotenv()
app = FastAPI()

# === Infobip Config ===
INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY")
INFOBIP_BASE_URL = os.getenv("INFOBIP_BASE_URL")
INFOBIP_SENDER = os.getenv("INFOBIP_WHATSAPP_NUMBER")

# === Supabase Config ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE")

# === Slanje WhatsApp template poruke ===
async def send_whatsapp_template(to_number: str, profession: str, stage: str):
    if not to_number.startswith("+"):
        to_number = f"+{to_number}"

    template_type = profession_to_template_type.get(profession)
    if not template_type:
        raise ValueError(f"Nepoznata profesija: {profession}")

    template_name = template_map[template_type][stage]

    url = f"{INFOBIP_BASE_URL}/whatsapp/1/message/template"
    INFOBIP_SENDER_FULL = INFOBIP_SENDER

    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Content-Type": "application/json"
    }

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

    payload = {
        "messages": [
            {
                "from": INFOBIP_SENDER_FULL,
                "to": to_number,
                "content": {
                    "templateName": template_name,
                    "language": "hr",
                    "templateData": {
                        "body": {
                            "placeholders": []
                        }
                    }
                }
            }
        ]
    }

    if buttons:
        payload["messages"][0]["content"]["templateData"]["buttons"] = buttons

    print("📨 SENDER (from):", INFOBIP_SENDER_FULL)
    print("📄 Template name koji šaljemo:", template_name)
    print("📦 PAYLOAD KOJI ŠALJEMO:")
    print(payload)

    async with httpx.AsyncClient() as client:
        res = await client.post(url, headers=headers, json=payload)
        print(f"📤 WhatsApp {template_name} to {to_number} → {res.status_code}")
        print(res.text)

# === Spremi zahtjev u Supabase ===
async def save_to_supabase(phone: str, business_id: str, priority: str, message: str):
    name_part = message.split(",")[0].strip()
    reason_part = ", ".join(message.split(",")[1:]).strip()

    payload = {
        "phone_number": phone,
        "priority": priority,
        "name": name_part,
        "reason": reason_part,
        "created_at": datetime.utcnow().isoformat(),
        "business_id": business_id,
        "status": "primljeno",
        "request_type": "whatsapp",
        "message": message,
        "additional_info": {}
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}",
            headers=headers,
            json=payload
        )

# === Simulacija propuštenog poziva ===
@app.post("/missed-call")
async def handle_missed_call(payload: dict):
    phone_number = payload.get("phone_number")

    if not phone_number:
        return {"error": "Nedostaje phone_number"}

    if not phone_number.startswith("+"):
        phone_number = f"+{phone_number}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }

    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{SUPABASE_URL}/rest/v1/businesses",
            headers=headers,
            params={
                "phone_number": f"eq.{phone_number}",
                "select": "profession,id"
            }
        )
        if res.status_code != 200 or not res.json():
            return {"error": "Obrtnik nije pronađen"}

        profession = res.json()[0]["profession"]
        business_id = res.json()[0]["id"]

    set_state(phone_number, profession, "intro", business_id)
    await send_whatsapp_template(phone_number, profession, "pm_intro")
    return {"message": "pm_intro poslan"}

# === Webhook za Infobip poruke ===
@app.post("/infobip-webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("📥 FULL WEBHOOK:", data)

    results = data.get("results", [])
    for result in results:
        message = result.get("message", {})

        from_number = result.get("from") or message.get("from", "")
        from_number = from_number.strip() if from_number else ""

        text = message.get("text", "").strip()

        if not from_number:
            print("⚠️ Nema from_number u poruci")
            continue

        if not from_number.startswith("+"):
            from_number = f"+{from_number}"

        print("📩 PRIMLJENA PORUKA OD:", from_number)
        print("📩 KORISNIK JE POSLAO:", text)

        state = get_state(from_number)
        if not state:
            print("⚠️ Nema aktivnog toka u Supabase za ovog korisnika")
            continue

        profession = state.get("profession")
        business_id = state.get("business_id")

        if state["step"] == "intro":
            priority = text if text else "opcenito"
            update_step(from_number, "details")
            await send_whatsapp_template(from_number, profession, "pm_details")
            print("✅ Poslan pm_details")

        elif state["step"] == "details":
            await save_to_supabase(
                from_number,
                business_id,
                state.get("priority", "opcenito"),
                text
            )
            await send_whatsapp_template(from_number, profession, "pm_confirmation")
            clear_state(from_number)
            print("✅ Poslan pm_confirmation i spremljeno u bazu")

    return {"status": "primljeno"}

@app.get("/")
async def root():
     return {"message": "AutoPing backend is running 🚀"}
