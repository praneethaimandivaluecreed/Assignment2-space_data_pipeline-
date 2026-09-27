import json
from pathlib import Path

import pandas as pd

from logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# READ RAW JSON FILES
# ============================================================

def read_raw_dataset(dataset_name):

    dataset_dir = RAW_DATA_DIR / dataset_name

    all_records = []

    json_files = sorted(
        dataset_dir.glob("page_*.json")
    )

    logger.info(
        f"Reading raw dataset: {dataset_name}"
    )

    if not json_files:

        raise FileNotFoundError(
            f"No raw JSON files found for "
            f"{dataset_name}"
        )

    for file_path in json_files:

        logger.info(
            f"Reading: {file_path}"
        )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        records = data.get(
            "results",
            []
        )

        all_records.extend(records)

        logger.info(
            f"Records loaded from file: "
            f"{len(records)}"
        )

    logger.info(
        f"Total raw records for "
        f"{dataset_name}: {len(all_records)}"
    )

    return all_records


# ============================================================
# TRANSFORM AGENCIES
# ============================================================

def transform_agencies(records):

    logger.info("=" * 70)
    logger.info("TRANSFORMING: AGENCIES")
    logger.info("=" * 70)

    transformed = []

    for record in records:

        country = record.get("country")

        # ----------------------------------------------------
        # HANDLE COUNTRY DATA
        # ----------------------------------------------------

        country_name = None

        if isinstance(country, list):

            country_names = []

            for country_item in country:

                if isinstance(country_item, dict):

                    name = country_item.get("name")

                    if name:
                        country_names.append(name)

            if country_names:

                country_name = ", ".join(
                    country_names
                )

        elif isinstance(country, dict):

            country_name = country.get(
                "name"
            )

        elif country is not None:

            logger.warning(
                f"Agency {record.get('id')} has "
                f"unexpected country data type: "
                f"{type(country).__name__}"
            )

        # ----------------------------------------------------
        # HANDLE AGENCY TYPE
        # ----------------------------------------------------

        agency_type = record.get("type")

        agency_type_name = None

        if isinstance(agency_type, dict):

            agency_type_name = (
                agency_type.get("name")
            )

        elif agency_type is not None:

            logger.warning(
                f"Agency {record.get('id')} has "
                f"unexpected type data."
            )

        # ----------------------------------------------------
        # CREATE TRANSFORMED RECORD
        # ----------------------------------------------------

        agency = {

            "agency_id":
                record.get("id"),

            "agency_name":
                record.get("name"),

            "abbreviation":
                record.get("abbrev"),

            "agency_type":
                agency_type_name,

            "country":
                country_name,

            "founding_year":
                record.get("founding_year")
        }

        transformed.append(agency)

    df = pd.DataFrame(transformed)

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    before = len(df)

    df = df.drop_duplicates(
        subset=["agency_id"]
    )

    duplicates_removed = (
        before - len(df)
    )

    logger.info(
        f"Duplicate agencies removed: "
        f"{duplicates_removed}"
    )

    # --------------------------------------------------------
    # STANDARDIZE TEXT
    # --------------------------------------------------------

    text_columns = [
        "agency_name",
        "abbreviation",
        "agency_type",
        "country"
    ]

    for column in text_columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------------
    # DATA TYPES
    # --------------------------------------------------------

    df["agency_id"] = pd.to_numeric(
        df["agency_id"],
        errors="coerce"
    ).astype("Int64")

    df["founding_year"] = pd.to_numeric(
        df["founding_year"],
        errors="coerce"
    ).astype("Int64")

    # --------------------------------------------------------
    # DATA QUALITY SUMMARY
    # --------------------------------------------------------

    logger.info(
        f"Missing agency country values: "
        f"{df['country'].isna().sum()}"
    )

    logger.info(
        f"Missing agency type values: "
        f"{df['agency_type'].isna().sum()}"
    )

    logger.info(
        f"Processed agency records: "
        f"{len(df)}"
    )

    return df


# ============================================================
# TRANSFORM LAUNCHER CONFIGURATIONS
# ============================================================

def transform_launcher_configurations(records):

    logger.info("=" * 70)
    logger.info(
        "TRANSFORMING: LAUNCHER CONFIGURATIONS"
    )
    logger.info("=" * 70)

    transformed = []

    for record in records:

        manufacturer = (
            record.get("manufacturer") or {}
        )

        # ----------------------------------------------------
        # HANDLE MANUFACTURER
        # ----------------------------------------------------

        if not isinstance(
            manufacturer,
            dict
        ):

            logger.warning(
                f"Launcher configuration "
                f"{record.get('id')} has "
                f"unexpected manufacturer format."
            )

            manufacturer = {}

        transformed.append({

            "launcher_configuration_id":
                record.get("id"),

            "launcher_name":
                record.get("name"),

            "full_name":
                record.get("full_name"),

            "variant":
                record.get("variant"),

            "manufacturer_id":
                manufacturer.get("id"),

            "manufacturer_name":
                manufacturer.get("name"),

            "active":
                record.get("active"),

            "reusable":
                record.get("reusable")
        })

    df = pd.DataFrame(transformed)

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    before = len(df)

    df = df.drop_duplicates(
        subset=[
            "launcher_configuration_id"
        ]
    )

    duplicates_removed = (
        before - len(df)
    )

    logger.info(
        f"Duplicate launcher configurations "
        f"removed: {duplicates_removed}"
    )

    # --------------------------------------------------------
    # STANDARDIZE TEXT
    # --------------------------------------------------------

    text_columns = [
        "launcher_name",
        "full_name",
        "variant",
        "manufacturer_name"
    ]

    for column in text_columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------------
    # DATA TYPES
    # --------------------------------------------------------

    df["launcher_configuration_id"] = (
        pd.to_numeric(
            df["launcher_configuration_id"],
            errors="coerce"
        ).astype("Int64")
    )

    df["manufacturer_id"] = (
        pd.to_numeric(
            df["manufacturer_id"],
            errors="coerce"
        ).astype("Int64")
    )

    logger.info(
        "Launcher configuration transformation "
        "completed."
    )

    logger.info(
        f"Processed records: {len(df)}"
    )

    return df


# ============================================================
# TRANSFORM PADS
# ============================================================

def transform_pads(records):

    logger.info("=" * 70)
    logger.info("TRANSFORMING: PADS")
    logger.info("=" * 70)

    transformed = []

    for record in records:

        country = (
            record.get("country") or {}
        )

        location = (
            record.get("location") or {}
        )

        # ----------------------------------------------------
        # HANDLE COUNTRY
        # ----------------------------------------------------

        country_name = None

        if isinstance(country, dict):

            country_name = country.get(
                "name"
            )

        # ----------------------------------------------------
        # HANDLE LOCATION
        # ----------------------------------------------------

        location_id = None
        location_name = None

        if isinstance(location, dict):

            location_id = location.get(
                "id"
            )

            location_name = location.get(
                "name"
            )

        transformed.append({

            "pad_id":
                record.get("id"),

            "pad_name":
                record.get("name"),

            "active":
                record.get("active"),

            "latitude":
                record.get("latitude"),

            "longitude":
                record.get("longitude"),

            "country":
                country_name,

            "location_id":
                location_id,

            "location_name":
                location_name,

            "total_launch_count":
                record.get(
                    "total_launch_count"
                ),

            "orbital_launch_attempt_count":
                record.get(
                    "orbital_launch_attempt_count"
                ),

            "fastest_turnaround":
                record.get(
                    "fastest_turnaround"
                )
        })

    df = pd.DataFrame(transformed)

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    before = len(df)

    df = df.drop_duplicates(
        subset=["pad_id"]
    )

    duplicates_removed = (
        before - len(df)
    )

    logger.info(
        f"Duplicate pads removed: "
        f"{duplicates_removed}"
    )

    # --------------------------------------------------------
    # STANDARDIZE TEXT
    # --------------------------------------------------------

    text_columns = [
        "pad_name",
        "country",
        "location_name"
    ]

    for column in text_columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------------
    # DATA TYPES
    # --------------------------------------------------------

    df["pad_id"] = pd.to_numeric(
        df["pad_id"],
        errors="coerce"
    ).astype("Int64")

    df["location_id"] = pd.to_numeric(
        df["location_id"],
        errors="coerce"
    ).astype("Int64")

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    df["total_launch_count"] = pd.to_numeric(
        df["total_launch_count"],
        errors="coerce"
    ).astype("Int64")

    df["orbital_launch_attempt_count"] = (
        pd.to_numeric(
            df["orbital_launch_attempt_count"],
            errors="coerce"
        ).astype("Int64")
    )

    logger.info(
        f"Processed pad records: "
        f"{len(df)}"
    )

    return df


# ============================================================
# TRANSFORM LAUNCHES
# ============================================================

def transform_launches(
    records,
    agencies_df,
    launcher_configs_df,
    pads_df
):

    logger.info("=" * 70)
    logger.info("TRANSFORMING: LAUNCHES")
    logger.info("=" * 70)

    transformed = []

    for record in records:

        status = (
            record.get("status") or {}
        )

        provider = (
            record.get(
                "launch_service_provider"
            ) or {}
        )

        rocket = (
            record.get("rocket") or {}
        )

        configuration = (
            rocket.get("configuration") or {}
        )

        mission = (
            record.get("mission") or {}
        )

        pad = (
            record.get("pad") or {}
        )

        transformed.append({

            "launch_id":
                record.get("id"),

            "launch_name":
                record.get("name"),

            "launch_datetime":
                record.get("net"),

            "status_id":
                status.get("id"),

            "status_name":
                status.get("name"),

            "launch_probability":
                record.get("probability"),

            "weather_concerns":
                record.get(
                    "weather_concerns"
                ),

            "failure_reason":
                record.get(
                    "failreason"
                ),

            "agency_id":
                provider.get("id"),

            "launcher_configuration_id":
                configuration.get("id"),

            "pad_id":
                pad.get("id"),

            "mission_name":
                mission.get("name"),

            "mission_type":
                mission.get("type")
        })

    df = pd.DataFrame(transformed)

    # --------------------------------------------------------
    # REMOVE DUPLICATE LAUNCHES
    # --------------------------------------------------------

    before = len(df)

    df = df.drop_duplicates(
        subset=["launch_id"]
    )

    duplicates_removed = (
        before - len(df)
    )

    logger.info(
        f"Duplicate launches removed: "
        f"{duplicates_removed}"
    )

    # --------------------------------------------------------
    # STANDARDIZE TEXT
    # --------------------------------------------------------

    text_columns = [
        "launch_name",
        "status_name",
        "weather_concerns",
        "failure_reason",
        "mission_name",
        "mission_type"
    ]

    for column in text_columns:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------------
    # DATA TYPES
    # --------------------------------------------------------

    # Launch ID is a UUID/string.
    # Do NOT convert it to numeric.
    df["launch_id"] = (
        df["launch_id"]
        .astype("string")
        .str.strip()
    )

    df["status_id"] = pd.to_numeric(
        df["status_id"],
        errors="coerce"
    ).astype("Int64")

    df["agency_id"] = pd.to_numeric(
        df["agency_id"],
        errors="coerce"
    ).astype("Int64")

    df["launcher_configuration_id"] = (
        pd.to_numeric(
            df["launcher_configuration_id"],
            errors="coerce"
        ).astype("Int64")
    )

    df["pad_id"] = pd.to_numeric(
        df["pad_id"],
        errors="coerce"
    ).astype("Int64")

    df["launch_probability"] = pd.to_numeric(
        df["launch_probability"],
        errors="coerce"
    )

    df["launch_datetime"] = pd.to_datetime(
        df["launch_datetime"],
        errors="coerce",
        utc=True
    )

    # --------------------------------------------------------
    # DERIVED FIELDS
    # --------------------------------------------------------

    df["launch_year"] = (
        df["launch_datetime"]
        .dt.year
        .astype("Int64")
    )

    df["launch_month"] = (
        df["launch_datetime"]
        .dt.month
        .astype("Int64")
    )

    # --------------------------------------------------------
    # DERIVED SUCCESS FLAG
    # --------------------------------------------------------

    df["is_successful"] = (
        df["status_name"]
        .fillna("")
        .str.lower()
        .str.contains(
            "success",
            na=False
        )
    )

    # --------------------------------------------------------
    # FOREIGN KEY VALIDATION
    # --------------------------------------------------------

    # --------------------------------------------------------
    # AGENCY VALIDATION
    # --------------------------------------------------------

    valid_agency_ids = set(
        agencies_df["agency_id"]
        .dropna()
        .astype(int)
    )

    missing_agencies = (
        df["agency_id"].notna()
        & ~df["agency_id"]
        .isin(valid_agency_ids)
    )

    logger.info(
        f"Launches with unmatched agencies: "
        f"{missing_agencies.sum()}"
    )

    df.loc[
        missing_agencies,
        "agency_id"
    ] = pd.NA

    # --------------------------------------------------------
    # LAUNCHER CONFIGURATION VALIDATION
    # --------------------------------------------------------

    valid_launcher_ids = set(
        launcher_configs_df[
            "launcher_configuration_id"
        ]
        .dropna()
        .astype(int)
    )

    missing_launchers = (
        df["launcher_configuration_id"].notna()
        & ~df["launcher_configuration_id"]
        .isin(valid_launcher_ids)
    )

    logger.info(
        f"Launches with unmatched launcher "
        f"configurations: "
        f"{missing_launchers.sum()}"
    )

    df.loc[
        missing_launchers,
        "launcher_configuration_id"
    ] = pd.NA

    # --------------------------------------------------------
    # PAD VALIDATION
    # --------------------------------------------------------

    valid_pad_ids = set(
        pads_df["pad_id"]
        .dropna()
        .astype(int)
    )

    missing_pads = (
        df["pad_id"].notna()
        & ~df["pad_id"]
        .isin(valid_pad_ids)
    )

    logger.info(
        f"Launches with unmatched pads: "
        f"{missing_pads.sum()}"
    )

    df.loc[
        missing_pads,
        "pad_id"
    ] = pd.NA

    # --------------------------------------------------------
    # FINAL COLUMN ORDER
    # --------------------------------------------------------

    df = df[
        [
            "launch_id",
            "launch_name",
            "launch_datetime",
            "status_id",
            "status_name",
            "launch_probability",
            "weather_concerns",
            "failure_reason",
            "agency_id",
            "launcher_configuration_id",
            "pad_id",
            "mission_name",
            "mission_type",
            "launch_year",
            "launch_month",
            "is_successful"
        ]
    ]

    logger.info(
        f"Successful launches: "
        f"{df['is_successful'].sum()}"
    )

    logger.info(
        f"Processed launch records: "
        f"{len(df)}"
    )

    return df


# ============================================================
# SAVE PROCESSED DATA
# ============================================================

def save_processed_data(
    df,
    filename
):

    output_file = (
        PROCESSED_DATA_DIR / filename
    )

    df.to_csv(
        output_file,
        index=False
    )

    logger.info(
        f"Processed data saved to: "
        f"{output_file}"
    )


# ============================================================
# MAIN TRANSFORMATION PIPELINE
# ============================================================

def main():

    logger.info("=" * 70)
    logger.info(
        "SPACE DATA TRANSFORMATION PIPELINE STARTED"
    )
    logger.info("=" * 70)

    try:

        # ----------------------------------------------------
        # READ RAW DATA
        # ----------------------------------------------------

        agencies_raw = read_raw_dataset(
            "agencies"
        )

        launcher_configs_raw = (
            read_raw_dataset(
                "launcher_configurations"
            )
        )

        pads_raw = read_raw_dataset(
            "pads"
        )

        launches_raw = read_raw_dataset(
            "launches"
        )

        # ----------------------------------------------------
        # TRANSFORM DIMENSION TABLES
        # ----------------------------------------------------

        agencies_df = transform_agencies(
            agencies_raw
        )

        launcher_configs_df = (
            transform_launcher_configurations(
                launcher_configs_raw
            )
        )

        pads_df = transform_pads(
            pads_raw
        )

        # ----------------------------------------------------
        # TRANSFORM LAUNCHES
        # ----------------------------------------------------

        launches_df = transform_launches(
            launches_raw,
            agencies_df,
            launcher_configs_df,
            pads_df
        )

        # ----------------------------------------------------
        # SAVE PROCESSED DATA
        # ----------------------------------------------------

        save_processed_data(
            agencies_df,
            "agencies.csv"
        )

        save_processed_data(
            launcher_configs_df,
            "launcher_configurations.csv"
        )

        save_processed_data(
            pads_df,
            "pads.csv"
        )

        save_processed_data(
            launches_df,
            "launches.csv"
        )

        # ----------------------------------------------------
        # FINAL SUMMARY
        # ----------------------------------------------------

        logger.info("=" * 70)
        logger.info("TRANSFORMATION SUMMARY")
        logger.info("=" * 70)

        logger.info(
            f"Agencies: "
            f"{len(agencies_df)}"
        )

        logger.info(
            f"Launcher configurations: "
            f"{len(launcher_configs_df)}"
        )

        logger.info(
            f"Pads: "
            f"{len(pads_df)}"
        )

        logger.info(
            f"Launches: "
            f"{len(launches_df)}"
        )

        logger.info("=" * 70)
        logger.info(
            "SPACE DATA TRANSFORMATION PIPELINE "
            "COMPLETED"
        )
        logger.info("=" * 70)

    except Exception as e:

        logger.exception(
            f"Transformation pipeline failed: {e}"
        )

        raise


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()