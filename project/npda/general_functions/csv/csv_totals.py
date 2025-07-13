def gather_unique_patient_and_visit_counts(dataframe, is_jersey=False):
        """
        Accepts a dataframe of the CSV data which has been cleaned and processed.
        The is_jersey flag indicates whether the PZ code is for Jersey, which has a different patient identifier field.
        Returns the number of unique patients and visits per patient in the dataframe
        This is a counting step for the progress bar in the upload_in_progress.html template
        """
        if is_jersey:
            unique_patients = dataframe["Unique Reference Number"].nunique()
            # Group by Unique Reference Number and count the number of non-null Visit/Appointment Dates
            unique_patient_visits = dataframe.groupby("Unique Reference Number")["Visit/Appointment Date"].apply(lambda x: x.notnull().sum()).to_dict()
        else:
            unique_patients = dataframe["NHS Number"].nunique()
            # Group by NHS Number and count the number of non-null Visit/Appointment Dates
            unique_patient_visits = dataframe.groupby("NHS Number")["Visit/Appointment Date"].apply(lambda x: x.notnull().sum()).to_dict()

         # Convert keys to strings to ensure JSON serialization works properly
        unique_patient_visits = {str(key): int(value) for key, value in unique_patient_visits.items()}


        total_rows = dataframe.shape[0]

        return unique_patients, unique_patient_visits, total_rows