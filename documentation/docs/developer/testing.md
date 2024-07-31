---
title: Testing
reviewers: Dr Anchit Chandran
---

## Getting started

Run all tests from the root directory:

```shell
pytest
```

## Useful Pytest flags

Some useful flags to improve the DX of testing.

### Only re-run failing tests

```shell
pytest -lf
```

### Run a specific test file, e.g. run all tests in only `test_npda_user_model_actions.py`

```shell
pytest project/npda/tests/permissions_tests/test_npda_user_model_actions.py
```

Use `::` notation to run a specific test within a file e.g.:

```shell
pytest project/npda/tests/permissions_tests/test_npda_user_model_actions.py::test_npda_user_list_view_rcpch_audit_team_can_view_all_users
```

### Start a completely clean run, clearing the cache (usually not required)

```shell
pytest --cache-clear
```

### Run tests through keyword expression

NOTE: this is sometimes slightly slower.

```shell
pytest -k "MyClass and not method"
```

## `pytest.ini` config file

Explanations and notes on our global `pytest.ini` configuration.

### Creating new tests

Test files are found as any `.py` prepended with `test_`:

```ini
# SET FILENAME FORMATS OF TESTS
python_files = test_*.py
```

### Flags set for all `pytest` runs

```init
# RE USE TEST DB AS DEFAULT
addopts =
    --reuse-db
    -k "not examples"
```

- `--reuse-db` allows a specified starting state testing database to be used between tests. All tests begin with this seeded starting state. The testing db is rolled back to the starting state after each state.

## Test Database

Every first test in a file should include the following fixtures to ensure the test database is correctly set up for when a particular test file is run independently:

```python
@pytest.mark.django_db
def test_npda_user_list_view_users_can_only_see_users_from_their_pdu(
    seed_users_fixture,
    seed_groups_fixture,
    seed_patients_fixture,
):
```

### `seed_users_fixture`

The testing database should include `8 NPDAUsers`.

At each of the `2` PDUs, GOSH and Alder Hey:

```py title='seed_users.py'
GOSH_PZ_CODE = "PZ196"
ALDER_HEY_PZ_CODE = "PZ074"
```

The following `4` user types are seeded:

```py title='seed_users.py'
users = [
    test_user_audit_centre_reader_data,
    test_user_audit_centre_editor_data,
    test_user_audit_centre_coordinator_data,
    test_user_rcpch_audit_team_data,
]
```

### `seed_groups_fixture`

Uses the `groups_seeder` to set `Groups` for `NPDAUsers`.

### `seed_patients_fixture`

*not yet implemented*

## Factories

Factories enable the intuitive and fast creation of testing instances, particularly in cases where multiple related models are required.

Factories are set up to set sensible defaults wherever possible, which can be overridden through keyword arguments.

Ideally, in all tests, if a model instance is being created, it should be done through its model Factory.

### `NPDAUserFactory`

Example usage below.

NOTE: we do not need to manually create `OrganisationEmployer`s and `PaediatricsDiabetesUnit` with associations. 

Once an instance of `NPDAUserFactory` is created, the related models will also be created and assigned the relations. These are set using the `organisation_employers` kwarg, with the value being an array of `pz_codes` as strings.

```py title="seed_users.py"
# GOSH User
new_user_gosh = NPDAUserFactory(
    first_name=first_name,
    role=user.role,
    # Assign flags based on user role
    is_active=is_active,
    is_staff=is_staff,
    is_rcpch_audit_team_member=is_rcpch_audit_team_member,
    is_rcpch_staff=is_rcpch_staff,
    groups=[user.group_name],
    view_preference=(
        VIEW_PREFERENCES[2][0]
        if user.role == RCPCH_AUDIT_TEAM
        else VIEW_PREFERENCES[0][0]
    ),
    organisation_employers=[GOSH_PZ_CODE],
)

# Alder hey user
new_user_alder_hey = NPDAUserFactory(
    first_name=first_name,
    role=user.role,
    # Assign flags based on user role
    is_active=is_active,
    is_staff=is_staff,
    is_rcpch_audit_team_member=is_rcpch_audit_team_member,
    is_rcpch_staff=is_rcpch_staff,
    groups=[user.group_name],
    organisation_employers=[ALDER_HEY_PZ_CODE],
)
```

### `PatientFactory`

Once an instance of `PatientFactory` is created, a related `TransferFactory` instance is also generated with the associated `PaediatricsDiabetesUnitFactory` instance.

### `PaediatricsDiabetesUnitFactory`

Multiple parent factories require the instantiation of multiple `PaediatricsDiabetesUnitFactory`s.

As there is a composite unique constraint set on the [`pz_code`, `ods_code`] attributes, we do not want to create multiple instances with duplicate values; instead, we want to mimic the Django ORM's `.get_or_create()` method.

This is emulated using an override on this factory's `._create()` method:

```py title="paediatrics_diabetes_unit_factory.py"
@classmethod
def _create(cls, model_class, *args, **kwargs):
    """
    Custom create method to handle get_or_create logic for PaediatricsDiabetesUnit.

    Each PDU has a composite unique constraint for pz_code and ods_code. This mimics
    a get or create operation every time a new PDUFactory instance is created.
    """
    pz_code = kwargs.pop("pz_code", None)
    ods_code = kwargs.pop("ods_code", None)

    if pz_code and ods_code:
        pdu, created = PaediatricDiabetesUnit.objects.get_or_create(
            pz_code=pz_code,
            ods_code=ods_code,
        )
        return pdu

    return super()._create(model_class, *args, **kwargs)
```