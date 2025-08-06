# state_memory.py

# state_memory.py

from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def set_state(phone, profession, step, business_id):
    await supabase.table("user_states").delete().eq("phone", phone).execute()

    data = {
        "phone": phone,
        "step": step,
        "profession": profession,
        "business_id": business_id
    }

    await supabase.table("user_states").insert(data).execute()

async def get_state(phone):
    result = await supabase.table("user_states").select("*").eq("phone", phone).limit(1).execute()
    if result.data:
        return result.data[0]
    return None

async def update_step(phone, new_step):
    await supabase.table("user_states").update({"step": new_step}).eq("phone", phone).execute()

async def clear_state(phone):
    await supabase.table("user_states").delete().eq("phone", phone).execute()
