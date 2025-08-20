# supabase_service.py

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def save_user_state(phone: str, business_id: str, profession: str, step: str):
    try:
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
        response = supabase.table("user_states").select("*").eq("phone", phone).order("created_at", desc=True).limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print("❌ Greška u get_user_state:", e)
        return None

def clear_user_state(phone: str):
    try:
        response = supabase.table("user_states").delete().eq("phone", phone).execute()
        print("🧹 User state obrisan:", response)
        return response
    except Exception as e:
        print("❌ Greška pri brisanju user state:", e)
        return None
