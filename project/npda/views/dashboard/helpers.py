"""Helper functions for dashboard views including calculations and data manipulation."""

# Python imports
import logging
from collections import Counter, defaultdict
from decimal import Decimal
from typing import Literal

from dateutil.relativedelta import relativedelta
from django.db.models import QuerySet

from project.constants.ethnicities import ETHNICITIES
from project.constants.sex_types import SEX_TYPE
from project.constants.types.kpi_types import KPIRegistry
from project.npda.kpi_class.kpis import CalculateKPIS
from project.npda.models.patient import Patient

# LOGGING
logger = logging.getLogger(__name__)





def convert_value_counts_dict_to_pct(value_counts_dict: dict):
    """
    Convert a value counts dict to percentages
    """
    total = sum(value_counts_dict.values())

    value_counts_dict_pct = {}

    for key, value in value_counts_dict.items():
        pct = value / total * 100
        value_counts_dict_pct[key] = int(pct) if pct >= 1 else round(pct, 1)

    return value_counts_dict_pct


def get_list_of_shortened_ticktext_labels(
    x: list[str],
    cut_off_char_len=10,
) -> list[str]:
    """Takes in a list of labels and intelligently shortens,
    adding `...` if appropriate."""
    shortened_ticktext_labels = []
    for label in x:
        if len(label) > cut_off_char_len:
            # Don't want to cut off in middle of word so split on spaces,
            # and keep as many full words as possible until we reach the cut off
            shortened_label_parts = []
            current_len = 0
            label_split = label.split(" ")
            for word in label_split:
                shortened_label_parts.append(word)
                current_len += len(word)
                if current_len > cut_off_char_len:
                    break

            shortened_label = f"{' '.join(shortened_label_parts)}"
            if len(shortened_label_parts) < len(label_split):
                shortened_label += "..."
            shortened_ticktext_labels.append(shortened_label)
        else:
            shortened_ticktext_labels.append(label)
    return shortened_ticktext_labels
