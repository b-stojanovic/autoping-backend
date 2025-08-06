# state_memory.py

from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def set_state(phone, profession, step, business_id):
    """
    Sprema novi user_state u Supabase
    """
    # Prvo brišemo ako već postoji
    supabase.table("user_states").delete().eq("phone", phone).execute()

    data = {
        "phone": phone,
        "step": step,
        "profession": profession,
        "business_id": business_id
    }

    supabase.table("user_states").insert(data).execute()


def get_state(phone):
    """
    Dohvaća user_state iz Supabase
    """
    result = supabase.table("user_states").select("*").eq("phone", phone).limit(1).execute()
    if result.data:
        return result.data[0]
    return None


def update_step(phone, new_step):
    """
    Ažurira step korisnika u Supabase
    """
    supabase.table("user_states").update({"step": new_step}).eq("phone", phone).execute()


def clear_state(phone):
    """
    Briše user_state iz Supabase
    """
    supabase.table("user_states").delete().eq("phone", phone).execute()
