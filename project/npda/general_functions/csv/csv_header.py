import csv
import io

from project.constants import (
    get_csv_heading_objects_for_year_and_unique_identifier,
)


def csv_header(is_jersey=False, dataset_year=2021):
    unique_identifier = "jersey" if is_jersey else "england"
    HEADINGS_LIST = get_csv_heading_objects_for_year_and_unique_identifier(
        dataset_year=dataset_year, unique_identifier=unique_identifier
    )
    HEADINGS_LIST = [item["heading"] for item in HEADINGS_LIST]

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(HEADINGS_LIST)

    return out.getvalue()
