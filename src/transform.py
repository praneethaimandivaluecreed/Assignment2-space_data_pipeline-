import json
from pathlib import Path

import pandas as pd

from logger import logger


# Configuration

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Create processed folder if it does not already exist
PROCESSED_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# Read raw JSON files

def read_raw_dataset(dataset_name):

    # Get the folder for the selected dataset
    dataset_dir = RAW_DATA_DIR / dataset_name

    # Store records from all JSON files here
    all_records = []

    # Get all page JSON files in sorted order
    json_files = sorted(
        dataset_dir.glob("page_*.json")
    )

    logger.info(
        f"Reading raw dataset: {dataset_name}"
    )

    # Stop the pipeline if no raw files are found
    if not json_files:

        raise FileNotFoundError(
            f"No raw JSON files found for "
            f"{dataset_name}"
        )

    # Read each page JSON file
    for file_path in json_files:

        logger.info(
            f"Reading: {file_path}"
        )

        # Open the JSON file and load its content
        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        # Get only the records from the API response
        records = data.get(
            "results",
            []
        )

        # Add records from this page to the main list
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


# Transform agency data

def transform_agencies(records):

    logger.info("=" * 70)
    logger.info("TRANSFORMING: AGENCIES")
    logger.info("=" * 70)

    # Store cleaned agency records
    transformed = []

    # Process each agency record
    for record in records:

        # Get country information from the API response
        country = record.get("country")

        # Handle country data

        country_name = None

        # Sometimes country can come as a list
        if isinstance(country, list):

            country_names = []

            # Read the name from each country object
            for country_item in country:

                if isinstance(country_item, dict):

                    name = country_item.get("name")

                    if name:
                        country_names.append(name)

            # Join multiple country names into one value
            if country_names:

                country_name = ", ".join(
                    country_names
                )

        # Sometimes country can be a single dictionary
        elif isinstance(country, dict):

            country_name = country.get(
                "name"
            )

        # Log unexpected country formats
        elif country is not None:

            logger.warning(
                f"Agency {record.get('id')} has "
                f"unexpected country data type: "
                f"{type(country).__name__}"
            )

        # Handle agency type

        agency_type = record.get("type")

        agency_type_name = None

        # Extract the agency type name from the dictionary
        if isinstance(agency_type, dict):

            agency_type_name = (
                agency_type.get("name")
            )

        # Log unexpected agency type formats
        elif agency_type is not None:

            logger.warning(
                f"Agency {record.get('id')} has "
                f"unexpected type data."
            )

        # Create a cleaned agency record
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

    # Convert the cleaned records into a DataFrame
    df = pd.DataFrame(transformed)

    # Remove duplicate agencies using agency_id
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

    # Clean text columns

    text_columns = [
        "agency_name",
        "abbreviation",
        "agency_type",
        "country"
    ]

    for column in text_columns:

        # Convert values to string and remove extra spaces
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # Convert numeric columns to proper data types

    df["agency_id"] = pd.to_numeric(
        df["agency_id"],
        errors="coerce"
    ).astype("Int64")

    df["founding_year"] = pd.to_numeric(
        df["founding_year"],
        errors="coerce"
    ).astype("Int64")

    # Log basic data quality information

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


# Transform launcher configuration data

def transform_launcher_configurations(records):

    logger.info("=" * 70)
    logger.info(
        "TRANSFORMING: LAUNCHER CONFIGURATIONS"
    )
    logger.info("=" * 70)

    # Store cleaned launcher configuration records
    transformed = []

    # Process each launcher configuration
    for record in records:

        # Get manufacturer information
        manufacturer = (
            record.get("manufacturer") or {}
        )

        # Make sure manufacturer data is a dictionary
        if not isinstance(
            manufacturer,
            dict
        ):

            logger.warning(
                f"Launcher configuration "
                f"{record.get('id')} has "
                f"unexpected manufacturer format."
            )

            # Use an empty dictionary if the format is incorrect
            manufacturer = {}

        # Create a cleaned launcher configuration record
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

    # Convert records into a DataFrame
    df = pd.DataFrame(transformed)

    # Remove duplicate launcher configurations
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

    # Clean text columns

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

    # Convert ID columns to numeric values

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


# Transform launch pad data

def transform_pads(records):

    logger.info("=" * 70)
    logger.info("TRANSFORMING: PADS")
    logger.info("=" * 70)

    # Store cleaned pad records
    transformed = []

    # Process each pad record
    for record in records:

        # Get country information
        country = (
            record.get("country") or {}
        )

        # Get location information
        location = (
            record.get("location") or {}
        )

        # Handle country

        country_name = None

        # Extract country name from the dictionary
        if isinstance(country, dict):

            country_name = country.get(
                "name"
            )

        # Handle location

        location_id = None
        location_name = None

        # Extract location ID and name
        if isinstance(location, dict):

            location_id = location.get(
                "id"
            )

            location_name = location.get(
                "name"
            )

        # Create a cleaned pad record
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

    # Convert records into a DataFrame
    df = pd.DataFrame(transformed)

    # Remove duplicate pads using pad_id
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

    # Clean text columns

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

    # Convert ID columns to numeric values

    df["pad_id"] = pd.to_numeric(
        df["pad_id"],
        errors="coerce"
    ).astype("Int64")

    df["location_id"] = pd.to_numeric(
        df["location_id"],
        errors="coerce"
    ).astype("Int64")

    # Convert latitude and longitude to numeric values

    df["latitude"] = pd.to_numeric(
        df["latitude"],
        errors="coerce"
    )

    df["longitude"] = pd.to_numeric(
        df["longitude"],
        errors="coerce"
    )

    # Convert launch count columns to integer values

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


# Transform launch data

def transform_launches(
    records,
    agencies_df,
    launcher_configs_df,
    pads_df
):

    logger.info("=" * 70)
    logger.info("TRANSFORMING: LAUNCHES")
    logger.info("=" * 70)

    # Store cleaned launch records
    transformed = []

    # Process each launch record
    for record in records:

        # Get nested status information
        status = (
            record.get("status") or {}
        )

        # Get launch service provider information
        provider = (
            record.get(
                "launch_service_provider"
            ) or {}
        )

        # Get rocket information
        rocket = (
            record.get("rocket") or {}
        )

        # Get rocket configuration information
        configuration = (
            rocket.get("configuration") or {}
        )

        # Get mission information
        mission = (
            record.get("mission") or {}
        )

        # Get launch pad information
        pad = (
            record.get("pad") or {}
        )

        # Create a cleaned launch record
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

    # Convert records into a DataFrame
    df = pd.DataFrame(transformed)

    # Remove duplicate launches using launch_id
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

    # Clean text columns

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

    # Convert columns to correct data types

    # Launch ID is a UUID/string,
    # so we should not convert it to numeric
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

    # Convert launch date/time into a proper datetime
    # UTC is used so all launch times follow one standard
    df["launch_datetime"] = pd.to_datetime(
        df["launch_datetime"],
        errors="coerce",
        utc=True
    )

    # Create year and month from launch date

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

    # Create a True/False flag for successful launches
    # If status contains "success", mark it as True
    df["is_successful"] = (
        df["status_name"]
        .fillna("")
        .str.lower()
        .str.contains(
            "success",
            na=False
        )
    )

    # Validate foreign key relationships

    # Check agency IDs

    # Create a set containing all valid agency IDs
    valid_agency_ids = set(
        agencies_df["agency_id"]
        .dropna()
        .astype(int)
    )

    # Find launches whose agency ID does not exist
    # in the agency table
    missing_agencies = (
        df["agency_id"].notna()
        & ~df["agency_id"]
        .isin(valid_agency_ids)
    )

    logger.info(
        f"Launches with unmatched agencies: "
        f"{missing_agencies.sum()}"
    )

    # Remove invalid agency IDs by setting them to null
    df.loc[
        missing_agencies,
        "agency_id"
    ] = pd.NA

    # Check launcher configuration IDs

    # Create a set containing all valid launcher IDs
    valid_launcher_ids = set(
        launcher_configs_df[
            "launcher_configuration_id"
        ]
        .dropna()
        .astype(int)
    )

    # Find launches with invalid launcher configuration IDs
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

    # Remove invalid launcher configuration IDs
    df.loc[
        missing_launchers,
        "launcher_configuration_id"
    ] = pd.NA

    # Check pad IDs

    # Create a set containing all valid pad IDs
    valid_pad_ids = set(
        pads_df["pad_id"]
        .dropna()
        .astype(int)
    )

    # Find launches with invalid pad IDs
    missing_pads = (
        df["pad_id"].notna()
        & ~df["pad_id"]
        .isin(valid_pad_ids)
    )

    logger.info(
        f"Launches with unmatched pads: "
        f"{missing_pads.sum()}"
    )

    # Remove invalid pad IDs
    df.loc[
        missing_pads,
        "pad_id"
    ] = pd.NA

    # Keep the final columns in a fixed order

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


# Save processed data

def save_processed_data(
    df,
    filename
):

    # Create the complete output file path
    output_file = (
        PROCESSED_DATA_DIR / filename
    )

    # Save the DataFrame as a CSV file
    # index=False avoids writing the DataFrame index
    df.to_csv(
        output_file,
        index=False
    )

    logger.info(
        f"Processed data saved to: "
        f"{output_file}"
    )


# Main transformation pipeline

def main():

    logger.info("=" * 70)
    logger.info(
        "SPACE DATA TRANSFORMATION PIPELINE STARTED"
    )
    logger.info("=" * 70)

    try:

        # Read all raw datasets

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

        # Transform dimension datasets first
        # These are needed later for foreign key validation

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

        # Transform launch data
        # Launches contain IDs that refer to the above datasets

        launches_df = transform_launches(
            launches_raw,
            agencies_df,
            launcher_configs_df,
            pads_df
        )

        # Save all processed datasets

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

        # Print final record counts

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

        # Log the complete error and stop the pipeline
        logger.exception(
            f"Transformation pipeline failed: {e}"
        )

        raise


# Run main() only when this file is executed directly

if __name__ == "__main__":
    main()