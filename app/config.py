# =============================
# app/config.py
# =============================
"""Project-wide configuration.

All values can be overridden via environment variables or a ``.env`` file
placed at the repository root.  Nothing here should require code changes once
the scraper is running in production.

Example ``.env``::

    # Google Sheets
    INPUT_SHEET_ID=1abc...xyz
    OUTPUT_SHEET_ID=1def...uvw
    INPUT_TAB=SearchJobs
    OUTPUT_TAB=Scraped

    # Chrome debugging port
    CDP_PORT=9223

    # Logging
    LOG_LEVEL=DEBUG
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

try:
    # Optional – only loaded if python-dotenv is installed
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover
    load_dotenv = None

# ---------------------------------------------------------------------------
# Initialise dotenv (if present)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[1]
if load_dotenv:  # pragma: no cover
    dotenv_path = _REPO_ROOT / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=False)

# ---------------------------------------------------------------------------
# Google Sheets
# ---------------------------------------------------------------------------
INPUT_SHEET_ID: Final[str] = os.getenv(
    "INPUT_SHEET_ID", "1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
)
OUTPUT_SHEET_ID: Final[str] = os.getenv(
    "OUTPUT_SHEET_ID", "1yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
)
INPUT_TAB: Final[str] = os.getenv("INPUT_TAB", "Input")
OUTPUT_TAB: Final[str] = os.getenv("OUTPUT_TAB", "Scraped")

# Column names in the *input* sheet
COL_COUNTRY: Final[str] = os.getenv("COL_COUNTRY", "country_name")
COL_CITY: Final[str] = os.getenv("COL_CITY", "city_name")
COL_BUSINESS: Final[str] = os.getenv("COL_BUSINESS", "business_type")

# Expected header for the *output* sheet – order must match rows we append
OUTPUT_HEADER: Final[list[str]] = [
    "country",
    "city",
    "business_type",
    "name",
    "email",
    "website",
    "phone",
    "reviews",
    "address",
    "maps_url",
]

# Service-account key for Google Sheets API
SERVICE_ACCOUNT_FILE: Final[Path] = Path(
    os.getenv("SERVICE_ACCOUNT_FILE", _REPO_ROOT / "credentials" / "service_account.json")
)

# ---------------------------------------------------------------------------
# Chrome / CDP
# ---------------------------------------------------------------------------
CHROME_EXECUTABLE: Final[str | None] = os.getenv("CHROME_EXECUTABLE")  # let Chrome pick default
CDP_HOST: Final[str] = os.getenv("CDP_HOST", "localhost")
CDP_PORT: Final[int] = int(os.getenv("CDP_PORT", "9222"))

# Extra launch flags appended when we spawn Chrome ourselves
CHROME_FLAGS: Final[list[str]] = [
    "--remote-debugging-port={}".format(CDP_PORT),
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
    "--password-store=basic",
    # Uncomment if you need to see every window gymnastics
    # "--auto-open-devtools-for-tabs",
]

# ---------------------------------------------------------------------------
# Human-like delays & timeouts (all in seconds)
# ---------------------------------------------------------------------------
NAVIGATION_TIMEOUT = 20
ELEMENT_WAIT_TIMEOUT = 15
DELAY_RANGE = (2.0, 4.0)  # random.uniform(*DELAY_RANGE) sleeps between actions

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
MAX_RESULTS_PER_SEARCH: Final[int | None] = (
    None
    if os.getenv("MAX_RESULTS_PER_SEARCH") in (None, "", "None")
    else int(os.getenv("MAX_RESULTS_PER_SEARCH"))
)

# Freeze the public namespace – anything not listed below is considered
# private implementation detail.
__all__: list[str] = [
    "INPUT_SHEET_ID",
    "OUTPUT_SHEET_ID",
    "INPUT_TAB",
    "OUTPUT_TAB",
    "COL_COUNTRY",
    "COL_CITY",
    "COL_BUSINESS",
    "OUTPUT_HEADER",
    "SERVICE_ACCOUNT_FILE",
    "CHROME_EXECUTABLE",
    "CDP_HOST",
    "CDP_PORT",
    "CHROME_FLAGS",
    "NAVIGATION_TIMEOUT",
    "ELEMENT_WAIT_TIMEOUT",
    "DELAY_RANGE",
    "LOG_LEVEL",
    "MAX_RESULTS_PER_SEARCH",
]
