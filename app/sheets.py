# ========================================
# app/sheets.py
# ========================================
"""
Google Sheets helper for the Google-Maps scraper.

Public API
----------
fetch_search_rows()              -> List[dict[str, str]]
append_results(rows: List[dict]) -> int   # number of new rows written
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Set, Tuple

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from . import config

logger = logging.getLogger(__name__)

_SCOPES = ("https://www.googleapis.com/auth/spreadsheets",)
_service = None  # cached API client


# ───────────────────────── low-level helpers ──────────────────────────
def _get_service():
    """Return (and cache) a Google Sheets API service instance."""
    global _service  # pylint: disable=global-statement
    if _service is None:
        creds = Credentials.from_service_account_file(
            str(config.SERVICE_ACCOUNT_FILE), scopes=_SCOPES
        )
        _service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return _service


def _get_sheet_values(sheet_id: str, rng: str) -> List[List[Any]]:
    """Read a range with exponential-back-off."""
    svc = _get_service()
    for attempt in range(3):
        try:
            return (
                svc.spreadsheets()
                .values()
                .get(spreadsheetId=sheet_id, range=rng)
                .execute()
                .get("values", [])
            )
        except HttpError as exc:
            wait = 2**attempt
            logger.warning("Sheets API error (%s) – retrying in %ds", exc.status_code, wait)
            time.sleep(wait)
    logger.error("❌  3 retries exhausted – gave up reading.")
    return []


def _update_sheet_values(sheet_id: str, rng: str, values: List[List[Any]], append=True):
    """Append or overwrite rows with retries."""
    svc = _get_service()
    body = {"values": values}

    call = (
        svc.spreadsheets()
        .values()
        .append(
            spreadsheetId=sheet_id,
            range=rng,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        if append
        else svc.spreadsheets()
        .values()
        .update(
            spreadsheetId=sheet_id,
            range=rng,
            valueInputOption="USER_ENTERED",
            body=body,
        )
    )

    for attempt in range(3):
        try:
            call.execute()
            return
        except HttpError as exc:
            wait = 2**attempt
            logger.warning("Sheets API error (%s) – retrying in %ds", exc.status_code, wait)
            time.sleep(wait)
    logger.error("❌  3 retries exhausted – rows not written.")


def _ensure_output_header() -> None:
    """Ensure first row of *output* tab matches `config.OUTPUT_HEADER`."""
    rng = f"{config.OUTPUT_TAB}!1:1"
    first = _get_sheet_values(config.OUTPUT_SHEET_ID, rng)
    if first and first[0] == config.OUTPUT_HEADER:
        return
    logger.info("ℹ️  Creating/fixing header row in output sheet …")
    _update_sheet_values(config.OUTPUT_SHEET_ID, rng, [config.OUTPUT_HEADER], append=False)


# ───────────────────────── public: read search rows ──────────────────────
def fetch_search_rows() -> List[Dict[str, str]]:
    """Return search parameters (country, city, business_type) from input sheet."""
    rows = _get_sheet_values(config.INPUT_SHEET_ID, f"{config.INPUT_TAB}!A:Z")
    if not rows:
        return []

    header_map = {h.strip(): idx for idx, h in enumerate(rows[0])}
    required = (config.COL_COUNTRY, config.COL_CITY, config.COL_BUSINESS)
    missing = [c for c in required if c not in header_map]
    if missing:
        raise ValueError(f"Missing column(s) in input sheet: {', '.join(missing)}")

    out: List[Dict[str, str]] = []
    for raw in rows[1:]:
        if not any(raw):
            continue
        out.append(
            {
                config.COL_COUNTRY:  raw[header_map[config.COL_COUNTRY]].strip(),
                config.COL_CITY:     raw[header_map[config.COL_CITY]].strip(),
                config.COL_BUSINESS: raw[header_map[config.COL_BUSINESS]].strip(),
            }
        )
    return out


# ───────────────────────── public: append with de-dup ────────────────────
def append_results(rows: List[Dict[str, str]]) -> int:
    """
    Append *unique* rows to the output sheet.

    A duplicate is any row whose `(name.lower(), phone)` matches an existing row.
    """
    if not rows:
        return 0

    _ensure_output_header()

    # 1️⃣  build set of existing keys
    existing_vals = _get_sheet_values(config.OUTPUT_SHEET_ID, f"{config.OUTPUT_TAB}!A:Z")
    name_idx = config.OUTPUT_HEADER.index("name")
    phone_idx = config.OUTPUT_HEADER.index("phone")

    existing_keys: Set[Tuple[str, str]] = {
        (r[name_idx].strip().lower(), r[phone_idx].strip())
        for r in existing_vals[1:]  # skip header
        if len(r) > phone_idx
    }

    # 2️⃣  filter incoming rows
    uniques: List[Dict[str, str]] = []
    for r in rows:
        key = (r["name"].strip().lower(), r["phone"].strip())
        if key not in existing_keys:
            existing_keys.add(key)
            uniques.append(r)

    if not uniques:
        return 0

    # 3️⃣  convert + batch write (≤500 / call)
    def to_row(d: Dict[str, str]) -> List[str]:
        return [d.get(col, "") for col in config.OUTPUT_HEADER]

    CHUNK = 500
    written = 0
    for start in range(0, len(uniques), CHUNK):
        chunk_vals = [to_row(r) for r in uniques[start : start + CHUNK]]
        _update_sheet_values(
            config.OUTPUT_SHEET_ID, config.OUTPUT_TAB, chunk_vals, append=True
        )
        written += len(chunk_vals)

    return written
