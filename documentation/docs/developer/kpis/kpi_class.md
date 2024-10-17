# KPI Class

## `CalculateKPIS`
The entrypoint for everything relevant to KPIs _should_ be the `CalculateKPIS`
class. Missing functionality should be added to this class.

This class is responsible for calculating all KPIs for a given subset of of patients, set through its `self.patients` attribute. There are various methods used to calculate KPIs for different abstractions (e.g. `calculate_kpis_for_single_patient` vs `calculate_kpis_for_pdus`), but each method is a wrapper that works to set the `self.patients` attribute, and then they all call the `_calculate_kpis` method.

### Initialisation

To initialise an instance of the `CalculateKPIS` class, you can pass in optional parameters to define the audit period and whether to return patient querysets as part of the KPI calculations.

**Parameters**

- `calculation_date` (`date`, optional):
   The date used to define the start and end dates of the audit period, used throughout calculations. If no date is provided, the current date is used as the default.

- `return_pt_querysets` (`bool`, optional):
   If set to `True`, the calculated KPIs will include patient querysets used during the KPI calculation. The default is `False`.

```python
from datetime import date
from project.npda.kpi_class.kpis import CalculateKPIS

# Initialise with default parameters
kpi_calculator = CalculateKPIS()

# Example 2: Initialise with a specific audit date
calculation_date = date(2023, 1, 1)
kpi_calculator_SPECIFIC_DATE = CalculateKPIS(calculation_date=calculation_date)
```

### Calculation methods

We can then use one of the `calculate_kpis_for_` methods to calculate KPIs:

1) `calculate_kpis_for_patients` (QuerySet[Patient])
    - Calculate KPIs for given patients.
2) `calculate_kpis_for_pdus` (list[str])
    - Calculate KPIs for given PZ codes.
3) `calculate_kpis_for_single_patient` (Patient)
    - Calculate KPIs for a single patient. Runs all calculations (required as KPIs 1-12 are used as denominators for subsequent KPIs) but returns a subset relevant to a single patient.

All `calculate_` methods return a `KPICalculationsObject`. This is used to represent the results of  calculations across the specified audit period. It contains information about the audit dates, the total number of patients involved, and the calculated KPI results. It looks like:

```python
@dataclass
class KPICalculationsObject:
    calculation_datetime: datetime
    audit_start_date: date
    audit_end_date: date
    total_patients_count: int
    calculated_kpi_values: Dict[
        str,
        KPIResult,
    ]
```

Actual calculation results can be retrieved using the `calculated_kpi_values` key.

This is a dictionary where the key is the KPI name and the value is a `KPIResult` object. This object contains the calculated KPI value and the patient querysets used during the calculation (if `return_pt_querysets` was set to `True` during `CalculateKPIS` initialisation).

The KPI name for keys comes from [`kpi_name_registry`](#kpi_name_registry) (described later). The values are `KPIResult` objects that look like:

```python
@dataclass
class KPIResult:
    """
    Example would be:

    `return_patient_querysets` == False
    {
        'total_eligible': 100,
        'total_ineligible': 50,
        'total_passed': 75,
        'total_failed': 25,
        'patient_querysets': None
    }

    `return_patient_querysets` == True
    {
        'total_eligible': 100,
        'total_ineligible': 50,
        'total_passed': 75,
        'total_failed': 25,
        'patient_querysets': {
            'eligible': <QuerySet[Patient]>,
            'ineligible': <QuerySet[Patient]>,
            'passed': <QuerySet[Patient]>,
            'failed': <QuerySet[Patient]>,
        }
    }
    """

    total_eligible: int
    total_ineligible: int
    total_passed: Union[int | None]  # E.g. KPIs 1-12 would be None as counts
    total_failed: Union[int | None]  # E.g. KPIs 1-12 would be None as counts
    kpi_label: str = "KPI Name not found"
    patient_querysets: Union[Dict[str, QuerySet[Patient]], None] = None
```

### Example usage

```python
class PatientVisitsListView(
    ...
):
    ...

    def get_context_data(self, **kwargs):
        patient_id = self.kwargs.get("patient_id")
        context = super(PatientVisitsListView, self).get_context_data(**kwargs)
        patient = Patient.objects.get(pk=patient_id)

        ...

        calculate_kpis = CalculateKPIS(
            calculation_date=datetime.date.today(), return_pt_querysets=False
        )

        # Calculate the KPIs for this patient, returning only subset relevant
        # for a single patient's calculation
        kpi_calculations_object = calculate_kpis.calculate_kpis_for_single_patient(patient)

        context["kpi_results"] = kpi_calculations_object

        return context
```

## `kpi_name_registry`

The `CalculateKPIS` object has a `.kpi_name_registry` attribute that can be used to access both attribute names and rendered label names for each KPI.

The benefit of using this registry is that it allows for a single source of truth for KPI names, which can be used throughout the application. This is particularly useful when needing to access KPI names in multiple places, such as in the frontend and backend.

It exposes the following methods:

- `get_kpi(self, number: int) -> KPINames` which returns a `KPINames` object for the given KPI number:

```python
@dataclass
class KPINames:
    attribute_name: str  # e.g. kpi_32_1_health_check_completion_rate
    rendered_label: str  # e.g. Care Processes Completion Rate
```

- `get_attribute_name(self, number: int) -> str` which returns the attribute name for the given KPI number


- `get_rendered_label(self, number: int) -> str` which returns the rendered label name for the given KPI number

### Example usage

```python
@pytest.mark.django_db
def test_ensure_calculate_kpis_for_patient_returns_correct_kpi_subset(AUDIT_START_DATE):
    """Tests that the `calculate_kpis_for_single_patient()` method
    returns the correct subset of KPIs for a single patient.
    """
    kpi_calculator = CalculateKPIS(calculation_date=AUDIT_START_DATE)

    kpi_calc_obj = kpi_calculator.calculate_kpis_for_single_patient(
        PatientFactory(),
    )

    kpi_results_obj = kpi_calc_obj["calculated_kpi_values"].keys()

    # Check that the KPIs are a subset of the full KPI list
    EXPECTED_KPIS_SUBSET = list(range(13, 32)) + [321, 322, 323] + (list(range(33, 50)))
    EXPECTED_KPI_KEYS = [
        kpi_calculator.kpi_name_registry.get_attribute_name(i)
        for i in EXPECTED_KPIS_SUBSET
    ]

    for expected_kpi_key in EXPECTED_KPI_KEYS:
        assert (
            expected_kpi_key in kpi_results_obj
        ), f"Expected KPI {expected_kpi_key} in single patient subset, but not present in results"
```
