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
        
        case "not specified" | "3":
            return 3
        
        case "unknown" | "99":
            return 99
        
        case _:
            # Return Not Known. The patient won't save in the database without a numeric value.
            return 0


def csv_clean(df):
    if not is_numeric_dtype(df["Stated gender"]):
        df["Stated gender"] = df["Stated gender"].apply(clean_csv_sex)
    
    # Strip whitespace only fields of whitespaces and replace with None
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip().replace('', None)

    return df
