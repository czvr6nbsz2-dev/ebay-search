"""Marktplaats-zoekopdracht via het interne JSON-endpoint.

De vorige versie las CSS-klassen uit de HTML (.hz-Listing etc.). Die brak
zodra Marktplaats zijn opmaak wijzigde en leverde daarna stilzwijgend rijen
met title=None, price=None op. Het lrp/api/search-endpoint geeft
gestructureerde JSON terug en is daarmee een stuk minder breekbaar.

Levert dezelfde velden als normalize_items(), plus "description" zodat de
gebrekcontrole er direct op kan draaien zonder extra verzoek.
"""

import time

import requests

BASE_URL = "https://www.marktplaats.nl"
SEARCH_API = f"{BASE_URL}/lrp/api/search"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
}


def _price_eur(listing):
    info = listing.get("priceInfo") or {}
    cents = info.get("priceCents")
    if isinstance(cents, (int, float)) and cents > 0:
        return round(cents / 100.0, 2)
    return None


def _url(listing):
    vip = listing.get("vipUrl") or ""
    if vip.startswith("http"):
        return vip
    if vip:
        return BASE_URL + vip
    item_id = listing.get("itemId")
    return f"{BASE_URL}/v/{item_id}" if item_id else None


def _seller(listing):
    info = listing.get("sellerInformation") or {}
    return info.get("sellerName"), info.get("isVerifiedSeller")


def search_marktplaats(query, limit=30):
    """Geeft (resultaten, diagnose) terug.

    diagnose is None bij succes, en anders een korte tekst die zegt wat er
    wél terugkwam — zodat een mislukking zichtbaar wordt in de output in
    plaats van als lege lijst te verdwijnen.
    """
    try:
        response = requests.get(
            SEARCH_API,
            headers=HEADERS,
            params={"query": query, "limit": limit, "offset": 0},
            timeout=25,
        )
    except Exception as e:
        return [], f"verzoek mislukt: {type(e).__name__}: {str(e)[:120]}"

    if response.status_code != 200:
        return [], f"HTTP {response.status_code} ({len(response.text)} tekens terug)"

    try:
        data = response.json()
    except ValueError:
        return [], f"geen JSON; begint met {response.text[:120]!r}"

    listings = data.get("listings")
    if listings is None:
        return [], f"geen 'listings' in JSON; sleutels: {sorted(data)[:12]}"

    results = []
    for listing in listings:
        seller_name, verified = _seller(listing)
        results.append({
            "source": "marktplaats",
            "region": "Marktplaats",
            "title": listing.get("title"),
            "price": _price_eur(listing),
            "currency": "EUR",
            "condition": None,
            "seller": seller_name,
            "seller_feedback": "geverifieerd" if verified else "particulier",
            "location": "NL",
            "city": (listing.get("location") or {}).get("cityName"),
            "url": _url(listing),
            "description": " ".join(filter(None, [
                listing.get("title"),
                listing.get("description"),
                listing.get("categorySpecificDescription"),
            ])),
        })

    if not results:
        return [], f"0 resultaten (totaal gemeld: {data.get('totalResultCount')})"
    return results, None


def search_many(queries, limit=30, pause=1.0):
    """Meerdere zoektermen, met een pauze ertussen."""
    all_results, notes = [], []
    for query in queries:
        results, problem = search_marktplaats(query, limit=limit)
        notes.append((query, len(results), problem))
        all_results.extend(results)
        time.sleep(pause)
    return all_results, notes
