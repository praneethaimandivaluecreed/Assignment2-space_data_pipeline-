import logging
import os


# ============================================================
# CREATE LOG DIRECTORY
# ============================================================

os.makedirs("logs", exist_ok=True)


# ============================================================
# LOGGER CONFIGURATION
# ============================================================

LOG_FILE = "logs/pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)


logger = logging.getLogger("space_pipeline")