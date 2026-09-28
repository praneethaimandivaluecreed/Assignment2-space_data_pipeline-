import os
from pathlib import Path

import numpy as np
import pandas as pd
import pyodbc
from dotenv import load_dotenv

from logger import logger


# Configuration

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA_DIR = (
    PROJECT_ROOT / "data" / "processed"
)

# Small batch size is used so that
# rollback behavior can be clearly demonstrated

BATCH_SIZE = 50


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


# Create database connection

def create_connection():

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

    connection = pyodbc.connect(
        connection_string
    )

    logger.info(
        "SQL Server connection successful"
    )

    return connection


# Clean values for SQL Server

def clean_value(value):

    # Convert Pandas missing values to None
    # because SQL Server accepts None as NULL

    if pd.isna(value):

        return None

    # Convert NumPy integer values
    # to normal Python integers

    if isinstance(value, np.integer):

        return int(value)

    # Convert NumPy float values
    # to normal Python floats

    if isinstance(value, np.floating):

        return float(value)

    # Convert NumPy boolean values
    # to normal Python boolean values

    if isinstance(value, np.bool_):

        return bool(value)

    # Convert Pandas Timestamp
    # to Python datetime

    if isinstance(value, pd.Timestamp):

        return value.to_pydatetime()

    return value


# Insert launch record

def insert_launch(
    cursor,
    row
):

    cursor.execute("""
        INSERT INTO dbo.launches_failure_test
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
        clean_value(
            row["launch_id"]
        ),
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
            row["launch_probability"]
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
            row["launcher_configuration_id"]
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


# Run failure scenario

def run_failure_scenario():

    logger.info("=" * 70)
    logger.info(
        "FAILURE SCENARIO TEST STARTED"
    )
    logger.info("=" * 70)

    connection = None
    cursor = None

    try:

        # Read processed launch data

        file_path = (
            PROCESSED_DATA_DIR
            / "launches.csv"
        )

        logger.info(
            f"Reading processed file: {file_path}"
        )

        if not file_path.exists():

            raise FileNotFoundError(
                f"Processed file not found: "
                f"{file_path}"
            )

        df = pd.read_csv(
            file_path
        )

        logger.info(
            f"Total launch records: {len(df)}"
        )

        # At least two batches are required
        # to test commit and rollback behavior

        if len(df) < BATCH_SIZE * 2:

            raise ValueError(
                "At least two batches are required "
                "for the failure scenario."
            )

        # Create database connection

        connection = create_connection()

        cursor = connection.cursor()

        # Use small batches for failure test

        logger.info(
            f"Failure test batch size: {BATCH_SIZE}"
        )

        # Process first batch

        first_batch = df.iloc[
            0:BATCH_SIZE
        ]

        logger.info("=" * 70)
        logger.info(
            "PROCESSING FIRST BATCH"
        )
        logger.info("=" * 70)

        logger.info(
            f"First batch records: "
            f"{len(first_batch)}"
        )

        try:

            for _, row in first_batch.iterrows():

                insert_launch(
                    cursor,
                    row
                )

            # Commit the first batch
            # so these records remain saved

            connection.commit()

            logger.info(
                f"First batch committed successfully: "
                f"{len(first_batch)} records"
            )

        except pyodbc.Error as e:

            # Roll back the first batch
            # if an error occurs

            connection.rollback()

            logger.exception(
                "First batch failed. "
                "First batch rolled back."
            )

            raise

        # Prepare second batch

        second_batch = df.iloc[
            BATCH_SIZE:BATCH_SIZE * 2
        ].copy()

        logger.info("=" * 70)
        logger.info(
            "PREPARING SECOND BATCH"
        )
        logger.info("=" * 70)

        logger.info(
            f"Second batch records: "
            f"{len(second_batch)}"
        )

        # Introduce invalid foreign key

        logger.info(
            "Introducing invalid agency_id "
            "to trigger foreign key failure"
        )

        # Set an agency ID which does not exist
        # so the database should reject the record

        second_batch.iloc[
            0,
            second_batch.columns.get_loc(
                "agency_id"
            )
        ] = 999999999

        logger.info(
            "Invalid agency_id assigned: 999999999"
        )

        # Load second batch

        logger.info("=" * 70)
        logger.info(
            "PROCESSING SECOND BATCH"
        )
        logger.info("=" * 70)

        try:

            for _, row in second_batch.iterrows():

                insert_launch(
                    cursor,
                    row
                )

            # This should not happen
            # because the invalid foreign key
            # should cause an error

            connection.commit()

            logger.error(
                "Second batch unexpectedly committed."
            )

            raise RuntimeError(
                "Failure scenario did not fail as expected."
            )

        except pyodbc.Error as e:

            # Roll back the failed second batch
            # without affecting the first committed batch

            connection.rollback()

            logger.exception(
                "Second batch failed because of "
                "the intentionally invalid foreign key."
            )

            logger.info(
                "Current second batch rolled back."
            )

            logger.info(
                "First batch remains committed."
            )

            logger.info(
                "Failure scenario behaved as expected."
            )

        # Verify rollback result

        logger.info("=" * 70)
        logger.info(
            "VERIFYING FAILURE SCENARIO RESULT"
        )
        logger.info("=" * 70)

        cursor.execute("""
            SELECT COUNT(*)
            FROM dbo.launches_failure_test
        """)

        record_count = cursor.fetchone()[0]

        logger.info(
            f"Records remaining after rollback: "
            f"{record_count}"
        )

        # Only the first batch should remain
        # because the second batch was rolled back

        if record_count == len(first_batch):

            logger.info(
                "ROLLBACK VERIFICATION PASSED"
            )

            logger.info(
                f"Expected records: "
                f"{len(first_batch)}"
            )

            logger.info(
                f"Actual records: "
                f"{record_count}"
            )

        else:

            logger.error(
                "ROLLBACK VERIFICATION FAILED"
            )

            logger.error(
                f"Expected records: "
                f"{len(first_batch)}"
            )

            logger.error(
                f"Actual records: "
                f"{record_count}"
            )

            raise RuntimeError(
                "Rollback verification failed."
            )

    except Exception as e:

        logger.exception(
            f"Failure scenario test failed: {e}"
        )

        raise

    finally:

        # Close database cursor

        if cursor is not None:

            cursor.close()

            logger.info(
                "Database cursor closed"
            )

        # Close database connection

        if connection is not None:

            connection.close()

            logger.info(
                "Database connection closed"
            )

    logger.info("=" * 70)
    logger.info(
        "FAILURE SCENARIO TEST COMPLETED"
    )
    logger.info("=" * 70)


# Program entry point

if __name__ == "__main__":

    run_failure_scenario()