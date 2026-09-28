import subprocess
import sys

from logger import logger


# Run pipeline step

def run_step(script_name):
    """
    Run one pipeline script and stop the pipeline if it fails.
    """

    logger.info("=" * 70)
    logger.info(
        f"STARTING: {script_name}"
    )
    logger.info("=" * 70)

    # Run the script using the same Python
    # interpreter that is running this pipeline

    result = subprocess.run(
        [sys.executable, script_name],
        check=False
    )

    # Stop the pipeline if the current step fails

    if result.returncode != 0:

        logger.error("=" * 70)
        logger.error(
            f"PIPELINE FAILED: {script_name}"
        )
        logger.error(
            f"Return code: {result.returncode}"
        )
        logger.error("=" * 70)

        sys.exit(result.returncode)

    logger.info("=" * 70)
    logger.info(
        f"COMPLETED: {script_name}"
    )
    logger.info("=" * 70)


# Main pipeline

def main():

    logger.info("=" * 70)
    logger.info(
        "SPACE DATA ETL PIPELINE STARTED"
    )
    logger.info("=" * 70)

    # Run extraction first
    # This gets the data from the source

    run_step("extract.py")

    # Run transformation after extraction
    # This cleans and prepares the extracted data

    run_step("transform.py")

    # Run loading after transformation
    # This loads the processed data into SQL Server

    run_step("load.py")

    # All pipeline steps completed successfully

    logger.info("=" * 70)
    logger.info(
        "SPACE DATA ETL PIPELINE COMPLETED SUCCESSFULLY"
    )
    logger.info("=" * 70)


# Program entry point

if __name__ == "__main__":
    main()