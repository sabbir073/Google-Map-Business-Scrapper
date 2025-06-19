# ========================================
# app/selectors.py
# ========================================
"""
Central place for all CSS / XPath selectors used by *maps_scraper.py*.

If Google Maps changes its DOM structure, update anything that breaks here.
"""

# ────────────────────────────────────────────────────────────────────────────
# LIST-VIEW  (left-hand result panel)
# ────────────────────────────────────────────────────────────────────────────
# Scrollable div that holds every result card
RESULTS_PANEL_XPATH = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div'

# Each individual business card inside the panel
RESULT_CONTAINER_CSS = "div.Nv2PK"

# Anchors whose hrefs are direct links to a place page
PLACE_LINKS_CSS = "a[href*='/maps/place']"

# “Back” button shown in detail view that returns to the list
BACK_BUTTON_XPATH = "//button[contains(@aria-label, 'Back')]"

# ────────────────────────────────────────────────────────────────────────────
# DETAIL-VIEW  (after a card is clicked)
# ────────────────────────────────────────────────────────────────────────────
BUSINESS_NAME_TAG = "h1"

# aria-label prefixes that never change in the English UI
ADDRESS_ARIA_PREFIX = "Address:"
PHONE_ARIA_PREFIX = "Phone:"
WEBSITE_ARIA_PREFIX = "Website:"

# aria-label suffix snippets for rating & reviews
RATING_ARIA_SUFFIX = "stars"
REVIEWS_ARIA_SUFFIX = "reviews"

__all__ = [
    "RESULTS_PANEL_XPATH",
    "RESULT_CONTAINER_CSS",
    "PLACE_LINKS_CSS",
    "BACK_BUTTON_XPATH",
    "BUSINESS_NAME_TAG",
    "ADDRESS_ARIA_PREFIX",
    "PHONE_ARIA_PREFIX",
    "WEBSITE_ARIA_PREFIX",
    "RATING_ARIA_SUFFIX",
    "REVIEWS_ARIA_SUFFIX",
]
