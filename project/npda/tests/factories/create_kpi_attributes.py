class CreateKPIAttributes:
    """Helper Class to feed in valid KPI PASS/FAIL/INELIGIBLE metrics to the PatienFactory.

    Returns a dictionary of keyword arguments which can be passed into the PatientFactory constructor to produce a completed audit according to provided values.

    First split based on age:


    # KPIs for Patients Aged 12 and Above
    
    These KPIs focus on patients aged 12 and above, generally involving more specific care processes or additional screenings:

    KPI 4: Number of patients aged 12+ with Type 1 diabetes
    KPI 6: Number of patients with Type 1 diabetes aged 12+ with a complete year of care in the audit period
    KPI 28: Blood Pressure (%)
    KPI 29: Urinary Albumin (%)
    KPI 30: Retinal Screening (%)
    KPI 31: Foot Examination (%)
    KPI 35: Smoking status screened (%)
    KPI 36: Referral to smoking cessation service (%)
    


    # KPIs for Patients Below 25 Years

    KPI 1: Total number of eligible patients
    KPI 2: Total number of new diagnoses within the audit period
    KPI 3: Total number of eligible patients with Type 1 diabetes
    KPI 5: Number of patients with Type 1 diabetes with a complete year of care in the audit period
    KPI 7: Number of patients with Type 1 diabetes who were diagnosed within the audit period
    
    
    
    # Other KPIs without Specific Age Eligibility

    KPI 8: Number of patients who died within the audit period
    KPI 9: Number of patients who transitioned/left service within the audit period
    KPI 10: Number of patients with coeliac disease
    KPI 11: Number of patients with thyroid disease
    KPI 12: Number of patients using (or trained to use) blood ketone testing equipment
    KPI 13: One - three injections/day
    KPI 14: Four or more injections/day
    KPI 15: Insulin pump (including those using a pump as part of a hybrid closed loop)
    KPI 16: One - three injections/day plus other blood glucose lowering medication
    KPI 17: Four or more injections/day plus other blood glucose lowering medication
    KPI 18: Insulin pump therapy plus other blood glucose lowering medication
    KPI 19: Dietary management alone (no insulin or other diabetes-related medication)
    KPI 20: Dietary management plus other blood glucose lowering medication (non-Type-1 diabetes)
    KPI 21: Number of patients using a flash glucose monitor
    KPI 22: Number of patients using a real-time continuous glucose monitor (CGM) with alarms
    KPI 23: Number of patients with Type 1 diabetes using a real-time continuous glucose monitor (CGM) with alarms
    KPI 24: Hybrid closed-loop system (HCL)
    KPI 25: HbA1c (%)
    KPI 26: BMI (%)
    KPI 27: Thyroid Screen (%)
    KPI 32: Health check completion rate (%)
    KPI 33: HbA1c 4+ (%)
    KPI 34: Psychological assessment (%)
    KPI 37: Additional dietetic appointment offered (%)
    KPI 38: Patients attending additional dietetic appointment (%)
    KPI 39: Influenza immunisation recommended (%)
    KPI 40: Sick day rules advice (%)
    KPI 41: Coeliac disease screening (%)
    KPI 42: Thyroid disease screening (%)
    KPI 43: Carbohydrate counting education (%)
    KPI 44: Mean HbA1c
    KPI 45: Median HbA1c
    KPI 46: Number of admissions
    KPI 47: Number of DKA admissions
    KPI 48: Required additional psychological support
    KPI 49: Albuminuria present
    """

    def __init__(self) -> None:
        pass
