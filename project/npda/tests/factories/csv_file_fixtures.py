import pytest


@pytest.fixture
def dummy_sheets_folder(request):
    return request.config.rootdir / "project" / "npda" / "dummy_sheets"


@pytest.fixture
def dummy_sheet_csv(dummy_sheets_folder, dataset_year):
    filename = (
        "dummy_sheet_2026_test.csv" if dataset_year == 2026 else "dummy_sheet_test.csv"
    )
    file = dummy_sheets_folder / filename
    with open(file, "r") as f:
        return f.read()


@pytest.fixture
def dummy_sheet_csv_jersey(dummy_sheets_folder):
    file = dummy_sheets_folder / "dummy_sheet_2024_jersey.csv"
    with open(file, "r") as f:
        return f.read()


@pytest.fixture
def dummy_sheet_csv_old_headers(dummy_sheets_folder):
    file = dummy_sheets_folder / "dummy_sheet_old_headers.csv"
    with open(file, "r") as f:
        return f.read()
