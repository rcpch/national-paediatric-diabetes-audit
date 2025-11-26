import json
import csv
from io import StringIO

from django.apps import apps
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from ..write_errors_to_xlsx import write_errors_to_xlsx
from ....constants.csv_headings import CSV_HEADING_OBJECTS, UNIQUE_IDENTIFIER_JERSEY, UNIQUE_IDENTIFIER_ENGLAND
from ....npda.models.visit import Visit


def download_csv_file(request, submission_id):
    """
    Download a CSV file.
    """
    Submission = apps.get_model(app_label="npda", model_name="Submission")
    submission = get_object_or_404(Submission, id=submission_id)

    response = HttpResponse(submission.csv_file, content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="{submission.csv_file_name}"'
    )
    return response


def download_xlsx(request, submission_id):
    """
    Download a XLSX file.
    NB: This repurposes download_csv with a simple file rename.
    """
    Submission = apps.get_model(app_label="npda", model_name="Submission")
    submission = get_object_or_404(Submission, id=submission_id)

    filename_without_extension = ".".join(submission.csv_file_name.split(".")[:-1])
    xlsx_file_name = f"{filename_without_extension}_data_quality_report.xlsx"

    errors = {}
    if submission.errors:
        errors = json.loads(submission.errors)

    xlsx_file = write_errors_to_xlsx(errors or {}, submission.csv_file)

    response = HttpResponse(xlsx_file, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{xlsx_file_name}"'
    return response


def export_as_csv(request, submission):
    out = StringIO()
    writer = csv.writer(out, delimiter=",")

    pz_code = submission.paediatric_diabetes_unit.pz_code
    is_jersey = pz_code == "PZ248"

    if is_jersey:
        HEADINGS_LIST = UNIQUE_IDENTIFIER_JERSEY + CSV_HEADING_OBJECTS
    else:
        HEADINGS_LIST = UNIQUE_IDENTIFIER_ENGLAND + CSV_HEADING_OBJECTS

    header = [row["heading"] for row in HEADINGS_LIST]
    writer.writerow(header)

    visits = Visit.objects.filter(patient__in=submission.patients.all()).select_related("patient").prefetch_related("patient__paediatric_diabetes_units")

    for visit in visits:
        row = []
        transfer = visit.patient.paediatric_diabetes_units.filter(paediatric_diabetes_unit__pz_code=pz_code).first()

        for row_heading in HEADINGS_LIST:
            heading = row_heading["heading"]
            model = row_heading.get("model")
            field_name = row_heading.get("model_field")

            match (heading, model):
                case ("PDU Number", _):
                    row.append(submission.paediatric_diabetes_unit.pz_code)
                case (_, "Visit"):
                    row.append(getattr(visit, field_name))
                case (_, "Patient"):
                    row.append(getattr(visit.patient, field_name))
                case (_, "Transfer"):
                    row.append(getattr(transfer, field_name))
                case _:
                    raise Exception(f"Unknown model: {model}")
        
        writer.writerow(row)

    filename = f"{submission.paediatric_diabetes_unit.pz_code}-{submission.audit_period.display_name()}.csv"

    response = HttpResponse(out.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response