"""Kleinanzeigen.de (voorheen eBay Kleinanzeigen) — Duitse particulieren.

Geen open API, dus dit leest de zoekpagina. Eerdere poging zocht op
klassenamen (article.aditem, .text-module-begin) en vond wel blokken maar
geen titels: die namen kloppen niet meer.

Deze versie hangt aan het enige dat structureel vastligt — elke advertentie
linkt naar /s-anzeige/ — en leidt titel, prijs en plaats af uit het blok
eromheen. Mislukt dat alsnog, dan rapporteert hij de werkelijke structuur
van het eerste blok, zodat één draai genoeg is om het recht te zetten.
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
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
}
# Zonder toestemmingscookie serveert Kleinanzeigen een consent-pagina.
COOKIES = {"gdpr-consent": "1", "ccpa-notice-viewed-02": "true"}

# Alleen een punt als duizendtalscheiding. Met een spatie erbij leest
# "HN-3 450,00 €" als 3450 in plaats van 450.
_PRICE = re.compile(r"(\d{1,3}(?:\.\d{3})*|\d+)(?:,(\d{2}))?\s*€")
_WS = re.compile(r"\s+")


def _parse_price(text):
    if not text:
        return None
    match = _PRICE.search(text.replace("\xa0", " "))
    if not match:
        return None
    whole = match.group(1).replace(".", "")
    try:
        return float(f"{whole}.{match.group(2) or '00'}")
    except ValueError:
        return None


def _clean(text):
    return _WS.sub(" ", text or "").strip()


def _block_for(anchor):
    """Het advertentieblok rond een /s-anzeige/-link.

    Het <li>-blok gaat vóór het <article>-blok: de prijs staat bij
    Kleinanzeigen soms buiten het article maar wel binnen het lijstitem.
    """
    block = anchor.find_parent("li") or anchor.find_parent("article")
    if block is not None:
        return block
    parent = anchor.parent
    for _ in range(3):
        if parent is None or parent.name in ("body", "html"):
            break
        parent = parent.parent
    return parent or anchor


def search_kleinanzeigen(query, limit=30):
    """Geeft (resultaten, diagnose) terug."""
    slug = urllib.parse.quote(query.strip().replace(" ", "-"))
    url = f"{BASE_URL}/s-{slug}/k0"
    try:
        response = requests.get(
            url, headers=HEADERS, cookies=COOKIES, timeout=25
        )
    except Exception as e:
        return [], f"verzoek mislukt: {type(e).__name__}: {str(e)[:120]}"

    if response.status_code != 200:
        return [], f"HTTP {response.status_code} ({len(response.text)} tekens terug)"

    soup = BeautifulSoup(response.text, "html.parser")
    anchors = soup.select('a[href*="/s-anzeige/"]')
    if not anchors:
        text = _clean(soup.get_text(" "))[:200]
        return [], f"geen /s-anzeige/-links op de pagina; tekst begint met {text!r}"

    results, seen = [], set()
    for anchor in anchors:
        href = anchor.get("href") or ""
        if href.startswith("/"):
            href = BASE_URL + href
        key = href.split("?")[0]
        if key in seen:
            continue

        block = _block_for(anchor)
        block_text = _clean(block.get_text(" "))

        title = _clean(anchor.get_text(" "))
        if not title:
            heading = block.find(["h2", "h3"])
            title = _clean(heading.get_text(" ")) if heading else ""
        if not title or len(title) < 6:
            continue

        seen.add(key)
        results.append({
            "source": "kleinanzeigen",
            "region": "Kleinanzeigen",
            "title": title,
            "price": _parse_price(block_text),
            "currency": "EUR",
            "condition": None,
            "seller": None,
            "seller_feedback": "particulier",
            "location": "DE",
            "city": None,
            "url": key or None,
            "description": block_text[:1200],
        })
        if len(results) >= limit:
            break

    if not results:
        first = _block_for(anchors[0])
        structure = f"<{first.name} class={first.get('class')}>"
        return [], (
            f"{len(anchors)} links gevonden maar geen bruikbare titels; "
            f"eerste blok: {structure} tekst={_clean(first.get_text(' '))[:120]!r}"
        )
    return results, None


def search_many(queries, limit=30, pause=1.5):
    all_results, notes = [], []
    for query in queries:
        results, problem = search_kleinanzeigen(query, limit=limit)
        notes.append((query, len(results), problem))
        all_results.extend(results)
        time.sleep(pause)
    return all_results, notes
