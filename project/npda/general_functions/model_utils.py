import pprint

from django.db.models.fields.related import ForeignKey


def pretty_print_instance(instance) -> None:
    """
    Pretty prints all field attributes and values of a Django model instance.

    Args:
        - instance: Django model instance
    """
    if not instance:
        print("No instance provided.")
        return

    model = instance.__class__
    print(f"{model.__name__} instance:")
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
    pprint(fields_dict, indent=2)
