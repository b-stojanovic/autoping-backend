template_map = {
    "booking_service": {
        "pm_intro": "booking_service_pm_intro",
        "pm_details": "booking_service_pm_details",
        "pm_confirmation": "booking_service_pm_confirmation"
    },
    "emergency_repair": {
        "pm_intro": "emergency_repair_pm_intro",
        "pm_details": "emergency_repair_pm_details",
        "pm_confirmation": "emergency_repair_pm_confirmation"
    },
    "business_query": {
        "pm_intro": "business_query_pm_intro",
        "pm_details": "business_query_pm_details",
        "pm_confirmation": "business_query_pm_confirmation"
    },
    "delivery_order": {
        "pm_intro": "delivery_order_pm_intro",
        "pm_details": "delivery_order_pm_details",
        "pm_confirmation": "delivery_order_pm_confirmation"
    }
}

profession_to_template_type = {
    # Booking services
    "Frizerka / Barber": "booking_service",
    "Kozmetičarka": "booking_service",
    "Groomer za pse": "booking_service",
    "Masažer / Terapeut": "booking_service",
    "Pediker / Maniker": "booking_service",
    "Tatoo majstor": "booking_service",
    "Privatni fitness trener": "booking_service",
    "Depilacija / Lash & brow tech": "booking_service",
    "Šminker / MUA": "booking_service",
    "AutoDetailing": "booking_service",
    "Cvjećarna": "booking_service",

    # Emergency repair
    "Upravnik zgrade": "emergency_repair",
    "Vodoinstalater": "emergency_repair",
    "Električar": "emergency_repair",
    "Stolar": "emergency_repair",
    "Montažer klime / serviser": "emergency_repair",
    "Bravar / Zidar / Keramičar": "emergency_repair",
    "Automehaničar": "emergency_repair",
    "Hitne intervencije (servis 0-24)": "emergency_repair",

    # Business query
    "Agent za nekretnine": "business_query",
    "Bookkeeper / računovođa": "business_query",
    "Građevinski nadzor": "business_query",
    "Arhitekt / dizajner interijera": "business_query",
    "Savjetnik / life coach / psihoterapeut": "business_query",

    # Delivery order
    "Dostava hrane / kolača / ručnih proizvoda": "delivery_order",
    "OPG": "delivery_order",
    "Pečenjarnica / Catering": "delivery_order",
}
