TREATMENT_TYPES = [
    (1, "One - three injections/day"),
    (2, "Four or more injections/day"),
    (3, "Insulin pump"),
    (4, "One - three injections/day plus other blood glucose lowering medication"),
    (5, "Four or more injections/day plus other blood glucose lowering medication"),
    (6, "Insulin pump therapy plus other blood glucose lowering medication"),
    (7, "Dietary management alone (no insulin or other diabetes related medication)"),
    (
        8,
        "Dietary management plus other blood glucose lowering medication (non Type-1 diabetes)",
    ),
    (99, "Unknown"),
]

INSULIN_TREATMENT = [
    (1, "No insulin"),
    (2, "One - three injections/day"),
    (3, "Four or more injections/day"),
    (4, "Insulin pump (standalone)"),
    (5, "Hybrid closed loop"),
    (99, "Unknown"),
]

NON_INSULIN_TREATMENT = [
    (1, "No medication"),
    (2, "Metformin only"),
    (3, "GLP-1 agonists"),
    (4, "SGLT2 inhibitors"),
    (5, "Other"),
    (99, "Unknown"),
]
