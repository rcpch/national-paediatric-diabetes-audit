import re
import json
from django import template, forms
from django.utils.safestring import mark_safe
from django.conf import settings
from ..general_functions import get_visit_category_for_field
from ...constants import VisitCategories, VISIT_FIELD_FLAT_LIST, VISIT_FIELDS
from datetime import date

register = template.Library()


@register.filter
def is_in(url_name, args):
    """
    receives the request.resolver_match.url_name
    and compares with the template name (can be a list in a string separated by commas),
    returning true if a match is present
    """
    if args is None:
        return None
    arg_list = [arg.strip() for arg in args.split(",")]
    if url_name in arg_list:
        return True
    else:
        return False


class_re = re.compile(r'(?<=class=["\'])(.*)(?=["\'])')


@register.filter
def match_category(value):
    """
    matches a category to a field in the visit form
    """
    field_name = value.name
    visit_category = get_visit_category_for_field(field_name=field_name)
    if visit_category:
        return visit_category.value
    else:
        return None


@register.filter
def colour_for_category(category):
    # returns a colour for a given category
    colours = [
        {"category": VisitCategories.HBA1, "colour": "rcpch_red_light_tint2"},
        {"category": VisitCategories.MEASUREMENT, "colour": "rcpch_red"},
        {"category": VisitCategories.TREATMENT, "colour": "rcpch_orange"},
        {"category": VisitCategories.CGM, "colour": "rcpch_orange_light_tint2"},
        {"category": VisitCategories.BP, "colour": "rcpch_yellow"},
        {"category": VisitCategories.FOOT, "colour": "rcpch_yellow_light_tint2"},
        {"category": VisitCategories.DECS, "colour": "rcpch_strong_green"},
        {"category": VisitCategories.ACR, "colour": "rcpch_strong_green_light_tint2"},
        {"category": VisitCategories.CHOLESTEROL, "colour": "rcpch_aqua_green"},
        {
            "category": VisitCategories.THYROID,
            "colour": "rcpch_aqua_green_light_tint2",
        },
        {"category": VisitCategories.COELIAC, "colour": "rcpch_purple"},
        {"category": VisitCategories.PSYCHOLOGY, "colour": "rcpch_purple_light_tint2"},
        {"category": VisitCategories.SMOKING, "colour": "rcpch_gold"},
        {"category": VisitCategories.DIETETIAN, "colour": "rcpch_vivid_green"},
        {"category": VisitCategories.SICK_DAY, "colour": "rcpch_pink"},
        {"category": VisitCategories.FLU, "colour": "rcpch_dark_blue"},
        {"category": VisitCategories.HOSPITAL_ADMISSION, "colour": "rcpch_light_blue"},
    ]
    for colour in colours:
        if colour["category"].value == category:
            return colour["colour"]
    return None


@register.simple_tag
def category_for_first_item(form, field, index):
    """
    Return categories only for those first fields in the category
    """
    if index < 3:
        if index == 2:
            current_visit_category = get_visit_category_for_field(field_name=field.name)
            return current_visit_category.value
        return ""

    current_visit_category = get_visit_category_for_field(field_name=field.name)
    if field.name == "visit_date":
        return ""

    previous_field = list(form)[index - 2]
    previous_visit_category = get_visit_category_for_field(
        field_name=previous_field.name
    )

    if current_visit_category == previous_visit_category:
        return ""
    else:
        return current_visit_category.value


@register.simple_tag
def site_contact_email():
    return settings.SITE_CONTACT_EMAIL


@register.filter
def is_select(widget):
    return isinstance(widget, (forms.Select, forms.SelectMultiple))


@register.filter
def error_for_field(messages, field):
    """
    Returns all errors for a given field
    """
    concatenated_fields = ""
    if messages is None:
        messages = []
    if field in VISIT_FIELD_FLAT_LIST:
        return "There are errors associated with one or more of this child's visits."
    if len(messages) > 0:
        for message in messages:
            if field == message["field"]:
                concatenated_fields += f"{message['message']},\n"
    return concatenated_fields if len(concatenated_fields) > 0 else []


@register.filter
def errors_for_category(category, error_list):
    """
    Returns all error messages for a given category
    """
    selected_category = None
    for visit_category in VisitCategories:
        if visit_category.value == category:
            selected_category = visit_category

    final_string = ""
    for error in error_list:
        if error:
            error_field_list = []

            for visit_field in VISIT_FIELDS:
                if visit_field[0] == selected_category:
                    error_field_list = visit_field[1]
            if len(error_field_list) > 0:
                if error["field"] in error_field_list:
                    final_string += f"{error['message']}\n"
    return final_string


@register.filter
def is_dateinput(widget):
    return isinstance(widget, (forms.DateInput))


@register.simple_tag
def today_date():
    return date.today().strftime("%Y-%m-%d")


@register.simple_tag
def patient_valid(patient):
    if not patient.is_valid or patient.visit_set.filter(is_valid=False).exists():
        return False
    else:
        return True
