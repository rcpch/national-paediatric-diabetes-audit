from ...constants import VISIT_FIELDS


def get_visit_categories(visit_instance):
    """
    Returns visit categories present in this visit instance, and tags them as to whether they contain errors
    """
    categories = []
    for category in VISIT_FIELDS:
        category_present = False
        category_error_present = False
        for field in category[1]:
            if hasattr(visit_instance, field):
                if getattr(visit_instance, field) is not None:
                    category_present = True
                    errors = visit_instance.errors
                    if errors:
                        for error in errors:
                            if error is not None:
                                if error["field"] == field:
                                    category_error_present = True
        categories.append(
            {
                "category": category[0].value,
                "present": category_present,
                "has_error": category_error_present,
            }
        )
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
