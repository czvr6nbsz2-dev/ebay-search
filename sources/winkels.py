"""Nederlandse fotowinkels met een webshop.

Deze winkels hebben geen API en draaien op uiteenlopende platforms, dus dit
probeert een paar gangbare zoek-URL's en haalt daarna de productlinks eruit.
Omdat de opmaak per winkel verschilt en zonder waarschuwing verandert,
rapporteert elke mislukking wat de pagina wél was: welke URL werkte, de
paginatitel, het herkende platform en de meest voorkomende klassenamen.
Eén draai is dan genoeg om de selector recht te zetten.

Een nieuwe winkel toevoegen = een regel in SHOPS.
"""

import re
import time
import urllib.parse
from collections import Counter

import requests
from bs4 import BeautifulSoup

SHOPS = [
    {
        "naam": "Fotohandel Delfshaven",
        "base": "https://fotohandeldelfshaven.nl",
        "land": "NL",
        # in volgorde van proberen; {q} wordt vervangen door de zoekterm
        "zoekpaden": [
            "/?s={q}&post_type=product",
            "/?s={q}",
            "/search?q={q}",
            "/zoeken?q={q}",
        ],
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
}

_PRICE = re.compile(r"(?:€|EUR)\s*(\d{1,3}(?:\.\d{3})*|\d+)(?:[,.](\d{2}))?")
# Fotohandel Delfshaven laat verkochte artikelen online staan met "Price: Sold".
# Zonder deze controle lijkt een archief van jaren op actuele voorraad.
_VERKOCHT = re.compile(
    r"\b(sold|verkocht|uitverkocht|out of stock|niet (?:meer )?(?:op )?voorraad|"
    r"nicht verf[üu]gbar|ausverkauft|vendu)\b", re.I)
_WS = re.compile(r"\s+")
_PRODUCT_HREF = re.compile(r"/(product|producten|shop|p|artikel|item)/", re.I)
_PLATFORMS = ["woocommerce", "shopify", "lightspeed", "magento", "prestashop",
              "ccvshop", "myonlinestore", "wp-content"]


def _clean(text):
    return _WS.sub(" ", text or "").strip()


def _price(text):
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


def _blok_met_prijs(anker):
    """Het kleinste blok rond de link dat ook de prijs bevat.

    WooCommerce zet de prijs geregeld buiten het element dat de titel omsluit.
    Daarom klimmen we omhoog tot er een bedrag in beeld komt — maar stoppen
    zodra het blok meer dan één product bevat, anders pikken we de prijs van
    de buurman.
    """
    blok = anker.find_parent(["li", "article"]) or anker.parent or anker
    node = blok
    for _ in range(4):
        if node is None:
            break
        tekst = node.get_text(" ")
        if "€" in tekst or "EUR" in tekst:
            links = {a["href"].split("?")[0].rstrip("/")
                     for a in node.find_all("a", href=True)
                     if _PRODUCT_HREF.search(a["href"])}
            if len(links) <= 1:
                return node
            break
        node = node.parent
    return blok


def _diagnose(soup, url):
    """Wat was dit voor pagina? Genoeg om de volgende poging te richten."""
    titel = _clean(soup.title.get_text()) if soup.title else "(geen titel)"
    html = str(soup)[:40000].lower()
    platform = next((p for p in _PLATFORMS if p in html), "onbekend")
    klassen = Counter()
    for tag in soup.find_all(["a", "article", "div", "li"], class_=True)[:400]:
        for naam in tag.get("class", []):
            if any(w in naam.lower() for w in ("product", "item", "card", "result")):
                klassen[naam] += 1
    top = ", ".join(f"{k}×{v}" for k, v in klassen.most_common(6)) or "geen"
    return f"url={url} titel={titel!r} platform={platform} klassen: {top}"


def _haal_pagina(shop, query):
    """Eerste zoekpad met productlinks erin; anders de laatste geldige pagina.

    Kiezen op paginagrootte werkt niet: een lege-resultatenpagina kan groot
    zijn en een goede klein. Daarom zoeken we naar de productlinks zelf, en
    valt hij terug op de laatste 200-respons zodat de diagnose iets echts te
    bekijken heeft.
    """
    laatste_html = laatste_url = laatste_fout = None
    for pad in shop["zoekpaden"]:
        url = shop["base"] + pad.format(q=urllib.parse.quote_plus(query))
        try:
            response = requests.get(url, headers=HEADERS, timeout=25)
        except Exception as e:
            laatste_fout = f"{url}: {type(e).__name__}: {str(e)[:80]}"
            continue
        if response.status_code != 200:
            laatste_fout = f"{url}: HTTP {response.status_code}"
            continue
        if _PRODUCT_HREF.search(response.text):
            return response.text, url, None
        laatste_html, laatste_url = response.text, url
        laatste_fout = f"{url}: 200 maar geen productlinks"
    if laatste_html is not None:
        return laatste_html, laatste_url, None
    return None, None, laatste_fout


def zoek_winkel(shop, query, limit=25):
    """Geeft (resultaten, diagnose) terug."""
    html, url, probleem = _haal_pagina(shop, query)
    if html is None:
        return [], f"geen bruikbare zoekpagina; laatste poging: {probleem}"

    soup = BeautifulSoup(html, "html.parser")
    ankers = [a for a in soup.find_all("a", href=True)
              if _PRODUCT_HREF.search(a["href"])]
    if not ankers:
        return [], "geen productlinks herkend; " + _diagnose(soup, url)

    resultaten, gezien = [], set()
    verkocht_aantal = 0
    for anker in ankers:
        href = anker["href"]
        if href.startswith("/"):
            href = shop["base"] + href
        sleutel = href.split("?")[0].rstrip("/")
        if sleutel in gezien:
            continue

        blok = _blok_met_prijs(anker)
        bloktekst = _clean(blok.get_text(" "))

        # De link omvat vaak kop én prijs; de kop binnen de link is schoner.
        kop = anker.find(["h2", "h3", "h4"]) or blok.find(["h2", "h3", "h4"])
        titel = _clean(kop.get_text(" ")) if kop else _clean(anker.get_text(" "))
        titel = _PRICE.sub("", titel).strip(" -–—|·,")
        if not titel or len(titel) < 6:
            continue

        gezien.add(sleutel)

        # Verkochte artikelen blijven online staan. Ze horen niet in de
        # resultaten, maar wel in de telling: nul leverbaar is iets anders
        # dan een stukgelopen scraper.
        if _VERKOCHT.search(bloktekst):
            verkocht_aantal += 1
            continue

        resultaten.append({
            "source": "winkel",
            "region": shop["naam"],
            "title": titel,
            "price": _price(bloktekst),
            "currency": "EUR",
            "condition": None,
            "seller": shop["naam"],
            "seller_feedback": "winkel",
            "location": shop["land"],
            "city": None,
            "url": sleutel,
            "description": bloktekst[:1200],
        })
        if len(resultaten) >= limit:
            break

    if not resultaten:
        if verkocht_aantal:
            return [], (f"niets leverbaar: alle {verkocht_aantal} treffers staan "
                        f"als verkocht in de webshop")
        return [], f"{len(ankers)} productlinks maar geen titels; " + _diagnose(soup, url)
    if verkocht_aantal:
        return resultaten, f"(terzijde: {verkocht_aantal} treffers waren al verkocht)"
    return resultaten, None


def search_many(queries, limit=25, pause=1.5):
    alle, notities = [], []
    for shop in SHOPS:
        for query in queries:
            resultaten, probleem = zoek_winkel(shop, query, limit=limit)
            notities.append((query, len(resultaten), probleem))
            alle.extend(resultaten)
            time.sleep(pause)
    return alle, notities
