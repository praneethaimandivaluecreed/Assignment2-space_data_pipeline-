import pandas as pd
from pathlib import Path

from logger import logger


# Configuration

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA_DIR = (
    PROJECT_ROOT / "data" / "processed"
)


# Read processed data

def read_processed_data(filename):

    file_path = (
        PROCESSED_DATA_DIR / filename
    )

    logger.info(
        f"Reading processed file: {file_path}"
    )

    if not file_path.exists():

        raise FileNotFoundError(
            f"Processed file not found: "
            f"{file_path}"
        )

    return pd.read_csv(file_path)


# Validate required columns

def validate_required_columns(
    df,
    required_columns,
    dataset_name
):

    logger.info(
        f"Validating columns: {dataset_name}"
    )

    # Check whether all required columns
    # are available in the dataframe

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        logger.error(
            f"{dataset_name} missing columns: "
            f"{missing_columns}"
        )

        return False

    logger.info(
        f"{dataset_name}: Required columns passed"
    )

    return True


# Validate duplicate IDs

def validate_unique_id(
    df,
    id_column,
    dataset_name
):

    logger.info(
        f"Checking duplicate IDs: {dataset_name}"
    )

    # IDs should be unique because they
    # identify each record separately

    duplicate_count = (
        df[id_column]
        .duplicated()
        .sum()
    )

    if duplicate_count > 0:

        logger.error(
            f"{dataset_name}: "
            f"{duplicate_count} duplicate "
            f"{id_column} values found"
        )

        return False

    logger.info(
        f"{dataset_name}: Duplicate ID check passed"
    )

    return True


# Validate required values

def validate_not_null(
    df,
    columns,
    dataset_name
):

    logger.info(
        f"Checking NULL values: {dataset_name}"
    )

    validation_passed = True

    # Check important columns one by one
    # because these columns should not be empty

    for column in columns:

        null_count = df[column].isna().sum()

        if null_count > 0:

            logger.error(
                f"{dataset_name}: "
                f"{column} contains "
                f"{null_count} NULL values"
            )

            validation_passed = False

        else:

            logger.info(
                f"{dataset_name}: "
                f"{column} NULL check passed"
            )

    return validation_passed


# Validate numeric range

def validate_range(
    df,
    column,
    minimum,
    maximum,
    dataset_name
):

    logger.info(
        f"Checking range: "
        f"{dataset_name}.{column}"
    )

    # Find values which are outside
    # the allowed minimum and maximum range

    invalid_count = (
        (df[column] < minimum)
        | (df[column] > maximum)
    ).sum()

    if invalid_count > 0:

        logger.error(
            f"{dataset_name}: "
            f"{invalid_count} invalid "
            f"{column} values found"
        )

        return False

    logger.info(
        f"{dataset_name}: "
        f"{column} range check passed"
    )

    return True


# Validate foreign key relationship

def validate_foreign_key(
    child_df,
    child_column,
    parent_df,
    parent_column,
    relationship_name
):

    logger.info(
        f"Checking relationship: "
        f"{relationship_name}"
    )

    # Get all valid IDs from the parent table

    valid_ids = set(
        parent_df[parent_column]
        .dropna()
    )

    # Check whether child IDs are available
    # in the parent table

    invalid_ids = (
        child_df[child_column]
        .dropna()
        .loc[
            lambda x: ~x.isin(valid_ids)
        ]
    )

    if len(invalid_ids) > 0:

        logger.error(
            f"{relationship_name}: "
            f"{len(invalid_ids)} unmatched "
            f"foreign key values found"
        )

        return False

    logger.info(
        f"{relationship_name}: "
        f"Foreign key check passed"
    )

    return True


# Validate agencies

def validate_agencies(df):

    logger.info("Validating agencies")

    passed = True

    # These columns are required
    # for the agencies dataset

    required_columns = [
        "agency_id",
        "agency_name",
        "agency_type",
        "country"
    ]

    if not validate_required_columns(
        df,
        required_columns,
        "Agencies"
    ):
        passed = False

    # Agency ID should be unique

    if not validate_unique_id(
        df,
        "agency_id",
        "Agencies"
    ):
        passed = False

    # These values should not be NULL

    if not validate_not_null(
        df,
        ["agency_id", "agency_name"],
        "Agencies"
    ):
        passed = False

    return passed


# Validate launcher configurations

def validate_launcher_configurations(df):

    logger.info(
        "Validating launcher configurations"
    )

    passed = True

    # Check whether important columns
    # are available in the dataset

    required_columns = [
        "launcher_configuration_id",
        "launcher_name",
        "manufacturer_id"
    ]

    if not validate_required_columns(
        df,
        required_columns,
        "Launcher configurations"
    ):
        passed = False

    # Launcher configuration ID
    # should be unique

    if not validate_unique_id(
        df,
        "launcher_configuration_id",
        "Launcher configurations"
    ):
        passed = False

    # These values should not be NULL

    if not validate_not_null(
        df,
        [
            "launcher_configuration_id",
            "launcher_name"
        ],
        "Launcher configurations"
    ):
        passed = False

    return passed


# Validate pads

def validate_pads(df):

    logger.info("Validating pads")

    passed = True

    # These columns are required
    # for the pads dataset

    required_columns = [
        "pad_id",
        "pad_name",
        "latitude",
        "longitude"
    ]

    if not validate_required_columns(
        df,
        required_columns,
        "Pads"
    ):
        passed = False

    # Pad ID should be unique

    if not validate_unique_id(
        df,
        "pad_id",
        "Pads"
    ):
        passed = False

    # These values should not be NULL

    if not validate_not_null(
        df,
        ["pad_id", "pad_name"],
        "Pads"
    ):
        passed = False

    # Latitude should always be
    # between -90 and 90

    if not validate_range(
        df,
        "latitude",
        -90,
        90,
        "Pads"
    ):
        passed = False

    # Longitude should always be
    # between -180 and 180

    if not validate_range(
        df,
        "longitude",
        -180,
        180,
        "Pads"
    ):
        passed = False

    return passed


# Validate launches

def validate_launches(
    df,
    agencies_df,
    launcher_configs_df,
    pads_df
):

    logger.info("Validating launches")

    passed = True

    # These columns are required
    # for the launches dataset

    required_columns = [
        "launch_id",
        "launch_name",
        "launch_datetime",
        "agency_id",
        "launcher_configuration_id",
        "pad_id"
    ]

    if not validate_required_columns(
        df,
        required_columns,
        "Launches"
    ):
        passed = False

    # Launch ID should be unique

    if not validate_unique_id(
        df,
        "launch_id",
        "Launches"
    ):
        passed = False

    # Important launch details
    # should not be NULL

    if not validate_not_null(
        df,
        [
            "launch_id",
            "launch_name",
            "launch_datetime"
        ],
        "Launches"
    ):
        passed = False

    # Launch probability should be
    # between 0 and 100

    if not validate_range(
        df,
        "launch_probability",
        0,
        100,
        "Launches"
    ):
        passed = False

    # Check foreign key relationships

    # Launch agency ID should exist
    # in the agencies dataset

    if not validate_foreign_key(
        df,
        "agency_id",
        agencies_df,
        "agency_id",
        "Launches -> Agencies"
    ):
        passed = False

    # Launcher configuration ID should exist
    # in the launcher configurations dataset

    if not validate_foreign_key(
        df,
        "launcher_configuration_id",
        launcher_configs_df,
        "launcher_configuration_id",
        "Launches -> Launcher Configurations"
    ):
        passed = False

    # Pad ID should exist
    # in the pads dataset

    if not validate_foreign_key(
        df,
        "pad_id",
        pads_df,
        "pad_id",
        "Launches -> Pads"
    ):
        passed = False

    return passed


# Main validation pipeline

def main():

    logger.info(
        "SPACE DATA VALIDATION PIPELINE STARTED"
    )

    try:

        # Read all processed datasets

        agencies_df = read_processed_data(
            "agencies.csv"
        )

        launcher_configs_df = (
            read_processed_data(
                "launcher_configurations.csv"
            )
        )

        pads_df = read_processed_data(
            "pads.csv"
        )

        launches_df = read_processed_data(
            "launches.csv"
        )

        # Run validation for each dataset

        validation_results = []

        validation_results.append(
            validate_agencies(
                agencies_df
            )
        )

        validation_results.append(
            validate_launcher_configurations(
                launcher_configs_df
            )
        )

        validation_results.append(
            validate_pads(
                pads_df
            )
        )

        validation_results.append(
            validate_launches(
                launches_df,
                agencies_df,
                launcher_configs_df,
                pads_df
            )
        )

        # Check whether all validations passed

        if all(validation_results):

            logger.info(
                "ALL VALIDATION CHECKS PASSED"
            )

        else:

            logger.error(
                "VALIDATION FAILED"
            )

            raise ValueError(
                "One or more validation checks failed."
            )

    except Exception as e:

        logger.exception(
            f"Validation pipeline failed: {e}"
        )

        raise


# Program entry point

if __name__ == "__main__":
    main()