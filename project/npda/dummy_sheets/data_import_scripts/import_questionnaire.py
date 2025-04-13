"""Script to import questionnaire data from a CSV file."""

import pandas as pd

from project.constants import (
    UNIQUE_IDENTIFIER_ENGLAND,
    UNIQUE_IDENTIFIER_JERSEY,
    CSV_HEADING_OBJECTS,
)


class QuestionnaireImporter:
    def __init__(self, csv_file_path: str, is_jersey: bool = False):
        self.csv_file_path = csv_file_path
        self.is_jersey = is_jersey

        self._import_questionnaire()

    def _import_questionnaire(self):
        """Import questionnaire data from a CSV file."""
        # Gather headers (fields for main CSV excluding Visit fields)
        if self.is_jersey:
            headers = [
                UNIQUE_IDENTIFIER_JERSEY["heading"],
            ]
        else:
            headers = [
                UNIQUE_IDENTIFIER_ENGLAND["heading"],
            ]

        for heading in CSV_HEADING_OBJECTS:
            if heading["model"] == "Patient":
                headers.append(heading["heading"])

        df = pd.read_csv(self.csv_file_path)

        # Check that all headers are present
        try:
            self._validate_headers(df, headers)
        except ValueError as e:
            raise ValueError(f"Column not found in CSV file: {e}")

    def _validate_headers(self, df: pd.DataFrame, headers: list[str]):
        """Validate that all headers are present in the CSV file."""
        for col in headers:
            if col not in df.columns:
                raise ValueError(f"Column {col} not found in CSV file.")
        if len(df.columns) != len(headers):
            raise ValueError(
                "Number of columns in CSV file does not match number of headers."
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Import questionnaire data from a CSV file."
    )
    parser.add_argument(
        "csv_file", type=str, help="The path to the CSV file to import."
    )
    parser.add_argument(
        "--is_jersey", type=bool, help="Whether the CSV file is for Jersey."
    )
    args = parser.parse_args()

    # Run the importer
    QuestionnaireImporter(args.csv_file, args.is_jersey)
