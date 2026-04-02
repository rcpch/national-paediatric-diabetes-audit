from django.db.models import DecimalField, Func


class Round(Func):
    function = "ROUND"
    template = "%(function)s(%(expressions)s, 0)"
    output_field = DecimalField()
