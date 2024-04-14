from ...constants import VISIT_FIELDS


def get_visit_categories(visit_instance):
    """
    Returns visit categories present in this visit instance
    """
    categories = []
    for category in VISIT_FIELDS:
        category_present = False
        for field in category[1]:
            if hasattr(visit_instance, field):
                category_present = True
        categories.append({category[0].value: category_present})
    return categories


def get_visit_category_for_field(field_name):
    """
    returns the visit category as an Enum for the field name in the Visit model
    """
    for category in VISIT_FIELDS:
        for field in category[1]:
            if field == field_name:
                return category[0]
    return None
