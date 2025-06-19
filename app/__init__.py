"""
Google Maps Scraper package
===========================

Importing ``app`` sets up sane logging defaults and exposes a one‑liner
``run()`` helper so you can do:

>>> from app import run
>>> run()  # reads config and starts scraping

The actual scraping entry‑point lives in :pymod:`app.main`.
Configuration comes from :pymod:`app.config` (env‑override friendly).
"""
from __future__ import annotations

import logging
from importlib.metadata import PackageNotFoundError, version as _pkg_version

# ---------------------------------------------------------------------------
# Package metadata
# ---------------------------------------------------------------------------
try:
    __version__: str = _pkg_version(__name__)
except PackageNotFoundError:  # editable / source checkout
    __version__ = "0.1.0.dev0"

# ---------------------------------------------------------------------------
# Logging setup – tweak as needed in `app.config`
# ---------------------------------------------------------------------------
_default_log_format = "% (asctime)s %(levelname)-8s | %(name)s: %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s | %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=False,
)

# Silence overly‑chatty noisy modules; comment out if troubleshooting
for _noisy in ("urllib3", "selenium", "googleapiclient.discovery", "httpx"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
from .main import run  # noqa: E402  (import after logging set‑up)

__all__: list[str] = [
    "run",
    "__version__",
]
