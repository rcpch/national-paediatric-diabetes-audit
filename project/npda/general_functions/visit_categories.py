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
