# python / django imports
import re
from datetime import date

# django imports
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

# 3rd party imports

# RCPCH imports

def not_in_the_future_validator(value):
    if value and value <= date.today():
        return value
    elif value:
        raise ValidationError("Cannot be in the future")

class CapitalAndSymbolValidator:
    def __init__(
        self,
        number_of_capitals=1,
        number_of_symbols=1,
        symbols="~!@#$%^&*()+:;'[]",
    ):
        self.number_of_capitals = number_of_capitals
        self.number_of_symbols = number_of_symbols
        self.symbols = symbols

    def validate(self, password, user=None):
        capitals = [char for char in password if char.isupper()]
        symbols = [char for char in password if char in self.symbols]
        if len(capitals) < self.number_of_capitals:
            raise ValidationError(
                _(
                    "This password must contain at least %(min_length)d capital letters."
                ),
                code="password_too_short",
                params={"min_length": self.number_of_capitals},
            )
        if len(symbols) < self.number_of_symbols:
            raise ValidationError(
                _("This password must contain at least %(min_length)d symbols."),
                code="password_too_short",
                params={"min_length": self.number_of_symbols},
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(number_of_capitals)d capital letters and %(number_of_symbols)d symbols."
            % {
                "number_of_capitals": self.number_of_capitals,
                "number_of_symbols": self.number_of_symbols,
            }
        )


class NumberValidator(object):
    def validate(self, password, user=None):
        if not re.findall(r"\d", password):
            raise ValidationError(
                _("The password must contain at least 1 digit, 0-9."),
                code="password_no_number",
            )

    def get_help_text(self):
        return _("Your password must contain at least one number.")
