import requests
import json
import time
from pathlib import Path

from logger import logger


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "https://ll.thespacedevs.com/2.3.0"

ENDPOINTS = {
    "launches": "launches/",
    "launcher_configurations": "launcher_configurations/",
    "agencies": "agencies/",
    "pads": "pads/"
}

# Project root/data/raw
RAW_DATA_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
)

# Maximum records requested in one API call
# API allows maximum 100 records per request
PAGE_LIMIT = 100

# Extraction strategy
# None = retrieve all available pages
# Number = retrieve only that many pages
MAX_PAGES = {
    "launches": 2,
    "launcher_configurations": None,
    "agencies": None,
    "pads": None
}

# Request timeout in seconds
TIMEOUT = 30

# Maximum retry attempts
MAX_RETRIES = 3

# HTTP status codes that may represent temporary failures
RETRY_STATUS_CODES = {
    429,  # Too Many Requests
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504   # Gateway Timeout
}


# ============================================================
# CREATE HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "Accept": "application/json"
})


# ============================================================
# EXTRACT ONE ENDPOINT
# ============================================================

def extract_endpoint(name, endpoint):

    logger.info("=" * 70)
    logger.info(f"EXTRACTING: {name.upper()}")
    logger.info("=" * 70)

    # Create folder for this endpoint
    output_dir = RAW_DATA_DIR / name
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    logger.info(
        f"Raw data directory: {output_dir}"
    )

    # Maximum pages for this endpoint
    max_pages = MAX_PAGES[name]

    # First API URL
    url = f"{BASE_URL}/{endpoint}"

    page_number = 1
    total_records = 0

    # --------------------------------------------------------
    # PAGINATION LOOP
    # --------------------------------------------------------

    while url and (
        max_pages is None
        or page_number <= max_pages
    ):

        logger.info(
            f"Requesting page {page_number}"
        )

        logger.info(
            f"URL: {url}"
        )

        response = None

        # ----------------------------------------------------
        # RETRY LOOP
        # ----------------------------------------------------

        for attempt in range(
            1,
            MAX_RETRIES + 1
        ):

            try:

                # First request uses the limit parameter.
                # Subsequent requests use the API's "next" URL.
                if page_number == 1:

                    response = session.get(
                        url,
                        params={
                            "limit": PAGE_LIMIT
                        },
                        timeout=TIMEOUT
                    )

                else:

                    response = session.get(
                        url,
                        timeout=TIMEOUT
                    )

                logger.info(
                    f"HTTP Status: {response.status_code}"
                )

                # ------------------------------------------------
                # SUCCESS
                # ------------------------------------------------

                if response.status_code == 200:

                    break

                # ------------------------------------------------
                # RETRYABLE HTTP ERROR
                # ------------------------------------------------

                if response.status_code in RETRY_STATUS_CODES:

                    if attempt < MAX_RETRIES:

                        wait_time = 2 ** (
                            attempt - 1
                        )

                        logger.warning(
                            f"Temporary API error "
                            f"({response.status_code}). "
                            f"Attempt {attempt}/"
                            f"{MAX_RETRIES}."
                        )

                        logger.info(
                            f"Retrying in "
                            f"{wait_time} seconds..."
                        )

                        time.sleep(
                            wait_time
                        )

                        continue

                    raise Exception(
                        f"API request failed after "
                        f"{MAX_RETRIES} attempts. "
                        f"Status: "
                        f"{response.status_code}"
                    )

                # ------------------------------------------------
                # NON-RETRYABLE HTTP ERROR
                # ------------------------------------------------

                response.raise_for_status()

            except requests.exceptions.Timeout:

                logger.warning(
                    f"Request timed out. "
                    f"Attempt {attempt}/"
                    f"{MAX_RETRIES}"
                )

                if attempt == MAX_RETRIES:

                    raise Exception(
                        f"Request timed out after "
                        f"{MAX_RETRIES} attempts."
                    )

                wait_time = 2 ** (
                    attempt - 1
                )

                logger.info(
                    f"Retrying in "
                    f"{wait_time} seconds..."
                )

                time.sleep(
                    wait_time
                )

            except requests.exceptions.RequestException as e:

                logger.exception(
                    f"API request failed: {e}"
                )

                raise Exception(
                    f"API request failed: {e}"
                )

        # --------------------------------------------------------
        # VALIDATE RESPONSE
        # --------------------------------------------------------

        if response is None:

            raise Exception(
                "No response received from API."
            )

        # --------------------------------------------------------
        # CONVERT RESPONSE TO JSON
        # --------------------------------------------------------

        try:

            data = response.json()

        except ValueError:

            raise Exception(
                "API returned a response "
                "that is not valid JSON."
            )

        # --------------------------------------------------------
        # VALIDATE EXPECTED API STRUCTURE
        # --------------------------------------------------------

        if not isinstance(data, dict):

            raise Exception(
                "Unexpected API response format."
            )

        if "results" not in data:

            raise Exception(
                "API response does not contain "
                "'results'."
            )

        # --------------------------------------------------------
        # SAVE RAW RESPONSE
        # --------------------------------------------------------

        output_file = (
            output_dir
            / f"page_{page_number}.json"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False
            )

        logger.info(
            f"Raw data saved to: {output_file}"
        )

        # --------------------------------------------------------
        # RECORD INFORMATION
        # --------------------------------------------------------

        records = data.get(
            "results",
            []
        )

        records_in_page = len(records)

        total_records += records_in_page

        logger.info(
            f"Records in page: "
            f"{records_in_page}"
        )

        logger.info(
            f"Total records retrieved: "
            f"{total_records}"
        )

        # --------------------------------------------------------
        # PAGINATION
        # --------------------------------------------------------

        url = data.get("next")

        if url:

            logger.info(
                "Next page available."
            )

        else:

            logger.info(
                "No more pages available."
            )

        page_number += 1

    # ------------------------------------------------------------
    # EXTRACTION SUMMARY
    # ------------------------------------------------------------

    logger.info(
        f"Extraction completed for {name}."
    )

    logger.info(
        f"Total {name} records retrieved: "
        f"{total_records}"
    )

    return total_records


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    logger.info("=" * 70)
    logger.info(
        "SPACE DATA EXTRACTION PIPELINE STARTED"
    )
    logger.info("=" * 70)

    logger.info(
        f"Raw data directory: {RAW_DATA_DIR}"
    )

    extraction_summary = {}

    # --------------------------------------------------------
    # EXTRACT ALL DATASETS
    # --------------------------------------------------------

    for name, endpoint in ENDPOINTS.items():

        try:

            total_records = extract_endpoint(
                name,
                endpoint
            )

            extraction_summary[name] = (
                total_records
            )

        except Exception as e:

            logger.exception(
                f"ERROR while extracting "
                f"{name}: {e}"
            )

            extraction_summary[name] = 0

            # Continue with remaining datasets
            logger.warning(
                f"Continuing extraction with "
                f"remaining datasets..."
            )

            continue

    # --------------------------------------------------------
    # EXTRACTION SUMMARY
    # --------------------------------------------------------

    logger.info("=" * 70)
    logger.info("EXTRACTION SUMMARY")
    logger.info("=" * 70)

    for name, total_records in (
        extraction_summary.items()
    ):

        logger.info(
            f"{name}: "
            f"{total_records} records"
        )

    logger.info("=" * 70)
    logger.info(
        "SPACE DATA EXTRACTION PIPELINE FINISHED"
    )
    logger.info("=" * 70)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()