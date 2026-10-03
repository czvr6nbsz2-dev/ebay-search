"""Kleinanzeigen.de (voorheen eBay Kleinanzeigen) — Duitse particulieren.

Kleinanzeigen heeft geen open API, dus dit leest de zoekpagina. Net als bij
Marktplaats geldt: bij een opmaakwijziging mag dit niet stilzwijgend een lege
lijst opleveren, dus elke mislukking komt als diagnose terug.
"""

import re
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.kleinanzeigen.de"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

_PRICE = re.compile(r"([\d.]+)\s*€")


def _parse_price(text):
    if not text:
        return None
    match = _PRICE.search(text.replace("\xa0", " "))
    if not match:
        return None
    try:
        return float(match.group(1).replace(".", ""))
    except ValueError:
        return None


def _first_text(node, selectors):
    for selector in selectors:
        found = node.select_one(selector)
        if found:
            text = found.get_text(" ", strip=True)
            if text:
                return text
    return None


def search_kleinanzeigen(query, limit=30):
    """Geeft (resultaten, diagnose) terug."""
    url = f"{BASE_URL}/s-{urllib.parse.quote_plus(query.replace(' ', '-'))}/k0"
    try:
        response = requests.get(url, headers=HEADERS, timeout=25)
    except Exception as e:
        return [], f"verzoek mislukt: {type(e).__name__}: {str(e)[:120]}"

    if response.status_code != 200:
        return [], f"HTTP {response.status_code} ({len(response.text)} tekens terug)"

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("article.aditem") or soup.select("[data-adid]")
    if not articles:
        snippet = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[:160]
        return [], f"geen advertenties gevonden; pagina begint met: {snippet!r}"

    results = []
    for article in articles[:limit]:
        href = article.get("data-href") or ""
        link = article.select_one("a[href]")
        if not href and link:
            href = link.get("href", "")
        if href.startswith("/"):
            href = BASE_URL + href

        title = _first_text(article, [
            ".text-module-begin a", "h2 a", "h2", ".ellipsis",
        ])
        price_text = _first_text(article, [
            ".aditem-main--middle--price-shipping--price",
            ".aditem-main--middle--price",
            "[class*='price']",
        ])
        location = _first_text(article, [
            ".aditem-main--top--left", "[class*='top--left']",
        ])
        description = _first_text(article, [
            ".aditem-main--middle--description", "[class*='description']",
        ])

        results.append({
            "source": "kleinanzeigen",
            "region": "Kleinanzeigen",
            "title": title,
            "price": _parse_price(price_text),
            "currency": "EUR",
            "condition": None,
            "seller": None,
            "seller_feedback": "particulier",
            "location": "DE",
            "city": location,
            "url": href or None,
            "description": " ".join(filter(None, [title, description])),
        })

    parsed = [r for r in results if r["title"]]
    if not parsed:
        return [], f"{len(articles)} blokken gevonden maar geen titels herkend"
    return parsed, None


def search_many(queries, limit=30, pause=1.5):
    all_results, notes = [], []
    for query in queries:
        results, problem = search_kleinanzeigen(query, limit=limit)
        notes.append((query, len(results), problem))
        all_results.extend(results)
        time.sleep(pause)
    return all_results, notes
