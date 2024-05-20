from django.db import models

class CategorisedFieldMixin:
    def __init__(self, *args, category=None, **kwargs):
        self.category = category
        super().__init__(*args, **kwargs)

class CategorisedDateField(CategorisedFieldMixin, models.DateField):
    pass

class CategorisedDecimalField(CategorisedFieldMixin, models.DecimalField):
    pass

class CategorisedDateField(CategorisedFieldMixin, models.DateField):
    pass

class CategorisedPositiveSmallIntegerField(CategorisedFieldMixin, models.PositiveSmallIntegerField):
    pass

class CategorisedIntegerField(CategorisedFieldMixin, models.IntegerField):
    pass

class CategorisedCharField(CategorisedFieldMixin, models.CharField):
    pass