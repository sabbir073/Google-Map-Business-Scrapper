# ========================================
# app/main.py
# ========================================
"""
CLI entry-point for the Google-Maps business scraper.

Usage
-----
$ python -m app.main                 # run with defaults
$ python -m app.main --max 250       # cap each search at 250 results
$ python -m app.main --log DEBUG     # verbose console logging
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any, Dict, List

from . import config
from . import chrome_control
from . import sheets
from . import maps_scraper
from .utils import human_delay


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:  # noqa: D401
    """Return parsed CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="google-maps-scraper",
        description="Fetches businesses by country / city / type and writes them to Sheets",
    )

    parser.add_argument(
        "--max",
        type=int,
        default=config.MAX_RESULTS_PER_SEARCH,
        help=f"Maximum results per search (default: {config.MAX_RESULTS_PER_SEARCH})",
    )

    parser.add_argument(
        "--log",
        dest="log_level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        default=config.LOG_LEVEL,
        help=f"Console log level (default: {config.LOG_LEVEL})",
    )

    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Main “happy path” pipeline
# ---------------------------------------------------------------------------
def run(max_results_per_search: int | None = None) -> None:
    """End-to-end scraping flow.

    1.  Read rows from the *input* Google Sheet.
    2.  Launch / attach to Chrome (non-headless, CDP).
    3.  For every (country, city, business_type) triple:
        * Search, scroll, and scrape Maps listings.
        * Yield one dict per business with all requested fields.
    4.  Append new rows to the *output* Google Sheet.
    5.  Cleanly shut down Chrome.
    """

    # Read search terms
    search_rows = sheets.fetch_search_rows()  # → List[dict[str, str]]
    if not search_rows:
        logger.warning("ℹ️  Nothing to do – input sheet is empty.")
        return

    # Launch Chrome
    browser = chrome_control.launch_chrome()

    scraped_rows: List[Dict[str, Any]] = []

    # Scrape each search triple
    for row in search_rows:
        country  = row[config.COL_COUNTRY]
        city     = row[config.COL_CITY]
        biz_type = row[config.COL_BUSINESS]

        logger.info("🔍  %-15s | %-15s | %s", country, city, biz_type)

        try:
            results = maps_scraper.scrape_search(
                browser,
                country,
                city,
                biz_type,
                max_results=max_results_per_search,
            )
            scraped_rows.extend(results)

            logger.info("   ↳ %d businesses scraped.", len(results))

        except Exception as exc:  # noqa: BLE001
            logger.exception("❌ Scrape failed for %s / %s / %s – %s", country, city, biz_type, exc)

        # Light “human” pause between searches
        human_delay()

    # Persist to the *output* sheet
    if scraped_rows:
        added = sheets.append_results(scraped_rows)
        logger.info("✅ %d new rows saved to output sheet.", added)
    else:
        logger.warning("⚠️  No data collected – nothing written to sheet.")

    # All done – close Chrome
    chrome_control.close_chrome(browser)


# ---------------------------------------------------------------------------
# Script entry-point
# ---------------------------------------------------------------------------
def main(argv: List[str] | None = None) -> None:
    """Console entry-point registered via ``python -m app.main``."""
    args = _parse_args(argv)

    # Configure root logger *before* importing heavy modules that may log
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    logger.debug("Args: %s", vars(args))

    try:
        run(max_results_per_search=args.max)
    except KeyboardInterrupt:  # Ctrl-C
        logger.warning("👋  Interrupted by user – exiting.")
        sys.exit(130)
    except Exception:  # noqa: BLE001
        logger.exception("💥 Unhandled exception – aborting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
