from django.apps import apps
from ...constants import PZ_CODES


def test_pzs():
    Organisation = apps.get_model("npda", "Organisation")
    Trust = apps.get_model("npda", "Trust")
    matches = 0
    total = 0
    for code in PZ_CODES:
        if "ods_code" in code:
            matches += 1
        else:
            print(code)
        total += 1
    print(f"total: {total}, matches: {matches}, failed: {total-matches}")
