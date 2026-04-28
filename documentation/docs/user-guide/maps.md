---
title: Maps and Deprivation
reviewers: Dr Simon Chapman
---

## The Dashboard Map

The NPDA dashboard includes an interactive map showing the geographic distribution of patients registered with your paediatric diabetes unit (PDU). Each dot represents a patient whose postcode has been successfully validated, and hovering over a dot displays:

- A patient identifier (NHS number or Unique Reference Number)
- The straight-line distance from the patient's home postcode to the PDU lead centre (in miles and kilometres)
- The patient's **Index of Multiple Deprivation (IMD) quintile**, if known

A summary footer shows the mean, minimum and maximum travel distances across all mapped patients.

---

## What is the Index of Multiple Deprivation?

The Index of Multiple Deprivation (IMD) is the official measure of relative deprivation used across the UK. It summarises social and economic conditions in small geographic areas, and is published separately for each of the four devolved nations.

### How it is calculated

The UK is divided into small statistical units of roughly comparable population size:

- **England and Wales** — Lower Layer Super Output Areas (LSOAs), each containing approximately 400–3,000 households
- **Scotland** — Data Zones
- **Northern Ireland** — Super Output Areas (SOAs)

Each unit is scored across several **deprivation domains**. The domains differ slightly between nations:

| Domain | England | Wales | Scotland | Northern Ireland |
|---|---|---|---|---|
| Income | ✓ | ✓ | ✓ | ✓ |
| Employment | ✓ | ✓ | ✓ | ✓ |
| Education | ✓ | ✓ | ✓ | ✓ |
| Health | ✓ | ✓ | ✓ | ✓ |
| Crime | ✓ | ✓ | ✓ | ✓ |
| Barriers to housing / services | ✓ | ✓ | ✓ | ✓ |
| Living environment | ✓ | ✓ | — | — |
| Access to services | — | ✓ | ✓ | ✓ |
| Community safety | — | ✓ | — | — |
| Physical environment | — | ✓ | — | — |

The domain scores are weighted and combined into a single IMD score for each area. Areas are then **ranked** from most to least deprived and divided into quantiles — commonly deciles (10 groups) or quintiles (5 groups). **Quintile 1 is the most deprived; quintile 5 is the least deprived.**

!!! warning "IMD scores are not comparable across countries"
    Because each nation calculates its index independently, a quintile 2 in England is not the same as a quintile 2 in Wales or Scotland. Comparisons should only be made within a single nation.

---

## Datasets and Boundaries

The IMD datasets used vary by country and publication year. The table below summarises the datasets held in the RCPCH Census Platform that power deprivation lookups in this platform:

| Country | Index | IMD Year | Area unit | Boundary era | Local Authority era |
|---|---|---|---|---|---|
| England | IoD | 2019 | LSOA | 2011 | 2019 |
| England | IoD | 2025 | LSOA | 2021 | 2024 |
| Wales | WIMD | 2019 | LSOA | 2011 | 2019 |
| Scotland | SIMD | 2020 | Data Zone | 2011 | 2011 |
| Northern Ireland | NIMDM | 2017 | SOA | 2001 | — |

---

## How NPDA Uses IMD

The NPDA platform looks up the IMD quintile for each patient whose postcode has been successfully validated. The lookup is **country-aware**: a patient in Wales is looked up against the Welsh IMD (WIMD), a patient in Scotland against the Scottish IMD (SIMD), and so on.

For **England**, the dataset year used depends on the audit period:

| Audit period | England IMD dataset |
|---|---|
| 2024–2025 and earlier | IoD 2019 (2011 LSOA boundaries) |
| 2025–2026 and later | IoD 2025 (2021 LSOA boundaries) |

This ensures that the most appropriate and up-to-date deprivation data is used as new datasets are published.

The quintile is stored against each patient record and displayed on:

- The **dashboard map** tooltip for each patient
- The **patient report**, where it can be used to explore the relationship between deprivation and clinical outcomes

Lookups are performed at the point of postcode validation during CSV upload, and can be recalculated in bulk by a system administrator using the `recalculate_imd` management command.

---

## Further Reading

- [RCPCH Census Platform](https://github.com/rcpch/rcpch-census-platform) — the open-source service providing deprivation lookups for RCPCH products
- [English Indices of Deprivation 2019](https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019) — Ministry of Housing, Communities & Local Government
- [English Indices of Deprivation 2025](https://www.gov.uk/government/statistics/english-indices-of-deprivation-2025) — Ministry of Housing, Communities & Local Government
- [Welsh Index of Multiple Deprivation 2019](https://www.gov.wales/welsh-index-multiple-deprivation) — Welsh Government
- [Scottish Index of Multiple Deprivation 2020](https://www.gov.scot/collections/scottish-index-of-multiple-deprivation-2020/) — Scottish Government
- [Northern Ireland Multiple Deprivation Measure 2017](https://www.nisra.gov.uk/statistics/deprivation/northern-ireland-multiple-deprivation-measure-2017-nimdm2017) — NISRA
