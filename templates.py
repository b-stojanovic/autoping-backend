# templates.py

templates = {
    "booking_service": {
        "pm_intro": "Pozdrav! Trenutno nismo dostupni. Da bismo mogli pomoći, molimo pošaljite nekoliko informacija.",
        "pm_details": "Molimo pošaljite: ime i prezime, uslugu koju želite i željeni termin.\nPrimjer: Ana Kovač, šišanje i feniranje, petak 25.7. ujutro",
        "pm_confirmation": "Hvala! Vaš zahtjev je zaprimljen. Javit ćemo Vam se uskoro za potvrdu. ✂️",
        "required_fields": ["ime i prezime", "usluga", "termin"]
    },
    "emergency_repair": {
        "pm_intro": "Poštovani, trenutačno nismo dostupni. Kako bismo što prije reagirali, pošaljite nam osnovne informacije.",
        "pm_details": "Molimo pošaljite: ime i prezime, adresu, broj stana i kratak opis problema.\nPrimjer: Ivan Horvat, Ulica kralja Petra 12, stan 4, pukla cijev u kuhinji",
        "pm_confirmation": "Hvala! Vaš zahtjev je zaprimljen. Kontaktirat ćemo Vas čim prije.",
        "required_fields": ["ime i prezime", "adresa", "broj stana", "problem"]
    },
    "delivery_order": {
        "pm_intro": "Pozdrav! Hvala što ste nas kontaktirali.",
        "pm_details": "Molimo pošaljite: ime i prezime, proizvod koji želite, opis proizvoda i količinu.\nPrimjer: Marija Kovačić, kolač od čokolade, bez glutena, 2 komada",
        "pm_confirmation": "Vaša narudžba je zaprimljena! Javit ćemo se radi potvrde.",
        "required_fields": ["ime i prezime", "proizvod", "opis proizvoda", "količina"]
    },
    "business_query": {
        "pm_intro": "Pozdrav! Trenutno nismo dostupni. Kako bismo odgovorili na Vaš upit, molimo pošaljite osnovne podatke.",
        "pm_details": "Molimo pošaljite: ime i prezime, email i svoje pitanje.\nPrimjer: Luka Marić, luka@email.com, zanima me da li nudite usluge i u Splitu?",
        "pm_confirmation": "Hvala na upitu! Javit ćemo Vam se uskoro s odgovorom.",
        "required_fields": ["ime i prezime", "email", "pitanje"]
    }
}
