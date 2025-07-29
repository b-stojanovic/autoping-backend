# template_utils.py

from template_map import profession_to_template_type
from templates import templates

def get_template_by_profession(profession: str):
    template_type = profession_to_template_type.get(profession)

    if not template_type:
        # fallback ako ne postoji mapirano zanimanje
        template_type = "booking_service"

    template_data = templates.get(template_type)
    return template_data or {}
