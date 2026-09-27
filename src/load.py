import os
from pathlib import Path

import pandas as pd
import pyodbc
from dotenv import load_dotenv

from logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_DATA_DIR = (
    PROJECT_ROOT / "data" / "processed"
)

# Number of records processed in one transaction
BATCH_SIZE = 500


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(
    PROJECT_ROOT / ".env"
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_DRIVER = os.getenv("DB_DRIVER")
DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_TRUSTED_CONNECTION = os.getenv(
    "DB_TRUSTED_CONNECTION"
)
DB_TRUST_SERVER_CERTIFICATE = os.getenv(
    "DB_TRUST_SERVER_CERTIFICATE"
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

    return pd.read_csv(
        file_path
    )


# ============================================================
# VALIDATE DATABASE CONFIGURATION
# ============================================================

def validate_database_configuration():

    logger.info(
        "Validating database configuration"
    )

    required_variables = {
        "DB_DRIVER": DB_DRIVER,
        "DB_SERVER": DB_SERVER,
        "DB_DATABASE": DB_DATABASE,
        "DB_TRUSTED_CONNECTION":
            DB_TRUSTED_CONNECTION,
        "DB_TRUST_SERVER_CERTIFICATE":
            DB_TRUST_SERVER_CERTIFICATE
    }

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


# ============================================================
# CREATE DATABASE CONNECTION
# ============================================================

def create_connection():

    validate_database_configuration()

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


# ============================================================
# CREATE TARGET TABLES
# ============================================================

def create_tables(connection):

    logger.info(
        "Checking/creating target tables"
    )

    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # AGENCIES
        # ----------------------------------------------------

        cursor.execute("""
            IF OBJECT_ID('dbo.agencies', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.agencies
                (
                    agency_id INT NOT NULL PRIMARY KEY,
                    agency_name NVARCHAR(255) NOT NULL,
                    abbreviation NVARCHAR(100),
                    agency_type NVARCHAR(255),
                    country NVARCHAR(255),
                    founding_year INT
                )
            END
        """)

        # ----------------------------------------------------
        # LAUNCHER CONFIGURATIONS
        # ----------------------------------------------------

        cursor.execute("""
            IF OBJECT_ID(
                'dbo.launcher_configurations',
                'U'
            ) IS NULL
            BEGIN
                CREATE TABLE dbo.launcher_configurations
                (
                    launcher_configuration_id INT
                        NOT NULL PRIMARY KEY,

                    launcher_name NVARCHAR(255)
                        NOT NULL,

                    full_name NVARCHAR(500),

                    variant NVARCHAR(255),

                    manufacturer_id INT,

                    manufacturer_name NVARCHAR(255),

                    active BIT,

                    reusable BIT
                )
            END
        """)

        # ----------------------------------------------------
        # PADS
        # ----------------------------------------------------

        cursor.execute("""
            IF OBJECT_ID('dbo.pads', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.pads
                (
                    pad_id INT NOT NULL PRIMARY KEY,

                    pad_name NVARCHAR(500)
                        NOT NULL,

                    active BIT,

                    latitude FLOAT,

                    longitude FLOAT,

                    country NVARCHAR(255),

                    location_id INT,

                    location_name NVARCHAR(500),

                    total_launch_count INT,

                    orbital_launch_attempt_count INT,

                    fastest_turnaround NVARCHAR(255)
                )
            END
        """)

        # ----------------------------------------------------
        # LAUNCHES
        # ----------------------------------------------------

        cursor.execute("""
            IF OBJECT_ID('dbo.launches', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.launches
                (
                    launch_id NVARCHAR(100)
                        NOT NULL PRIMARY KEY,

                    launch_name NVARCHAR(500)
                        NOT NULL,

                    launch_datetime DATETIMEOFFSET
                        NOT NULL,

                    status_id INT,

                    status_name NVARCHAR(255),

                    launch_probability FLOAT,

                    weather_concerns NVARCHAR(MAX),

                    failure_reason NVARCHAR(MAX),

                    agency_id INT,

                    launcher_configuration_id INT,

                    pad_id INT,

                    mission_name NVARCHAR(500),

                    mission_type NVARCHAR(255),

                    launch_year INT,

                    launch_month INT,

                    is_successful BIT,

                    CONSTRAINT FK_launches_agencies
                        FOREIGN KEY (agency_id)
                        REFERENCES dbo.agencies(agency_id),

                    CONSTRAINT FK_launches_launcher_configurations
                        FOREIGN KEY (
                            launcher_configuration_id
                        )
                        REFERENCES dbo.launcher_configurations(
                            launcher_configuration_id
                        ),

                    CONSTRAINT FK_launches_pads
                        FOREIGN KEY (pad_id)
                        REFERENCES dbo.pads(pad_id)
                )
            END
        """)

        connection.commit()

        logger.info(
            "Target tables are ready"
        )

    except pyodbc.Error as e:

        connection.rollback()

        logger.exception(
            f"Table creation failed: {e}"
        )

        raise

    finally:

        cursor.close()


# ============================================================
# CONVERT VALUE FOR SQL SERVER
# ============================================================

def clean_value(value):

    if pd.isna(value):

        return None

    return value


# ============================================================
# LOAD AGENCIES
# ============================================================

def load_agencies(
    connection,
    df
):

    logger.info("=" * 70)
    logger.info("LOADING: AGENCIES")
    logger.info("=" * 70)

    cursor = connection.cursor()

    insert_count = 0
    update_count = 0

    try:

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

                    agency_id = clean_value(
                        row["agency_id"]
                    )

                    cursor.execute("""
                        SELECT 1
                        FROM dbo.agencies
                        WHERE agency_id = ?
                    """, agency_id)

                    exists = cursor.fetchone()

                    if exists:

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

        cursor.close()


# ============================================================
# LOAD LAUNCHER CONFIGURATIONS
# ============================================================

def load_launcher_configurations(
    connection,
    df
):

    logger.info("=" * 70)
    logger.info(
        "LOADING: LAUNCHER CONFIGURATIONS"
    )
    logger.info("=" * 70)

    cursor = connection.cursor()

    insert_count = 0
    update_count = 0

    try:

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
                        row[
                            "launcher_configuration_id"
                        ]
                    )

                    cursor.execute("""
                        SELECT 1
                        FROM dbo.launcher_configurations
                        WHERE launcher_configuration_id = ?
                    """, record_id)

                    exists = cursor.fetchone()

                    if exists:

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


# ============================================================
# LOAD PADS
# ============================================================

def load_pads(
    connection,
    df
):

    logger.info("=" * 70)
    logger.info("LOADING: PADS")
    logger.info("=" * 70)

    cursor = connection.cursor()

    insert_count = 0
    update_count = 0

    try:

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

                    cursor.execute("""
                        SELECT 1
                        FROM dbo.pads
                        WHERE pad_id = ?
                    """, record_id)

                    exists = cursor.fetchone()

                    if exists:

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


# ============================================================
# LOAD LAUNCHES
# ============================================================

def load_launches(
    connection,
    df
):

    logger.info("=" * 70)
    logger.info("LOADING: LAUNCHES")
    logger.info("=" * 70)

    cursor = connection.cursor()

    insert_count = 0
    update_count = 0

    try:

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

                    cursor.execute("""
                        SELECT 1
                        FROM dbo.launches
                        WHERE launch_id = ?
                    """, launch_id)

                    exists = cursor.fetchone()

                    if exists:

                        # ------------------------------------
                        # EXISTING RECORD → UPDATE
                        # ------------------------------------

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

                        # ------------------------------------
                        # NEW RECORD → INSERT
                        # ------------------------------------

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

                # --------------------------------------------
                # COMMIT CURRENT BATCH
                # --------------------------------------------

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

                # --------------------------------------------
                # ROLLBACK CURRENT BATCH ONLY
                # --------------------------------------------

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


# ============================================================
# MAIN LOADING PIPELINE
# ============================================================

def main():

    logger.info("=" * 70)
    logger.info(
        "SPACE DATA LOADING PIPELINE STARTED"
    )
    logger.info("=" * 70)

    connection = None

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

        logger.info(
            "All processed datasets loaded successfully"
        )

        # ----------------------------------------------------
        # CREATE DATABASE CONNECTION
        # ----------------------------------------------------

        connection = create_connection()

        # ----------------------------------------------------
        # CREATE TARGET TABLES
        # ----------------------------------------------------

        create_tables(
            connection
        )

        # ----------------------------------------------------
        # LOAD DIMENSION TABLES FIRST
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # LOAD LAUNCHES
        # ----------------------------------------------------

        load_launches(
            connection,
            launches_df
        )

        # ----------------------------------------------------
        # FINAL SUMMARY
        # ----------------------------------------------------

        logger.info("=" * 70)
        logger.info(
            "SPACE DATA LOADING PIPELINE COMPLETED"
        )
        logger.info("=" * 70)

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

        logger.info("=" * 70)

    except Exception as e:

        logger.exception(
            f"Loading pipeline failed: {e}"
        )

        raise

    finally:

        if connection is not None:

            connection.close()

            logger.info(
                "Database connection closed"
            )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()