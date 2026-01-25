def csv_year(csv) -> int:
    """
    Extract the year of the earliest visit date from the CSV data to define the dataset year to use.
    Args:
        csv: The CSV data as a pandas DataFrame.

    Returns:
        int: 2021 or 2026 depending on the earliest visit date found.
    """
    import pandas as pd

    # Define the cutoff date for the two dataset years
    cutoff_date = pd.Timestamp("2024-04-01")

    # Ensure the 'visit_date' column is in datetime format
    csv["visit_date"] = pd.to_datetime(csv["visit_date"], errors="coerce")

    # Find the earliest visit date in the CSV
    earliest_visit_date = csv["visit_date"].min()

    # Determine the dataset year based on the earliest visit date
    if pd.isna(earliest_visit_date) or earliest_visit_date < cutoff_date:
        return 2021
    else:
        return 2026
