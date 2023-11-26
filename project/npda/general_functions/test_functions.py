from django.apps import apps
from ...constants import PZ_CODES


def test_pzs():
    Organisation = apps.get_model("npda", "Organisation")
    Trust = apps.get_model("npda", "Trust")
    matches = 0
    total = 0
    updates = []
    failed = []
    for code in PZ_CODES:
        if Organisation.objects.filter(name__icontains=code["paediatric_unit"].upper()).exists():
            matches += 1
            org = Organisation.objects.filter(name__icontains=code["paediatric_unit"].upper()).first()
            code.update({'ods_code': org.ods_code})
            updates.append(code)
        else:
            print(f"failed {code["paediatric_unit"].upper()}")
            failed.append(code["paediatric_unit"])
        total += 1
    print(f"matches: {matches}, total: {total}")
    
    for failure in failed:
        if Trust.objects.filter(name__icontains=failure).exists():
            trust = Organisation.objects.filter(name__icontains=failure.upper()).first()
            # code.update({'ods_code': trust.ods_code})
            print(f"didnt fail: {failure}")
        else:
            print(f"failed {failure.upper()}")

