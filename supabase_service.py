import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ========================
# Utils
# ========================

def _norm_phone(msisdn: str) -> str:
    msisdn = (msisdn or "").replace(" ", "")
    return msisdn if msisdn.startswith("+") else f"+{msisdn}"

# ========================
# User state functions
# ========================

def save_user_state(phone: str, business_id: str, profession: str, step: str):
    try:
        phone = _norm_phone(phone)
        data = {
            "phone": phone,
            "business_id": business_id,
            "profession": profession,
            "step": step
        }
        response = supabase.table("user_states").upsert(data).execute()
        print("💾 User state spremljen:", response)
        return response
    except Exception as e:
        print("❌ Greška pri spremanju user state:", e)
        return None

def get_user_state(phone: str):
    try:
        phone = _norm_phone(phone)
        response = supabase.table("user_states").select("*").eq("phone", phone).limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print("❌ Greška u get_user_state:", e)
        return None

def clear_user_state(phone: str):
    try:
        phone = _norm_phone(phone)
        response = supabase.table("user_states").delete().eq("phone", phone).execute()
        print("🧹 User state obrisan:", response)
        return response
    except Exception as e:
        print("❌ Greška pri brisanju user state:", e)
        return None

# ========================
# Business fetch
# ========================

def get_business_by_id(business_id: str):
    try:
        response = supabase.table("businesses").select("*").eq("id", business_id).limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print("❌ Greška u get_business_by_id:", e)
        return None

# ========================
# Requests
# ========================

def save_request(phone_number: str, business_id: str, message: str, profession: str = None, request_type: str = "booking_service", priority: str = "normal", name: str = None, additional_info: dict = None):
    try:
        data = {
            "phone_number": _norm_phone(phone_number),
            "business_id": business_id,
            "profession": profession or "",
            "message": message,
            "request_type": request_type,
            "priority": priority,
            "name": name or "",
            "additional_info": additional_info or {},
            "status": "pending"
        }
        response = supabase.table("requests").insert(data).execute()
        print("💾 Zahtjev spremljen u Supabase:", response)
        return response
    except Exception as e:
        print("❌ Greška pri spremanju zahtjeva:", e)
        return None
