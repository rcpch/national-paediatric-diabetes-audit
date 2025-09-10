"""TODO:
    - [ ] Move constants to a separate file. Currently importing from `seed_submission.py`.
    - [ ] Generalise the parsing of inputs and share between this and `seed_submission.py`.

Generate a CSV using data generator.

Default behavior of data generator is creating VALID visits - CSV.

Example use:

    python manage.py create_csv \
        --pts=5 \
        --visits="CDCD DHPC ACDC CDCD" \
        --hb_target=T \
        --age_range=11_15 \
        --pz_code="PZ999" \
        --imd=2 \
        --build
    
    # Jersey

    python manage.py create_csv \
        --pts=5 \
        --visits="CDCD DHPC ACDC CDCD" \
        --hb_target=T \
        --age_range=11_15 \
        --pz_code="PZ248" \
        --build

    Will generate 1 csv file with 5 patients, each with 12 visits, with the visit encoding provided.
    The HbA1c target range for each visit will be set to 'TARGET'.
    The resulting csv will have 5 * 12 = 60 rows (one for each visit).

    ## Building multiple larger csv files

    This can be used to create a spread of data with different ages, visits, hb_targets etc.

    Using the `--build` flag will generate a `build` csv file, the same as above, but with
    a `build_` filename prefix. The `--coalesce` flag can be used to combine all the build files
    into a single csv file.

    python manage.py create_csv \
        --pts=15 \
        --visits="CDCD DHPC ACDC CDCD" \
        --hb_target=T \
        --age_range=11_15 \
        --imd=1 \
        --build \
    && python manage.py create_csv \
        --pts=15 \
        --visits="CDCCD DDCC CACC" \
        --hb_target=A \
        --age_range=16_19 \
        --imd=2 \
        --build \
    && python manage.py create_csv \
        --pts=15 \
        --visits="CDC ACDC CDCD" \
        --hb_target=T \
        --age_range=0_4 \
        --imd=3 \
        --build \
    && python manage.py create_csv \
        --pts=15 \
        --visits="CDC ACDC CDCD" \
        --hb_target=T \
        --age_range=0_4 \
        --imd=4 \
        --build \
    && python manage.py create_csv \
        --pts=15 \
        --visits="CDC ACDC CDCD" \
        --hb_target=T \
        --age_range=0_4 \
        --imd=5 \
        --build \
    && python manage.py create_csv \
       --coalesce

Implementation notes:

    We can use the `FakePatientCreator`'s `.build()` methods to generate Python object stubs of Patients and Visits. We then use pandas to concatenate these values into the csv.

    Factory `.build()` will not create related objects (but is significantly quicker). At the end,
    need to additionally add the `Transfer` column values manually.
"""

import logging
import os
import random
from collections import defaultdict
from datetime import datetime

import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from project.constants.csv_headings import (
    ALL_DATES,
    CSV_DATA_TYPES_MINUS_DATES,
    CSV_HEADING_OBJECTS,
    ENGLAND_CSV_DATA_TYPES,
    JERSEY_CSV_DATA_TYPES,
    UNIQUE_IDENTIFIER_ENGLAND,
    UNIQUE_IDENTIFIER_JERSEY,
)
from project.constants.diabetes_types import DIABETES_TYPES
from project.npda.general_functions.audit_period import get_audit_period_for_date
from project.npda.general_functions.data_generator_extended import (
    AgeRange,
    FakePatientCreator,
    HbA1cTargetRange,
)
from project.npda.management.commands.seed_submission import (
    CYAN,
    GREEN,
    RESET,
    age_range_map,
    hb_target_map,
    letter_name_map,
)

# Logging
logger = logging.getLogger(__name__)

GP_ODS_CODES = [
    "A81001",
    "A81002",
    "A81004",
    "A81005",
    "A81006",
    "A81007",
    "A81009",
    "A81011",
    "A81012",
    "A81013",
    "A81014",
    "A81016",
    "A81017",
    "A81018",
    "A81019",
    "A81020",
    "A81021",
    "A81022",
    "A81023",
    "A81025",
]

# IMD -> example postcode
IMD_POSTCODE_MAP = {
    5: "AL5 2SL",
    4: "SW1A1AA",
    3: "DA8 1QJ",
    2: "GU21 5JG",
    1: "B18 6PU",
}

POSTCODES = []


class Command(BaseCommand):
    help = "Creates a csv file that can be uploaded to the NPDA platform."

    def print_success(self, message: str):
        self.stdout.write(self.style.SUCCESS(message))

    def print_info(self, message: str):
        self.stdout.write(self.style.WARNING(message))

    def print_error(self, message: str):
        self.stdout.write(self.style.ERROR(f"ERROR: {message}"))

    def add_arguments(self, parser):
        # Primary parser for standard arguments
        parser.add_argument(
            "--pts",
            type=int,
            help="Number of patients to seed.",
        )
        parser.add_argument(
            "--visits",
            type=str,
            help="Visit types (e.g., 'CDCD DHPC ACDC CDCD'). Can have whitespaces, these will be ignored.",
        )
        parser.add_argument(
            "--hb_target",
            type=str,
            choices=["T", "A", "W"],
            help="HBA1C Target range for visit seeding.",
        )
        parser.add_argument(
            "--diabetes_types",
            type=str,
            help="Diabetes types to use for seeding (can be multiple e.g., 'T1 T2'). Defaults to T1. (CFRD, MODY, OTHER, UNKNOWN not yet supported)",
        )
        parser.add_argument(
            "--pz_code",
            type=str,
            default="PZ999",
            help="PZ Code of the Paediatric Diabetes Unit.",
        )
        parser.add_argument(
            "--submission_date",
            type=str,
            help="Submission date in YYYY-MM-DD format (optional, defaults to today).",
        )
        parser.add_argument(
            "--output_path",
            type=str,
            help="Path to save the csv",
            default="project/npda/dummy_sheets/local_generated_data",
        )
        parser.add_argument(
            "--age_range",
            type=str,
            default="11_15",
            choices=["0_4", "5_10", "11_15", "16_19", "20_25"],
            help="Age range for patients to be seeded.",
        )

        # Mutually exclusive group for --build and --coalesce
        mutex_group = parser.add_mutually_exclusive_group(required=True)
        mutex_group.add_argument(
            "--build",
            action="store_true",
            help="Outputs a build csv file.",
        )
        mutex_group.add_argument(
            "--coalesce",
            action="store_true",
            help="Coalesces build csv files.",
        )

        mutex_group = parser.add_mutually_exclusive_group()
        mutex_group.add_argument(
            "--imd",
            type=int,
            help="Requested IMD value used to assign a postcode.",
            choices=[1, 2, 3, 4, 5],
        )
        mutex_group.add_argument(
            "--postcode_outcode",
            type=str,
            help="Use random postcodes with the given outcode (eg W1A for W1A 1AA)"
        )



    def handle(self, *args, **options):

        # If --coalesce is provided, ignore other options
        if options["coalesce"]:
            # Only coalesce, ignoring all other arguments
            self._run_coalesce(**options)
            return

        if options["build"]:
            required_args = ["pts", "visits", "hb_target"]
        for arg in required_args:
            if options.get(arg) is None:
                raise CommandError(f"--{arg} is required when using --build")

        if not (parsed_values := self._parse_values_from_options(**options)):
            return

        audit_start_date = parsed_values["audit_start_date"]
        audit_end_date = parsed_values["audit_end_date"]
        n_pts_to_seed = parsed_values["n_pts_to_seed"]
        hba1c_target = parsed_values["hba1c_target"]
        diabetes_types = parsed_values["diabetes_types"]
        visits = parsed_values["visits"]
        visit_types = parsed_values["visit_types"]
        submission_date = parsed_values["submission_date"]
        age_range = parsed_values["age_range"]
        imd = parsed_values["imd"]
        postcode = parsed_values["postcode"]
        postcode_outcode = parsed_values["postcode_outcode"]
        pdu = parsed_values["pz_code"]
        output_path = parsed_values["output_path"]
        build_flag = parsed_values["build_flag"]

        # PRINT INFORMATION
        # Header
        self.print_info(f"{CYAN}--- Build Information ---{RESET}\n")

        # Build information table
        build_info = [
            ["Build Mode", "ON" if build_flag else "OFF"],
            ["Submission Date", submission_date],
            ["Audit Start Date", audit_start_date],
            ["Audit End Date", audit_end_date],
        ]
        for item in build_info:
            self.print_info(f"{CYAN}{item[0]:<30}{RESET} {item[1]}")

        diabetes_type_strs = []
        for dt in diabetes_types:
            for code, description in DIABETES_TYPES:
                if dt == code:
                    diabetes_type_strs.append(description)
                    break

        # Seeding information table
        seeding_info = [
            ["Number of Patients to Seed", n_pts_to_seed],
            ["Number of Visits per Patient", len(visit_types)],
            ["Total Rows in Resulting CSV", n_pts_to_seed * len(visit_types)],
            ["HbA1c Target Range", hba1c_target.name],
            ["Diabetes Types", ", ".join(diabetes_type_strs)],
            ["Age Range", f"{age_range.name}"],
            ["IMD Value", imd],
            ["Postcode Outcode" if postcode_outcode else "Postcode", postcode or postcode_outcode],
            ["PZ Code", pdu],
        ]

        self.print_info("-" * 45)
        for item in seeding_info:
            self.print_info(f"{CYAN}{item[0]:<30}{RESET} {item[1]}")
        # Visit types table

        self.print_info("\n--- Visit Types Provided ---\n")

        # Divide the list into chunks of 4 for a compact table
        visit_types_chunks = [visit_types[i : i + 4] for i in range(0, len(visit_types), 4)]
        for chunk in visit_types_chunks:
            self.print_info("    ".join(f"{CYAN}{visit}{RESET}" for visit in chunk))

        self.generate_csv(
            audit_start_date,
            audit_end_date,
            n_pts_to_seed,
            age_range,
            hba1c_target,
            diabetes_types,
            pdu,
            visits,
            visit_types,
            output_path,
            build_flag,
            postcode,
            postcode_outcode
        )
        self.print_success(f"✨ CSV generated successfully at {self.csv_name}.\n")
        if build_flag:
            self.print_info("Coalesce the build csv files using the --coalesce flag.")

    def generate_csv(
        self,
        audit_start_date,
        audit_end_date,
        n_pts_to_seed,
        age_range,
        hba1c_target,
        diabetes_types,
        pdu,
        visits,
        visit_types,
        output_path,
        build_flag,
        postcode,
        postcode_outcode
    ):

        # Start csv logic

        fake_patient_creator = FakePatientCreator(
            audit_start_date=audit_start_date,
            audit_end_date=audit_end_date,
            # either postcode or postcode_outcode
            postcode=postcode,
            postcode_outcode=postcode_outcode
        )

        new_pts = fake_patient_creator.build_fake_patients(
            n=n_pts_to_seed,
            age_range=age_range,
            latest_diagnosis_date=audit_end_date,
            diabetes_types=diabetes_types
        )

        # For each pt, add visits
        new_visits = fake_patient_creator.build_fake_visits(
            patients=new_pts,
            age_range=age_range,
            hb1ac_target_range=hba1c_target,
            visit_types=visit_types
        )

        # `CSV_HEADINGS` is a tuple for csv headings and model fields
        # Create a map = {
        #   model : {
        #     model_field : csv_heading
        #   }
        # }
        if pdu == "PZ248":
            is_jersey = True
        else:
            is_jersey = False

        csv_map = self._get_map_model_csv_heading_field(is_jersey=is_jersey)

        # Initialise data list, where each item is a dict relating to a row in the csv
        # Each dict will have keys as csv headings and values as the data
        data = []

        # We're using the build method so Patients and Visits are separate objects
        # Need to manually iterate and join the data
        N_VISIT_TYPES = len(visit_types)
        for ix, pt in enumerate(new_pts):
            gp_ods_code = random.choice(GP_ODS_CODES)
            visit_start_idx = ix * N_VISIT_TYPES
            visit_end_idx = visit_start_idx + N_VISIT_TYPES
            for visit in new_visits[visit_start_idx:visit_end_idx]:
                visit_dict = {}

                for model, field_heading_mappings in csv_map.items():

                    for (
                        model_field,
                        csv_heading,
                    ) in field_heading_mappings.items():
                        if model == "Visit":
                            visit_dict[csv_heading] = getattr(visit, model_field)
                        elif model == "Patient":
                            # Foreign key so need to manually set the value
                            if model_field == "pdu":
                                visit_dict[csv_heading] = pdu
                                continue
                            if model_field == "gp_ods_code":
                                visit_dict[csv_heading] = gp_ods_code
                                continue

                            visit_dict[csv_heading] = getattr(pt, model_field)

                        # date of leaving service
                        # & reason for leaving service. Ignore for now
                        elif model == "Transfer":
                            visit_dict[csv_heading] = None

                data.append(visit_dict)

        is_jersey = True if pdu == "PZ248" else False

        df = self._set_valid_dtypes(pd.DataFrame(data), is_jersey)

        self.csv_name = self._get_file_name(
            n_pts_to_seed=n_pts_to_seed,
            visits=visits,
            build=build_flag,
            output_path=output_path,
            age_range=age_range,
            hb_target=hba1c_target,
            pz_code=pdu,
        )
        df.to_csv(
            self.csv_name,
            index=False,
        )

    def _run_coalesce(self, **options):
        self.print_info("Coalescing build csv files...")

        pdu = options["pz_code"]
        is_jersey = True if pdu == "PZ248" else False

        # Get the existing build files
        existing_build_files = [
            f for f in os.listdir(options["output_path"]) if f.startswith("build")
        ]
        if not existing_build_files:
            self.print_error(f"No build files to coalesce in {options['output_path']}/")
            return
        self.print_info(f"{CYAN}Existing build files: {RESET}\n")
        for file in existing_build_files:
            self.print_info(f"\t{file}")
        # Coalesce the build files

        # First read all the files into a list of dataframes
        dfs = []
        for file in existing_build_files:
            dfs.append(pd.read_csv(os.path.join(options["output_path"], file)))

        # Make sure the columns are the same
        seen_cols = set(dfs[0].columns)
        for i, df in enumerate(dfs[1:], 1):
            if set(df.columns) != seen_cols:
                self.print_error(
                    f"Column mismatch in {existing_build_files[i]} compared to {existing_build_files[0]}"
                )

        # Concatenate the dataframes
        df = pd.concat(dfs, axis=0, join="outer").reset_index(drop=True)
        df = self._set_valid_dtypes(
            df,
            is_jersey=is_jersey,
        )

        df.info()

        csv_file_name = f"coalesced_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        full_csv_path = os.path.join(options["output_path"], csv_file_name)
        df.to_csv(
            full_csv_path,
            index=False,
        )

        self.print_success(f"\n✨ CSV coalesced successfully at {full_csv_path}.\n")

        # PRINT OUT DIFFERENCE IN DATA TYPES
        comparison_csv = "dummy_sheet_invalid.csv"
        orig = pd.read_csv(f"project/npda/dummy_sheets/{comparison_csv}")
        # Get data types for both DataFrames
        orig_dtypes = orig.dtypes
        new_dtypes = df.dtypes
        # Identify columns with differing data types
        mismatched_dtypes = {}
        for col in orig_dtypes.index:
            if col in new_dtypes.index and orig_dtypes[col] != new_dtypes[col]:
                mismatched_dtypes[col] = (orig_dtypes[col], new_dtypes[col])

        # Print out mismatched columns and their respective data types
        self.print_error(f"Columns with differing data types from {comparison_csv}:")
        self.print_info("NOTE: columns with Nan are cast to float")
        for col, (orig_type, new_type) in mismatched_dtypes.items():
            print(
                f"{col}: original type = {GREEN}{orig_type}{RESET}, coalesced type = {CYAN}{new_type}{RESET}"
            )
            print(
                f"Value in original: {GREEN}{orig[col].iloc[0]}{RESET}, value in coalesced: {CYAN}{df[col].iloc[0]}{RESET}\n"
            )

        return

    def _set_valid_dtypes(self, df: pd.DataFrame, is_jersey=False) -> pd.DataFrame:
        """Sets the correct data types for the dataframe, making them same as original
        dummy_sheet_invalid.csv file (to ensure we handle errors).
        """
        if is_jersey:
            CSV_DATA_TYPES_MINUS_DATES.update(JERSEY_CSV_DATA_TYPES)
            TEMPLATE_HEADERS = pd.read_csv(
                "project/npda/dummy_sheets/npda_csv_submission_template_for_use_from_april_2025.csv"
            ).columns
        else:
            CSV_DATA_TYPES_MINUS_DATES.update(ENGLAND_CSV_DATA_TYPES)
            TEMPLATE_HEADERS = pd.read_csv(
                "project/npda/dummy_sheets/npda_csv_submission_template_for_use_from_april_2021.csv"
            ).columns

        for header in df.columns:
            if header in ALL_DATES:
                continue
            print(
                f"Column: {header}, dtype: {df[header].dtype}, unique values: {df[header].unique()}"
            )
            print(f"Original dtype: {CSV_DATA_TYPES_MINUS_DATES[header]}")

        # Set dtypes for non-date columns
        df = self.clean_and_cast(df, CSV_DATA_TYPES_MINUS_DATES)

        df = (
            df.assign(
                # Convert each date column in ALL_DATES to the desired format, preserving null values as NaT
                **{
                    date_header: lambda x, date_header=date_header: pd.to_datetime(
                        x[date_header], format="%d/%m/%Y", errors="coerce"
                    )
                    for date_header in ALL_DATES
                },
            )
            # # Reorder columns
            # [TEMPLATE_HEADERS]
        )
        df = df[TEMPLATE_HEADERS]

        # Ensure the formatting is right for validation
        for date_header in ALL_DATES:
            df[date_header] = df[date_header].dt.strftime("%d/%m/%Y")

        return df

    def clean_and_cast(self, df, column_types):
        try:
            for column, dtype in column_types.items():
                if dtype.startswith("Int"):  # Handle nullable integers
                    df[column] = (
                        df[column]
                        .replace({np.nan: pd.NA, None: pd.NA})  # Replace missing values
                        .apply(
                            lambda x: (int(x) if pd.notna(x) and x == int(x) else pd.NA)
                        )  # Ensure valid integers
                        .astype(dtype)  # Cast to nullable Int dtype
                    )
                elif dtype == "string":  # Handle strings
                    df[column] = df[column].replace({np.nan: pd.NA, None: pd.NA}).astype("string")
                elif dtype.startswith("float"):  # Handle floats
                    df[column] = df[column].replace({None: np.nan}).astype(dtype)
                else:
                    raise ValueError(
                        f"Unsupported dtype from CSV_DATA_TYPES_MINUS_DATES: {dtype}\n (for {column=} {df[column].dtype=})"
                    )
        # Catch and throw error again to log the column and dtype
        # Cant continue
        except Exception as e:
            logger.error(f"ERROR in clean_and_cast: {e}")
            logger.error(f"CSV_DATA_TYPES_MINUS_DATES {column=} {dtype=}\n{df[column].dtype=}")
            raise e

        return df

    def _parse_values_from_options(self, **options):

        # Handle submission_date with default to today's date if not provided
        submission_date_str = options.get("submission_date")
        if submission_date_str:
            try:
                submission_date = timezone.make_aware(
                    datetime.strptime(submission_date_str, "%Y-%m-%d")
                ).date()
            except ValueError:
                self.print_error("Invalid submission_date format. Use YYYY-MM-DD.")
                return
        else:
            submission_date = timezone.now().date()

        audit_start_date, audit_end_date = get_audit_period_for_date(submission_date)

        # Number of patients to seed (pts)
        n_pts_to_seed = options["pts"]

        # Visit types
        visits: str = options["visits"]
        # Map to actual VisitType
        # NOTE: `_map_visit_type_letters_to_names` already did some basic validation
        visit_types = list(
            map(
                lambda letter: letter_name_map[letter],
                visits.replace(" ", ""),
            )
        )

        # hba1c target
        hba1c_target = hb_target_map[options["hb_target"]]

        if options.get("diabetes_types"):
            diabetes_type_strs = options["diabetes_types"].upper().split(" ")

            invalid_diabetes_type_strs = [dt for dt in diabetes_type_strs if dt not in {"T1", "T2"}]
            if invalid_diabetes_type_strs:
                self.print_error(
                    f"Invalid diabetes_types provided. Must be one of 'T1', 'T2'. Invalid values: {', '.join(invalid_diabetes_type_strs)}"
                )
                return
        
            diabetes_types = []

            if "T1" in diabetes_type_strs:
                diabetes_types.append(DIABETES_TYPES[0][0])
            
            if "T2" in diabetes_type_strs:
                diabetes_types.append(DIABETES_TYPES[1][0])
        else:
            diabetes_types = [DIABETES_TYPES[0][0]] # T1 default

        # age range
        age_range = age_range_map[options["age_range"]]

        imd = options["imd"]
        postcode_outcode = options["postcode_outcode"]

        if imd:
            postcode = IMD_POSTCODE_MAP.get(imd)

            if not postcode:
                self.print_error(f"Invalid IMD value: {imd}")
                return
        elif postcode_outcode:
            postcode = None
        else:
            imd = 1
            postcode = IMD_POSTCODE_MAP[1] 

        # pdu
        pz_code = options["pz_code"]

        # output path
        output_path = options["output_path"]

        # flags
        build_flag = options["build"]

        return {
            "n_pts_to_seed": n_pts_to_seed,
            "audit_start_date": audit_start_date,
            "audit_end_date": audit_end_date,
            "hba1c_target": hba1c_target,
            "diabetes_types": diabetes_types,
            "pz_code": pz_code,
            "visits": visits,
            "visit_types": visit_types,
            "submission_date": submission_date,
            "output_path": output_path,
            "age_range": age_range,
            "imd": imd,
            "postcode": postcode,
            "postcode_outcode": postcode_outcode,
            "build_flag": build_flag,
        }

    def _get_file_name(
        self,
        n_pts_to_seed: str,
        visits: str,
        output_path: str,
        age_range: AgeRange,
        hb_target: HbA1cTargetRange,
        pz_code: str,
        build: bool = False,
    ) -> str:

        building_str = ""
        if build:
            # First count the number of existing files to use this as filename prefix
            existing_files = [f for f in os.listdir(output_path) if f.startswith("build")]

            # Set the building string filename prefix
            building_str = f"build__{len(existing_files) + 1}_"

        output_path = os.path.join(
            output_path,
            f"{building_str}{datetime.now().strftime("%Y%m%d%H%M%S")}-npda-seed-data-{pz_code}-{n_pts_to_seed}pts-{age_range.name}-{hb_target.name}-{visits.replace(' ', '')}.csv",
        )
        return output_path

    def _map_visit_type_letters_to_names(self, vt_letters: str) -> str:
        rendered_vt_names: list[str] = []

        for letter in vt_letters:
            if letter == " ":
                rendered_vt_names.append("\n\t")
                continue
            if letter.upper() not in "CADPH":
                self.print_error("INVALID VISIT TYPE LETTER: " + letter)

            rendered_vt_names.append(f"\n\t{letter_name_map[letter]}")

        return "".join(rendered_vt_names)

    def _get_map_model_csv_heading_field(self, is_jersey) -> dict:
        """Generates dict that looks like:

        {
            'Patient': {
                'nhs_number': 'NHS Number',
                'date_of_birth': 'Date of Birth',
                ...
            },
            'Visit': {
                'visit_type': 'Visit Type',
                'visit_date': 'Visit/Appointment Date',
                ...
            },
            'Transfer': {
                'date_leaving_service': 'Date Leaving Service',
                ...
        }
        """

        map_model_csv_heading_field = defaultdict(dict)

        if is_jersey:
            CSV_HEADINGS = UNIQUE_IDENTIFIER_JERSEY + CSV_HEADING_OBJECTS
        else:
            CSV_HEADINGS = UNIQUE_IDENTIFIER_ENGLAND + CSV_HEADING_OBJECTS

        for item in CSV_HEADINGS:
            # pdu no longer has model defined
            if item.get("model_field") == "pdu":
                model = "Patient"
            else:
                model = item["model"]
            csv_heading = item["heading"]
            model_field = item["model_field"]
            map_model_csv_heading_field[model][model_field] = csv_heading

        return map_model_csv_heading_field
