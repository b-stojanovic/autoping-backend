# supabase_service.py

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def save_request_to_supabase(phone_number, message):
    data = {
        "phone_number": phone_number,
        "message": message,
        "status": "new"
    }

    try:
        response = supabase.table("requests").insert(data).execute()
        print("💾 Zahtjev spremljen u Supabase:", response)
    except Exception as e:
        print("❌ Greška pri spremanju zahtjeva:", e)
