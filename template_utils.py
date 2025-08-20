import unicodedata
from typing import Dict, Tuple
from template_map import template_map, profession_to_template_type

# Ako želiš da ne šalje krivi template, drži STRICT=True (raise umjesto tihog fallbacka)
STRICT = True

VALID_STAGES = {"pm_intro", "pm_details", "pm_confirmation"}

def normalize(s: str) -> str:
    s = (s or "").strip().lower()
    # makni dijakritike
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    # sredi razmake
    s = " ".join(s.split())
    return s

# Normalizirana mapa (ključevi su cleaned verzije onoga što dolazi iz UI-a)
_NORM_PROF_TO_TYPE: Dict[str, str] = {normalize(k): v for k, v in profession_to_template_type.items()}

def resolve_template_type(profession: str) -> str:
    key = normalize(profession)
    ttype = _NORM_PROF_TO_TYPE.get(key)
    if ttype:
        return ttype
    if STRICT:
        raise ValueError(f"Nepoznata profesija (nema mapiranja): '{profession}'")
    # soft fallback ako želiš da uvijek ipak pošalje nešto
    return "booking_service_default"

def get_template_name_by_profession(profession: str, stage: str) -> Tuple[str, str]:
    """
    Vraća (template_name, template_type) na temelju ljudskog naziva profesije i stage-a.
    """
    if stage not in VALID_STAGES:
        raise ValueError(f"Unknown stage: {stage}")

    ttype = resolve_template_type(profession)

    try:
        name = template_map[ttype][stage]
    except KeyError as e:
        if STRICT:
            raise KeyError(
                f"Nedostaje template za type='{ttype}', stage='{stage}'. "
                f"Provjeri template_map."
            ) from e
        # Soft fallback: pokušaj core granu po kategoriji ili default booking
        fallback_type = "booking_service_default"
        name = template_map[fallback_type][stage]
        ttype = fallback_type

    # ✅ Debug printovi s ispravnom varijablom
    print("✅ template_type:", ttype, "| stage:", stage, "| keys:", list(template_map.keys()))
    print("✅ stage:", stage)
    print("✅ template_map keys:", list(template_map.keys()))

    return name, ttype


