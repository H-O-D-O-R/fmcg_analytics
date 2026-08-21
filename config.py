from pathlib import Path


# ============================================================
# PROJECT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# DATABASE
# ============================================================

DB_PATH = (
    BASE_DIR
    / "data"
    / "analytics.db"
)

DB_NAME = "fmcg_analytics"
DB_USER = "postgres"
DB_PASSWORD = "30122020kK+"
DB_HOST = "localhost"
DB_PORT = 5432


# ============================================================
# DATA DIRECTORIES
# ============================================================

DATA_DIR = BASE_DIR / "data"

RAW_DATA_DIR = (
    DATA_DIR / "raw"
)

PROCESSED_DATA_DIR = (
    DATA_DIR / "processed"
)

EXPORTS_DIR = (
    DATA_DIR / "exports"
)


# ============================================================
# VISUALIZATION
# ============================================================

CHARTS_DIR = (
    EXPORTS_DIR / "charts"
)


# ============================================================
# APPLICATION
# ============================================================

APP_NAME = "Business Analytics Service"

APP_VERSION = "1.0.0"

DEBUG = True


# ============================================================
# ANALYTICS DEFAULTS
# ============================================================

DEFAULT_TOP_LIMIT = 10

ABC_A_LIMIT = 0.80

ABC_B_LIMIT = 0.95

RFM_QUANTILES = 5


# ============================================================
# CREATE DIRECTORIES
# ============================================================

for directory in (
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    EXPORTS_DIR,
    CHARTS_DIR,
):
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )