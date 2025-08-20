# template_map.py

# =========================
# TEMPLATE NAME REGISTRY
# =========================
# Svaki ključ (template_type) ima 3 koraka:
#   - pm_intro
#   - pm_details
#   - pm_confirmation
#
# Napomena:
#  - Nazive dolje uskladi s onima u Infobipu ako si negdje koristila drukčiji pattern.

template_map = {
    # ==== Core tipovi (ostavi ih) ====
    "booking_service": {
        "pm_intro": "booking_service_pm_intro",
        "pm_details": "booking_service_pm_details",
        "pm_confirmation": "booking_service_pm_confirmation",
    },
    "emergency_repair": {
        "pm_intro": "emergency_repair_pm_intro",
        "pm_details": "emergency_repair_pm_details",
        "pm_confirmation": "emergency_repair_pm_confirmation",
    },
    "business_query": {
        "pm_intro": "business_query_pm_intro",
        "pm_details": "business_query_pm_details",
        "pm_confirmation": "business_query_pm_confirmation",
    },
    "delivery_order": {
        "pm_intro": "delivery_order_pm_intro",
        "pm_details": "delivery_order_pm_details",
        "pm_confirmation": "delivery_order_pm_confirmation",
    },

    # ==== Booking per-profession ====
    "booking_service_default": {
        "pm_intro": "booking_service_default_pm_intro",
        "pm_details": "booking_service_default_pm_details",
        "pm_confirmation": "booking_service_default_pm_confirmation",
    },
    "booking_service_beauty": {
        "pm_intro": "booking_service_beauty_pm_intro",
        "pm_details": "booking_service_beauty_pm_details",
        "pm_confirmation": "booking_service_beauty_pm_confirmation",
    },
    "booking_service_groomer": {
        "pm_intro": "booking_service_groomer_pm_intro",
        "pm_details": "booking_service_groomer_pm_details",
        "pm_confirmation": "booking_service_groomer_pm_confirmation",
    },
    "booking_service_massage": {
        "pm_intro": "booking_service_massage_pm_intro",
        "pm_details": "booking_service_massage_pm_details",
        "pm_confirmation": "booking_service_massage_pm_confirmation",
    },
    "booking_service_nails": {
        "pm_intro": "booking_service_nails_pm_intro",
        "pm_details": "booking_service_nails_pm_details",
        "pm_confirmation": "booking_service_nails_pm_confirmation",
    },
    "booking_service_tattoo": {
        "pm_intro": "booking_service_tattoo_pm_intro",
        "pm_details": "booking_service_tattoo_pm_details",
        "pm_confirmation": "booking_service_tattoo_pm_confirmation",
    },
    "booking_service_fitness": {
        "pm_intro": "booking_service_fitness_pm_intro",
        "pm_details": "booking_service_fitness_pm_details",
        "pm_confirmation": "booking_service_fitness_pm_confirmation",
    },
    "booking_service_makeup": {
        "pm_intro": "booking_service_makeup_pm_intro",
        "pm_details": "booking_service_makeup_pm_details",
        "pm_confirmation": "booking_service_makeup_pm_confirmation",
    },
    "booking_service_autodetail": {
        "pm_intro": "booking_service_autodetail_pm_intro",
        "pm_details": "booking_service_autodetail_pm_details",
        "pm_confirmation": "booking_service_autodetail_pm_confirmation",
    },
    "booking_service_flower_shop": {
        "pm_intro": "booking_service_flower_shop_pm_intro",
        "pm_details": "booking_service_flower_shop_pm_details",
        "pm_confirmation": "booking_service_flower_shop_pm_confirmation",
    },

    # ==== Emergency repair (per-profession) ====
    "emergency_repair_upravnik": {
        "pm_intro": "emergency_repair_upravnik_pm_intro",
        "pm_details": "emergency_repair_upravnik_pm_details",
        "pm_confirmation": "emergency_repair_upravnik_pm_confirmation",
    },
    "emergency_repair_vodoinstalater": {
        "pm_intro": "emergency_repair_vodoinstalater_pm_intro",
        "pm_details": "emergency_repair_vodoinstalater_pm_details",
        "pm_confirmation": "emergency_repair_vodoinstalater_pm_confirmation",
    },
    "emergency_repair_elektricar": {
        "pm_intro": "emergency_repair_elektricar_pm_intro",
        "pm_details": "emergency_repair_elektricar_pm_details",
        "pm_confirmation": "emergency_repair_elektricar_pm_confirmation",
    },
    "emergency_repair_stolar": {
        "pm_intro": "emergency_repair_stolar_pm_intro",
        "pm_details": "emergency_repair_stolar_pm_details",
        "pm_confirmation": "emergency_repair_stolar_pm_confirmation",
    },
    "emergency_repair_klima_serviser": {
        "pm_intro": "emergency_repair_klima_serviser_pm_intro",
        "pm_details": "emergency_repair_klima_serviser_pm_details",
        "pm_confirmation": "emergency_repair_klima_serviser_pm_confirmation",
    },
    "emergency_repair_bravar_zidar_keramicar": {
        "pm_intro": "emergency_repair_bravar_zidar_keramicar_pm_intro",
        "pm_details": "emergency_repair_bravar_zidar_keramicar_pm_details",
        "pm_confirmation": "emergency_repair_bravar_zidar_keramicar_pm_confirmation",
    },
    "emergency_repair_automehanicar": {
        "pm_intro": "emergency_repair_automehanicar_pm_intro",
        "pm_details": "emergency_repair_automehanicar_pm_details",
        "pm_confirmation": "emergency_repair_automehanicar_pm_confirmation",
    },
    "emergency_repair_24h": {
        "pm_intro": "emergency_repair_24h_pm_intro",
        "pm_details": "emergency_repair_24h_pm_details",
        "pm_confirmation": "emergency_repair_24h_pm_confirmation",
    },

    # ==== Business query (per-profession) ====
    "business_query_real_estate_agent": {
        "pm_intro": "business_query_real_estate_agent_pm_intro",
        "pm_details": "business_query_real_estate_agent_pm_details",
        "pm_confirmation": "business_query_real_estate_agent_pm_confirmation",
    },
    "business_query_bookkeeper": {
        "pm_intro": "business_query_bookkeeper_pm_intro",
        "pm_details": "business_query_bookkeeper_pm_details",
        "pm_confirmation": "business_query_bookkeeper_pm_confirmation",
    },
    "business_query_gradevinski_nadzor": {
        "pm_intro": "business_query_gradevinski_nadzor_pm_intro",
        "pm_details": "business_query_gradevinski_nadzor_pm_details",
        "pm_confirmation": "business_query_gradevinski_nadzor_pm_confirmation",
    },
    "business_query_arhitekt_dizajner_interijera": {
        "pm_intro": "business_query_arhitekt_dizajner_interijera_pm_intro",
        "pm_details": "business_query_arhitekt_dizajner_interijera_pm_details",
        "pm_confirmation": "business_query_arhitekt_dizajner_interijera_pm_confirmation",
    },
    "business_query_savjetnik_psihoterapeut_coach": {
        "pm_intro": "business_query_savjetnik_psihoterapeut_coach_pm_intro",
        "pm_details": "business_query_savjetnik_psihoterapeut_coach_pm_details",
        "pm_confirmation": "business_query_savjetnik_psihoterapeut_coach_pm_confirmation",
    },

    # ==== Delivery order (per-profession) ====
    "delivery_order_food": {
        "pm_intro": "delivery_order_food_pm_intro",
        "pm_details": "delivery_order_food_pm_details",
        "pm_confirmation": "delivery_order_food_pm_confirmation",
    },
    "delivery_order_opg": {
        "pm_intro": "delivery_order_opg_pm_intro",
        "pm_details": "delivery_order_opg_pm_details",
        "pm_confirmation": "delivery_order_opg_pm_confirmation",
    },
    "delivery_order_catering": {
        "pm_intro": "delivery_order_catering_pm_intro",
        "pm_details": "delivery_order_catering_pm_details",
        "pm_confirmation": "delivery_order_catering_pm_confirmation",
    },
}

# =========================
# PROFESSION → TEMPLATE TYPE
# =========================
# Ova mapa MORA pokazivati na gore definirane ključeve (template_type).
# Ključevi su pisani kako ti ih UI šalje (s dijakriticima).

profession_to_template_type = {
    # Booking services
    "Frizerka / Barber": "booking_service_default",
    "Kozmetičarka": "booking_service_beauty",
    "Groomer za pse": "booking_service_groomer",
    "Masažer / Terapeut": "booking_service_massage",
    "Pediker / Maniker": "booking_service_nails",
    "Tatoo majstor": "booking_service_tattoo",
    "Privatni fitness trener": "booking_service_fitness",
    "Depilacija / Lash & brow tech": "booking_service_beauty",
    "Šminker / MUA": "booking_service_makeup",
    "AutoDetailing": "booking_service_autodetail",
    "Cvjećarna": "booking_service_flower_shop",

    # Emergency repair
    "Upravnik zgrade": "emergency_repair_upravnik",
    "Vodoinstalater": "emergency_repair_vodoinstalater",
    "Električar": "emergency_repair_elektricar",
    "Stolar": "emergency_repair_stolar",
    "Montažer klime / serviser": "emergency_repair_klima_serviser",
    "Bravar / Zidar / Keramičar": "emergency_repair_bravar_zidar_keramicar",
    "Automehaničar": "emergency_repair_automehanicar",
    "Hitne intervencije (servis 0-24)": "emergency_repair_24h",

    # Business query
    "Agent za nekretnine": "business_query_real_estate_agent",
    "Bookkeeper / računovođa": "business_query_bookkeeper",
    "Građevinski nadzor": "business_query_gradevinski_nadzor",
    "Arhitekt / dizajner interijera": "business_query_arhitekt_dizajner_interijera",
    "Savjetnik / life coach / psihoterapeut": "business_query_savjetnik_psihoterapeut_coach",

    # Delivery order
    "Dostava hrane / kolača / ručnih proizvoda": "delivery_order_food",
    "OPG": "delivery_order_opg",
    "Pečenjarnica / Catering": "delivery_order_catering",
}
