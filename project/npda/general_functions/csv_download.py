from django.apps import apps
from django.http import HttpResponse
from django.shortcuts import get_object_or_404


def download_csv(request, submission_id):
    """
    Download a CSV file.
    """
    Submission = apps.get_model(app_label="npda", model_name="Submission")
    submission = get_object_or_404(Submission, id=submission_id)
    file_path = submission.csv_file.path
    file_name = submission.csv_file.name.split("/")[-1]

    with open(file_path, "rb") as f:
        response = HttpResponse(f.read(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        return response
