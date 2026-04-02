from functools import partial as curry


class HelpTextMixin:
    """
    Thanks https://bradmontgomery.net/blog/django-hack-help-text-modal-instance/ for this snippet
    Returns the help text methods to the template
    Can use {{visit.get_*field*_help_label_text}} and {{visit.get_*field*_help_reference_text}}
    in the template
    """

    def _get_label_text(self, field_name):
        """Given a field name, return it's label help text."""
        for field in self._meta.fields:
            if field.name == field_name:
                return field.get_field_label()

    def _get_help_label_text(self, field_name):
        """Given a field name, return it's label help text."""
        for field in self._meta.fields:
            if field.name == field_name:
                return field.get_field_help_text()

    def _get_help_reference_text(self, field_name):
        """Given a field name, return it's reference help text."""
        for field in self._meta.fields:
            if field.name == field_name:
                return field.get_field_justification_or_standard()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Again, iterate over all of our field objects.
        for field in self._meta.fields:
            # Create a string, get_FIELDNAME_help text
            label_method_name = f"get_{field.name}_label_text"
            help_label_method_name = f"get_{field.name}_help_label_text"
            reference_method_name = f"get_{field.name}_help_reference_text"

            # We can use curry to create the method with a pre-defined argument
            label_curried_method = curry(self._get_label_text, field_name=field.name)
            help_label_curried_method = curry(
                self._get_help_label_text, field_name=field.name
            )
            reference_curried_method = curry(
                self._get_help_reference_text, field_name=field.name
            )

            # And we add this method to the instance of the class.
            setattr(self, label_method_name, label_curried_method)
            setattr(self, help_label_method_name, help_label_curried_method)
            setattr(self, reference_method_name, reference_curried_method)

    class Meta:
        abstract = True
