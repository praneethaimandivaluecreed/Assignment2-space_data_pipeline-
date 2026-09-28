import os
from pathlib import Path

import pandas as pd
import pyodbc
from dotenv import load_dotenv

from logger import logger


# Configuration

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA_DIR = (
    PROJECT_ROOT / "data" / "processed"
)

# Number of records processed
# in one transaction

BATCH_SIZE = 500


# Load environment variables

load_dotenv(
    PROJECT_ROOT / ".env"
)


# Database configuration

DB_DRIVER = os.getenv("DB_DRIVER")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")

DB_TRUSTED_CONNECTION = os.getenv(
    "DB_TRUSTED_CONNECTION"
)

DB_TRUST_SERVER_CERTIFICATE = os.getenv(
    "DB_TRUST_SERVER_CERTIFICATE"
)


# Read processed data

def read_processed_data(filename):

    file_path = (
        PROCESSED_DATA_DIR / filename
    )

    logger.info(
        f"Reading processed file: {file_path}"
    )

    # Check whether the processed file
    # exists before reading it

    if not file_path.exists():

        raise FileNotFoundError(
            f"Processed file not found: "
            f"{file_path}"
        )

    return pd.read_csv(file_path)


# Validate database configuration

def validate_database_configuration():

    logger.info(
        "Validating database configuration"
    )

    # Store all required database
    # configuration values

    required_variables = {
        "DB_DRIVER": DB_DRIVER,
        "DB_SERVER": DB_SERVER,
        "DB_DATABASE": DB_DATABASE,
        "DB_TRUSTED_CONNECTION":
            DB_TRUSTED_CONNECTION,
        "DB_TRUST_SERVER_CERTIFICATE":
            DB_TRUST_SERVER_CERTIFICATE
    }

    # Find configuration values
    # which are missing or empty

    missing_variables = [
        name
        for name, value
        in required_variables.items()
        if not value
    ]

    if missing_variables:

        raise ValueError(
            "Missing database configuration: "
            f"{missing_variables}"
        )

    logger.info(
        "Database configuration validation passed"
    )


# Create database connection

def create_connection():

    validate_database_configuration()

    # Build the SQL Server connection string
    # using values from the environment file

    connection_string = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"Trusted_Connection={DB_TRUSTED_CONNECTION};"
        f"TrustServerCertificate="
        f"{DB_TRUST_SERVER_CERTIFICATE};"
    )

    logger.info(
        "Connecting to SQL Server"
    )

    try:

        connection = pyodbc.connect(
            connection_string
        )

        logger.info(
            "SQL Server connection successful"
        )

        return connection

    except pyodbc.Error as e:

        logger.exception(
            f"Database connection failed: {e}"
        )

        raise


# Convert value for SQL Server

def clean_value(value):

    # Convert Pandas NULL values into
    # Python None values for SQL Server

    if pd.isna(value):

        return None

    return value


# Load agencies

def load_agencies(
    connection,
    df
):

    logger.info("Loading agencies")

    cursor = connection.cursor()

    insert_count = 0
    update_count = 0

    try:

        # Process the dataframe in batches
        # to avoid loading everything at once

        for start in range(
            0,
            len(df),
            BATCH_SIZE
        ):

            batch = df.iloc[
                start:start + BATCH_SIZE
            ]

            batch_inserted = 0
            batch_updated = 0

            try:

                # Process each record
                # in the current batch

                for _, row in batch.iterrows():

                    agency_id = clean_value(
                        row["agency_id"]
                    )

                    # Check whether the agency
                    # already exists in the database

                    cursor.execute("""
                        SELECT 1
                        FROM dbo.agencies
                        WHERE agency_id = ?
                    """, agency_id)

                    exists = cursor.fetchone()

                    if exists:

                        # Existing agency record
                        # should be updated

                        cursor.execute("""
                            UPDATE dbo.agencies
                            SET
                                agency_name = ?,
                                abbreviation = ?,
                                agency_type = ?,
                                country = ?,
                                founding_year = ?
                            WHERE agency_id = ?
                        """,
                            clean_value(
                                row["agency_name"]
                            ),
                            clean_value(
                                row["abbreviation"]
                            ),
                            clean_value(
                                row["agency_type"]
                            ),
                            clean_value(
                                row["country"]
                            ),
                            clean_value(
                                row["founding_year"]
                            ),
                            agency_id
                        )

                        batch_updated += 1

                    else:

                        # New agency record
                        # should be inserted

                        cursor.execute("""
                            INSERT INTO dbo.agencies
                            (
                                agency_id,
                                agency_name,
                                abbreviation,
                                agency_type,
                                country,
                                founding_year
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                        """,
                            agency_id,
                            clean_value(
                                row["agency_name"]
                            ),
                            clean_value(
                                row["abbreviation"]
                            ),
                            clean_value(
                                row["agency_type"]
                            ),
                            clean_value(
                                row["country"]
                            ),
                            clean_value(
                                row["founding_year"]
                            )
                        )

                        batch_inserted += 1

                # Commit the current batch
                # after all records are processed

                connection.commit()

                insert_count += batch_inserted
                update_count += batch_updated

                logger.info(
                    f"Agencies batch committed: "
                    f"{len(batch)} records | "
                    f"Inserted: {batch_inserted} | "
                    f"Updated: {batch_updated}"
                )

            except pyodbc.Error as e:

                # Roll back the current batch
                # if a database error occurs

                connection.rollback()

                logger.exception(
                    f"Agency batch failed. "
                    f"Batch starting at {start}. "
                    f"Rolled back batch: {e}"
                )

                raise

        logger.info(
            f"Agencies loading completed | "
            f"Inserted: {insert_count} | "
            f"Updated: {update_count}"
        )

    finally:

        # Close the cursor after loading

        cursor.close()


# Load launcher configurations

def load_launcher_configurations(
    connection,
    df
):

    logger.info(
        "Loading launcher configurations"
    )

    cursor = connection.cursor()

    insert_count = 0
    update_count = 0

    try:

        # Process the dataframe in batches

        for start in range(
            0,
            len(df),
            BATCH_SIZE
        ):

            batch = df.iloc[
                start:start + BATCH_SIZE
            ]

            batch_inserted = 0
            batch_updated = 0

            try:

                # Process each launcher
                # configuration in the batch

                for _, row in batch.iterrows():

                    record_id = clean_value(
                        row[
                            "launcher_configuration_id"
                        ]
                    )

                    # Check whether the launcher
                    # configuration already exists

                    cursor.execute("""
                        SELECT 1
                        FROM dbo.launcher_configurations
                        WHERE launcher_configuration_id = ?
                    """, record_id)

                    exists = cursor.fetchone()

                    if exists:

                        # Existing record
                        # should be updated

                        cursor.execute("""
                            UPDATE dbo.launcher_configurations
                            SET
                                launcher_name = ?,
                                full_name = ?,
                                variant = ?,
                                manufacturer_id = ?,
                                manufacturer_name = ?,
                                active = ?,
                                reusable = ?
                            WHERE launcher_configuration_id = ?
                        """,
                            clean_value(
                                row["launcher_name"]
                            ),
                            clean_value(
                                row["full_name"]
                            ),
                            clean_value(
                                row["variant"]
                            ),
                            clean_value(
                                row["manufacturer_id"]
                            ),
                            clean_value(
                                row["manufacturer_name"]
                            ),
                            clean_value(
                                row["active"]
                            ),
                            clean_value(
                                row["reusable"]
                            ),
                            record_id
                        )

                        batch_updated += 1

                    else:

                        # New record
                        # should be inserted

                        cursor.execute("""
                            INSERT INTO dbo.launcher_configurations
                            (
                                launcher_configuration_id,
                                launcher_name,
                                full_name,
                                variant,
                                manufacturer_id,
                                manufacturer_name,
                                active,
                                reusable
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            record_id,
                            clean_value(
                                row["launcher_name"]
                            ),
                            clean_value(
                                row["full_name"]
                            ),
                            clean_value(
                                row["variant"]
                            ),
                            clean_value(
                                row["manufacturer_id"]
                            ),
                            clean_value(
                                row["manufacturer_name"]
                            ),
                            clean_value(
                                row["active"]
                            ),
                            clean_value(
                                row["reusable"]
                            )
                        )

                        batch_inserted += 1

                # Commit the current batch

                connection.commit()

                insert_count += batch_inserted
                update_count += batch_updated

                logger.info(
                    f"Launcher configuration batch "
                    f"committed: {len(batch)} records | "
                    f"Inserted: {batch_inserted} | "
                    f"Updated: {batch_updated}"
                )

            except pyodbc.Error as e:

                # Roll back the current batch
                # if loading fails

                connection.rollback()

                logger.exception(
                    f"Launcher configuration batch "
                    f"failed. Batch starting at "
                    f"{start}. Rolled back batch: {e}"
                )

                raise

        logger.info(
            f"Launcher configuration loading "
            f"completed | "
            f"Inserted: {insert_count} | "
            f"Updated: {update_count}"
        )

    finally:

        cursor.close()


# Load pads

def load_pads(
    connection,
    df
):

    logger.info("Loading pads")

    cursor = connection.cursor()

    insert_count = 0
    update_count = 0

    try:

        # Process the dataframe in batches

        for start in range(
            0,
            len(df),
            BATCH_SIZE
        ):

            batch = df.iloc[
                start:start + BATCH_SIZE
            ]

            batch_inserted = 0
            batch_updated = 0

            try:

                for _, row in batch.iterrows():

                    record_id = clean_value(
                        row["pad_id"]
                    )

                    # Check whether the pad
                    # already exists

                    cursor.execute("""
                        SELECT 1
                        FROM dbo.pads
                        WHERE pad_id = ?
                    """, record_id)

                    exists = cursor.fetchone()

                    if exists:

                        # Existing pad
                        # should be updated

                        cursor.execute("""
                            UPDATE dbo.pads
                            SET
                                pad_name = ?,
                                active = ?,
                                latitude = ?,
                                longitude = ?,
                                country = ?,
                                location_id = ?,
                                location_name = ?,
                                total_launch_count = ?,
                                orbital_launch_attempt_count = ?,
                                fastest_turnaround = ?
                            WHERE pad_id = ?
                        """,
                            clean_value(
                                row["pad_name"]
                            ),
                            clean_value(
                                row["active"]
                            ),
                            clean_value(
                                row["latitude"]
                            ),
                            clean_value(
                                row["longitude"]
                            ),
                            clean_value(
                                row["country"]
                            ),
                            clean_value(
                                row["location_id"]
                            ),
                            clean_value(
                                row["location_name"]
                            ),
                            clean_value(
                                row[
                                    "total_launch_count"
                                ]
                            ),
                            clean_value(
                                row[
                                    "orbital_launch_attempt_count"
                                ]
                            ),
                            clean_value(
                                row[
                                    "fastest_turnaround"
                                ]
                            ),
                            record_id
                        )

                        batch_updated += 1

                    else:

                        # New pad
                        # should be inserted

                        cursor.execute("""
                            INSERT INTO dbo.pads
                            (
                                pad_id,
                                pad_name,
                                active,
                                latitude,
                                longitude,
                                country,
                                location_id,
                                location_name,
                                total_launch_count,
                                orbital_launch_attempt_count,
                                fastest_turnaround
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            record_id,
                            clean_value(
                                row["pad_name"]
                            ),
                            clean_value(
                                row["active"]
                            ),
                            clean_value(
                                row["latitude"]
                            ),
                            clean_value(
                                row["longitude"]
                            ),
                            clean_value(
                                row["country"]
                            ),
                            clean_value(
                                row["location_id"]
                            ),
                            clean_value(
                                row["location_name"]
                            ),
                            clean_value(
                                row[
                                    "total_launch_count"
                                ]
                            ),
                            clean_value(
                                row[
                                    "orbital_launch_attempt_count"
                                ]
                            ),
                            clean_value(
                                row[
                                    "fastest_turnaround"
                                ]
                            )
                        )

                        batch_inserted += 1

                # Commit the current batch

                connection.commit()

                insert_count += batch_inserted
                update_count += batch_updated

                logger.info(
                    f"Pads batch committed: "
                    f"{len(batch)} records | "
                    f"Inserted: {batch_inserted} | "
                    f"Updated: {batch_updated}"
                )

            except pyodbc.Error as e:

                # Roll back the current batch
                # if a database error occurs

                connection.rollback()

                logger.exception(
                    f"Pad batch failed. "
                    f"Batch starting at {start}. "
                    f"Rolled back batch: {e}"
                )

                raise

        logger.info(
            f"Pad loading completed | "
            f"Inserted: {insert_count} | "
            f"Updated: {update_count}"
        )

    finally:

        cursor.close()


# Load launches

def load_launches(
    connection,
    df
):

    logger.info("Loading launches")

    cursor = connection.cursor()

    insert_count = 0
    update_count = 0

    try:

        # Process the dataframe in batches

        for start in range(
            0,
            len(df),
            BATCH_SIZE
        ):

            batch = df.iloc[
                start:start + BATCH_SIZE
            ]

            batch_inserted = 0
            batch_updated = 0

            try:

                for _, row in batch.iterrows():

                    launch_id = clean_value(
                        row["launch_id"]
                    )

                    # Check whether the launch
                    # already exists

                    cursor.execute("""
                        SELECT 1
                        FROM dbo.launches
                        WHERE launch_id = ?
                    """, launch_id)

                    exists = cursor.fetchone()

                    if exists:

                        # Existing launch record
                        # should be updated

                        cursor.execute("""
                            UPDATE dbo.launches
                            SET
                                launch_name = ?,
                                launch_datetime = ?,
                                status_id = ?,
                                status_name = ?,
                                launch_probability = ?,
                                weather_concerns = ?,
                                failure_reason = ?,
                                agency_id = ?,
                                launcher_configuration_id = ?,
                                pad_id = ?,
                                mission_name = ?,
                                mission_type = ?,
                                launch_year = ?,
                                launch_month = ?,
                                is_successful = ?
                            WHERE launch_id = ?
                        """,
                            clean_value(
                                row["launch_name"]
                            ),
                            clean_value(
                                row["launch_datetime"]
                            ),
                            clean_value(
                                row["status_id"]
                            ),
                            clean_value(
                                row["status_name"]
                            ),
                            clean_value(
                                row[
                                    "launch_probability"
                                ]
                            ),
                            clean_value(
                                row["weather_concerns"]
                            ),
                            clean_value(
                                row["failure_reason"]
                            ),
                            clean_value(
                                row["agency_id"]
                            ),
                            clean_value(
                                row[
                                    "launcher_configuration_id"
                                ]
                            ),
                            clean_value(
                                row["pad_id"]
                            ),
                            clean_value(
                                row["mission_name"]
                            ),
                            clean_value(
                                row["mission_type"]
                            ),
                            clean_value(
                                row["launch_year"]
                            ),
                            clean_value(
                                row["launch_month"]
                            ),
                            clean_value(
                                row["is_successful"]
                            ),
                            launch_id
                        )

                        batch_updated += 1

                    else:

                        # New launch record
                        # should be inserted

                        cursor.execute("""
                            INSERT INTO dbo.launches
                            (
                                launch_id,
                                launch_name,
                                launch_datetime,
                                status_id,
                                status_name,
                                launch_probability,
                                weather_concerns,
                                failure_reason,
                                agency_id,
                                launcher_configuration_id,
                                pad_id,
                                mission_name,
                                mission_type,
                                launch_year,
                                launch_month,
                                is_successful
                            )
                            VALUES (
                                ?, ?, ?, ?, ?,
                                ?, ?, ?, ?, ?,
                                ?, ?, ?, ?, ?, ?
                            )
                        """,
                            launch_id,
                            clean_value(
                                row["launch_name"]
                            ),
                            clean_value(
                                row["launch_datetime"]
                            ),
                            clean_value(
                                row["status_id"]
                            ),
                            clean_value(
                                row["status_name"]
                            ),
                            clean_value(
                                row[
                                    "launch_probability"
                                ]
                            ),
                            clean_value(
                                row["weather_concerns"]
                            ),
                            clean_value(
                                row["failure_reason"]
                            ),
                            clean_value(
                                row["agency_id"]
                            ),
                            clean_value(
                                row[
                                    "launcher_configuration_id"
                                ]
                            ),
                            clean_value(
                                row["pad_id"]
                            ),
                            clean_value(
                                row["mission_name"]
                            ),
                            clean_value(
                                row["mission_type"]
                            ),
                            clean_value(
                                row["launch_year"]
                            ),
                            clean_value(
                                row["launch_month"]
                            ),
                            clean_value(
                                row["is_successful"]
                            )
                        )

                        batch_inserted += 1

                # Commit the current batch
                # after all records are processed

                connection.commit()

                insert_count += batch_inserted
                update_count += batch_updated

                logger.info(
                    f"Launch batch committed: "
                    f"{len(batch)} records | "
                    f"Inserted: {batch_inserted} | "
                    f"Updated: {batch_updated}"
                )

            except pyodbc.Error as e:

                # Roll back the current batch
                # if a database error occurs

                connection.rollback()

                logger.exception(
                    f"Launch batch failed. "
                    f"Batch starting at {start}. "
                    f"Rolled back current batch: {e}"
                )

                raise

        logger.info(
            f"Launch loading completed | "
            f"Inserted: {insert_count} | "
            f"Updated: {update_count}"
        )

    finally:

        cursor.close()


# Main loading pipeline

def main():

    logger.info(
        "SPACE DATA LOADING PIPELINE STARTED"
    )

    connection = None

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

        logger.info(
            "All processed datasets loaded successfully"
        )

        # Create SQL Server connection

        connection = create_connection()

        # Load dimension tables first
        # because launches contain foreign keys
        # referring to these tables

        load_agencies(
            connection,
            agencies_df
        )

        load_launcher_configurations(
            connection,
            launcher_configs_df
        )

        load_pads(
            connection,
            pads_df
        )

        # Load the main launches table

        load_launches(
            connection,
            launches_df
        )

        # Display final processing summary

        logger.info(
            "SPACE DATA LOADING PIPELINE COMPLETED"
        )

        logger.info(
            f"Agencies processed: "
            f"{len(agencies_df)}"
        )

        logger.info(
            f"Launcher configurations "
            f"processed: "
            f"{len(launcher_configs_df)}"
        )

        logger.info(
            f"Pads processed: "
            f"{len(pads_df)}"
        )

        logger.info(
            f"Launches processed: "
            f"{len(launches_df)}"
        )

    except Exception as e:

        logger.exception(
            f"Loading pipeline failed: {e}"
        )

        raise

    finally:

        # Close the database connection
        # after the pipeline finishes

        if connection is not None:

            connection.close()

            logger.info(
                "Database connection closed"
            )


# Program entry point

if __name__ == "__main__":
    main()