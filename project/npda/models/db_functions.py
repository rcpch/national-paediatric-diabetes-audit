from django.db.models import Func, F, DecimalField


class Round(Func):
    function = "ROUND"
    template = "%(function)s(%(expressions)s, 0)"
    output_field = DecimalField()
