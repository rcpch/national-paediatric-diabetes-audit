from pandas.api.types import is_numeric_dtype

"""
CSV specific cleaning and value conversion.
Validation errors should be added in the patient and visit form, not here.
"""

def clean_csv_sex(value):
    match value.lower():
        case "m" | "1":
            return 1
        
        case "f" | "2":
            return 2
        
        case "not specified" | "9":
            return 9
        
        case _:
            # Return Not Known. The patient won't save in the database without a numeric value.
            return 0


def csv_clean(df):
    if not is_numeric_dtype(df["Stated gender"]):
        df["Stated gender"] = df["Stated gender"].apply(clean_csv_sex)
    
    print(df["Stated gender"].dtype)

    return df
