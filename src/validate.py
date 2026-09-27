import pandas as pd
from pathlib import Path

from logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA_DIR = (
    PROJECT_ROOT / "data" / "processed"
)


# ============================================================
# READ PROCESSED DATA
# ============================================================

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


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

def validate_required_columns(
    df,
    required_columns,
    dataset_name
):

    logger.info(
        f"Validating columns: {dataset_name}"
    )

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


# ============================================================
# VALIDATE DUPLICATE IDs
# ============================================================

def validate_unique_id(
    df,
    id_column,
    dataset_name
):

    logger.info(
        f"Checking duplicate IDs: {dataset_name}"
    )

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


# ============================================================
# VALIDATE REQUIRED VALUES
# ============================================================

def validate_not_null(
    df,
    columns,
    dataset_name
):

    logger.info(
        f"Checking NULL values: {dataset_name}"
    )

    validation_passed = True

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


# ============================================================
# VALIDATE NUMERIC RANGE
# ============================================================

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


# ============================================================
# VALIDATE FOREIGN KEY
# ============================================================

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

    valid_ids = set(
        parent_df[parent_column]
        .dropna()
    )

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


# ============================================================
# VALIDATE AGENCIES
# ============================================================

def validate_agencies(df):

    logger.info("=" * 70)
    logger.info("VALIDATING: AGENCIES")
    logger.info("=" * 70)

    passed = True

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

    if not validate_unique_id(
        df,
        "agency_id",
        "Agencies"
    ):
        passed = False

    if not validate_not_null(
        df,
        ["agency_id", "agency_name"],
        "Agencies"
    ):
        passed = False

    return passed


# ============================================================
# VALIDATE LAUNCHER CONFIGURATIONS
# ============================================================

def validate_launcher_configurations(df):

    logger.info("=" * 70)
    logger.info(
        "VALIDATING: LAUNCHER CONFIGURATIONS"
    )
    logger.info("=" * 70)

    passed = True

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

    if not validate_unique_id(
        df,
        "launcher_configuration_id",
        "Launcher configurations"
    ):
        passed = False

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


# ============================================================
# VALIDATE PADS
# ============================================================

def validate_pads(df):

    logger.info("=" * 70)
    logger.info("VALIDATING: PADS")
    logger.info("=" * 70)

    passed = True

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

    if not validate_unique_id(
        df,
        "pad_id",
        "Pads"
    ):
        passed = False

    if not validate_not_null(
        df,
        ["pad_id", "pad_name"],
        "Pads"
    ):
        passed = False

    if not validate_range(
        df,
        "latitude",
        -90,
        90,
        "Pads"
    ):
        passed = False

    if not validate_range(
        df,
        "longitude",
        -180,
        180,
        "Pads"
    ):
        passed = False

    return passed


# ============================================================
# VALIDATE LAUNCHES
# ============================================================

def validate_launches(
    df,
    agencies_df,
    launcher_configs_df,
    pads_df
):

    logger.info("=" * 70)
    logger.info("VALIDATING: LAUNCHES")
    logger.info("=" * 70)

    passed = True

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

    if not validate_unique_id(
        df,
        "launch_id",
        "Launches"
    ):
        passed = False

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

    if not validate_range(
        df,
        "launch_probability",
        0,
        100,
        "Launches"
    ):
        passed = False

    # --------------------------------------------------------
    # FOREIGN KEY VALIDATION
    # --------------------------------------------------------

    if not validate_foreign_key(
        df,
        "agency_id",
        agencies_df,
        "agency_id",
        "Launches -> Agencies"
    ):
        passed = False

    if not validate_foreign_key(
        df,
        "launcher_configuration_id",
        launcher_configs_df,
        "launcher_configuration_id",
        "Launches -> Launcher Configurations"
    ):
        passed = False

    if not validate_foreign_key(
        df,
        "pad_id",
        pads_df,
        "pad_id",
        "Launches -> Pads"
    ):
        passed = False

    return passed


# ============================================================
# MAIN VALIDATION PIPELINE
# ============================================================

def main():

    logger.info("=" * 70)
    logger.info(
        "SPACE DATA VALIDATION PIPELINE STARTED"
    )
    logger.info("=" * 70)

    try:

        # ----------------------------------------------------
        # READ PROCESSED DATA
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # VALIDATE DATASETS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # FINAL VALIDATION RESULT
        # ----------------------------------------------------

        if all(validation_results):

            logger.info("=" * 70)
            logger.info(
                "ALL VALIDATION CHECKS PASSED"
            )
            logger.info("=" * 70)

        else:

            logger.error("=" * 70)
            logger.error(
                "VALIDATION FAILED"
            )
            logger.error("=" * 70)

            raise ValueError(
                "One or more validation checks failed."
            )

    except Exception as e:

        logger.exception(
            f"Validation pipeline failed: {e}"
        )

        raise


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()