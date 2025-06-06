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

def clean_csv_measurement(value):
    """
    Convert measurement values to float, handling empty strings and non-numeric values.
    Remove extraneous non-numeric characters if necessary.
    Returns None for empty strings or non-numeric values.
    If the value is a valid number, it will be converted to float.
    If the value is an empty string, it will return None.
    If the value cannot be converted to float, it will return None.
    """
    if value == "":
        return None
    if isinstance(value, str):
        # Remove any non-numeric characters except for decimal points
        value = ''.join(char for char in value if char.isdigit() or char == '.')
    
    try:
        return float(value)
    except ValueError:
        return None


def csv_clean(df):
    if not is_numeric_dtype(df["Stated gender"]):
        df["Stated gender"] = df["Stated gender"].apply(clean_csv_sex)
    
    # strip whitespace and convert height and weight to numeric, removing any non-numeric characters (eg, "cm", "kg")
    if not is_numeric_dtype(df["Patient Height (cm)"]):
        df["Patient Height (cm)"] = df["Patient Height (cm)"].apply(clean_csv_measurement)
    if not is_numeric_dtype(df["Patient Weight (kg)"]):
        df["Patient Weight (kg)"] = df["Patient Weight (kg)"].apply(clean_csv_measurement)
    
    # Strip whitespace only fields of whitespaces and replace with None
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip().replace('', None)
    


    return df
