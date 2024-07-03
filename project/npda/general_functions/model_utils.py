import logging
from pprint import pformat

from django.db.models.fields.related import ForeignKey

# Logging
logger = logging.getLogger(__name__)


def print_instance_field_attrs(instance):
    """
    Pretty prints all field attributes and values of a Django model instance.

    Args:
        - instance: Django model instance
    """
    if not instance:
        logger.info("No instance provided.")
        return

    model = instance.__class__
    fields_dict = {}
    for field in model._meta.get_fields():
        field_name = field.name
        try:
            field_value = getattr(instance, field_name)
            if isinstance(field, ForeignKey):
                field_value = field_value.pk  # Display related object primary key
            fields_dict[field_name] = field_value
        except AttributeError:
            fields_dict[field_name] = "<error retrieving value>"

    logger.info(f"{model.__name__} instance:\n{pformat(fields_dict, indent=2)}")
