# ========================================
# app/maps_scraper.py
# ========================================
"""
Google-Maps click-through scraper

• Gets the business *name* from the list-panel card
  (div.fontBodyMedium > div.fontHeadlineSmall).
• Clicks card → grabs website, phone, address, reviews.
"""

from __future__ import annotations

import random
import time
import urllib.parse
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import selectors as S
from .parsers import find_first_email
from .utils import human_delay, wait_for_element


# ───────────────────────── helpers ──────────────────────────
def _detail_by_aria(drv: WebDriver, prefix: str, retries: int = 3) -> str:
    for _ in range(retries):
        try:
            el = drv.find_element(By.CSS_SELECTOR, f'*[aria-label^="{prefix}"]')
            return el.get_attribute("aria-label").replace(prefix, "").strip()
        except (NoSuchElementException, StaleElementReferenceException):
            time.sleep(0.4)
    return ""


def _fetch_email(url: str) -> str:
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return find_first_email(BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True))
    except Exception:  # noqa: BLE001
        return ""


def _human_type(inp, text: str) -> None:
    for ch in text:
        inp.send_keys(ch)
        time.sleep(random.uniform(0.05, 0.12))


def _scroll_into_view(driver: WebDriver, el) -> None:
    driver.execute_script("arguments[0].scrollIntoView({block:'center'})", el)
    human_delay(0.4, 0.8)


# ───────────────────────── main ──────────────────────────
def scrape_search(
    driver: WebDriver,
    country: str,
    city: str,
    biz_type: str,
    max_results: int | None = None,
) -> List[Dict[str, Any]]:
    # 1. open map (English UI)
    driver.get(
        "https://www.google.com/maps/place/"
        + urllib.parse.quote_plus(f"{city} {country}")
        + "?hl=en&gl=us"
    )

    # accept cookies if needed
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button/div[normalize-space()='Accept all']"))
        ).click()
        human_delay()
    except Exception:
        pass

    # 2. type query
    box = wait_for_element(driver, By.ID, "searchboxinput")
    box.clear()
    _human_type(box, biz_type)
    box.send_keys(Keys.ENTER)
    human_delay(1.2, 2.0)

    # 3. iterate result cards
    panel = wait_for_element(driver, By.XPATH, S.RESULTS_PANEL_XPATH)
    rows: List[Dict[str, Any]] = []
    seen_titles: set[str] = set()
    idx = 0

    while True:
        cards = panel.find_elements(By.CSS_SELECTOR, S.RESULT_CONTAINER_CSS)

        if idx >= len(cards):
            prev = len(cards)
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", panel)
            human_delay()
            cards = panel.find_elements(By.CSS_SELECTOR, S.RESULT_CONTAINER_CSS)
            if len(cards) == prev:
                break
            continue

        card = cards[idx]
        idx += 1

        # --- name from list-pane card --------------------
        try:
            title = card.find_element(
                By.CSS_SELECTOR,
                "div.fontBodyMedium div.fontHeadlineSmall, div.fontHeadlineSmall",
            ).text.strip()
        except NoSuchElementException:
            continue

        if not title or title.lower() == "results" or title in seen_titles:
            continue
        seen_titles.add(title)
        name = title  # <-- this is what we will save

        # click card
        try:
            _scroll_into_view(driver, card)
            ActionChains(driver).move_to_element(card).pause(0.2).click().perform()
        except StaleElementReferenceException:
            continue

        # wait a moment for details to load
        time.sleep(0.6)

        # scrape other fields (name stays as list title)
        address = _detail_by_aria(driver, S.ADDRESS_ARIA_PREFIX)
        phone   = _detail_by_aria(driver, S.PHONE_ARIA_PREFIX)
        website = _detail_by_aria(driver, S.WEBSITE_ARIA_PREFIX)

        # rating + reviews
        rating_text = ""
        for _ in range(3):
            try:
                rating  = driver.find_element(
                    By.CSS_SELECTOR, f"*[aria-label$='{S.RATING_ARIA_SUFFIX}']"
                ).get_attribute("aria-label")
                reviews = driver.find_element(
                    By.CSS_SELECTOR, f"*[aria-label$='{S.REVIEWS_ARIA_SUFFIX}']"
                ).get_attribute("aria-label")
                rating_text = f"{reviews} {rating}"
                break
            except (NoSuchElementException, StaleElementReferenceException):
                time.sleep(0.4)

        email = _fetch_email(website) if website else ""

        rows.append(
            {
                "country": country,
                "city": city,
                "business_type": biz_type,
                "name": name,
                "email": email,
                "website": website,
                "phone": phone,
                "reviews": rating_text,
                "address": address,
                "maps_url": driver.current_url,
            }
        )

        human_delay(4.0, 5.0)

        # refocus list panel
        try:
            panel.click()
        except Exception:
            panel = wait_for_element(driver, By.XPATH, S.RESULTS_PANEL_XPATH)

        if max_results and len(rows) >= max_results:
            break

    return rows
