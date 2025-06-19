# ========================================
# app/parsers.py
# ========================================
"""
Tiny helpers for pulling e-mail addresses, phone numbers, and review data
out of arbitrary strings scraped from Google Maps or business websites.

Public API
----------
find_first_email(text)             -> str | ""
find_first_phone(text)             -> str | ""
parse_reviews_blob(blob)           -> tuple[str, str]     # (reviews, rating)
"""

from __future__ import annotations

import re
from typing import Tuple

# ---------------------------------------------------------------------------
# Compiled regexes
# ---------------------------------------------------------------------------
_EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+-]+@"                 # local-part
    r"[A-Za-z0-9.-]+\."                   # domain prefix
    r"[A-Za-z]{2,}",                      # TLD
    re.I,
)

# Very permissive phone matcher:   +1 555-123-4567   (555) 123-4567   555.123.4567
_PHONE_RE = re.compile(
    r"""
    (?:\+?\d{1,3}[\s.-]?)?                # optional country code
    (?:\(?\d{2,4}\)?[\s.-]?)?             # optional area code
    \d{2,4}                               # first trunk
    (?:[\s./-]?\d{2,4}){1,3}              # remaining groups
    """,
    re.X,
)

# e.g.  "4.3 (178 reviews)"  or  "178 reviews 4.3 stars"
_REVIEWS_RE = re.compile(r"(\d[\d,]*)\s+reviews?", re.I)
_RATING_RE  = re.compile(r"(\d(?:\.\d)?)\s+stars?", re.I)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
def find_first_email(text: str) -> str:
    """Return the first e-mail in *text* (or empty string)."""
    m = _EMAIL_RE.search(text)
    return m.group(0) if m else ""


def find_first_phone(text: str) -> str:
    """Return the first phone-number-like string in *text* (or empty string)."""
    m = _PHONE_RE.search(text)
    return m.group(0).strip() if m else ""


def parse_reviews_blob(blob: str) -> Tuple[str, str]:
    """Extract `(reviews_count, rating_value)` from a combined blob.

    Parameters
    ----------
    blob : str
        Text such as "4.3 (178 reviews)" or "178 reviews 4.3 stars".

    Returns
    -------
    tuple
        ``(reviews, rating)`` — each as a plain string,
        or ``("", "")`` if not found.
    """
    reviews = _REVIEWS_RE.search(blob)
    rating  = _RATING_RE.search(blob)
    return (
        reviews.group(1).replace(",", "") if reviews else "",
        rating.group(1) if rating else "",
    )


__all__ = [
    "find_first_email",
    "find_first_phone",
    "parse_reviews_blob",
]
