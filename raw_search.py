#!/usr/bin/env python3
"""
Ruwe zoektocht zonder AI: haalt eBay-listings op (Japan + Europees continent)
en plaatst ze onbewerkt als GitHub-issue-comment.

Geen OpenAI nodig. De beoordeling gebeurt buiten dit script.

Gebruik:
    python raw_search.py --label "Nikon Coolpix A" \
        --queries "nikon coolpix a,coolpix a 28mm" \
        --include "coolpix a" \
        --exclude "a10,a100,a300,a900,a1000"
"""

import argparse
import os
import re
import sys
from datetime import date

from dotenv import load_dotenv

load_dotenv()

from sources.ebay import search_ebay, get_item_description
from sources import marktplaats, kleinanzeigen, winkels
from normalize import normalize_items
from filter import filter_items
import flaws

# Hoeveel kandidaten hun volledige beschrijving krijgen nagelopen op gebreken.
# Eén extra API-call per item, dus begrensd.
INSPECT_LIMIT = 60

MARKETPLACE_BY_DOMAIN = {
    "ebay.de": "EBAY_DE",
    "ebay.nl": "EBAY_NL",
    "ebay.com": "EBAY_US",
    "ebay.co.uk": "EBAY_GB",
    "ebay.fr": "EBAY_FR",
    "ebay.it": "EBAY_IT",
    "ebay.es": "EBAY_ES",
    "ebay.at": "EBAY_AT",
    "ebay.be": "EBAY_BE",
    "ebay.ie": "EBAY_IE",
}

# Waar de koper woont. deliveryCountry gooit alle aanbiedingen weg die niet
# naar dit land verzenden — zonder dat filter komen er listings terug met
# "Kein Versand nach Niederlande", waar je niets aan hebt.
SHIP_TO = "NL"

# Per pass: (label, eBay-locatiefilter, marketplace)
# Europa wordt via twee marketplaces bevraagd: DE (grootste Europese
# catalogus) en NL (Nederlandse aanbiedingen die niet naar .de doorlopen).
EBAY_PASSES = [
    ("Japan", "itemLocationCountry:JP", "EBAY_US"),
    ("Europa/DE", "itemLocationRegion:EUROPE", "EBAY_DE"),
    ("Europa/NL", "itemLocationRegion:EUROPE", "EBAY_NL"),
]


def with_delivery(region_filter, ship_to=SHIP_TO):
    return f"{region_filter},deliveryCountry:{ship_to}" if ship_to else region_filter


def split_arg(value):
    return [t.strip() for t in (value or "").split(",") if t.strip()]


def marketplace_for(url):
    for domain, mp in MARKETPLACE_BY_DOMAIN.items():
        if domain in (url or ""):
            return mp
    return "EBAY_DE"


EU_COUNTRIES = {
    "DE", "NL", "BE", "FR", "IT", "ES", "AT", "IE", "PT", "PL", "CZ", "SK",
    "SI", "HR", "HU", "RO", "BG", "GR", "FI", "SE", "DK", "EE", "LV", "LT",
    "LU", "MT", "CY",
}

# Ruwe omrekening, alleen om op prijs te kunnen sorteren.
TO_EUR = {"EUR": 1.0, "USD": 0.92, "GBP": 1.16, "JPY": 0.0062, "CHF": 1.05}


def price_value(item):
    """Prijs in euro's. Zonder omrekening sorteert $1099 onder €750, waardoor
    juist de Europese aanbiedingen buiten de gebrekcontrole vielen."""
    try:
        amount = float(item.get("price") or 0)
    except (TypeError, ValueError):
        return 0.0
    return amount * TO_EUR.get(item.get("currency") or "EUR", 1.0)


def inspect_priority(item):
    """EU eerst, daarna op prijs: binnen de EU koopt de gebruiker zonder
    invoerkosten, dus die aanbiedingen moeten sowieso gecontroleerd zijn."""
    return (0 if (item.get("location") in EU_COUNTRIES) else 1, price_value(item))


def inspect_descriptions(items, limit=INSPECT_LIMIT):
    """Haal per kandidaat de verkopersbeschrijving op en zoek naar gebreken.

    De zoek-API levert alleen titels; "leichter Nebel" of schimmel staat
    uitsluitend in de beschrijving. Zonder deze stap komen zulke exemplaren
    gewoon in de aanbevelingen terecht.
    """
    todo = sorted(items, key=inspect_priority)[:limit]
    eu_count = sum(1 for i in todo if i.get("location") in EU_COUNTRIES)
    print(
        f"\nBeschrijvingen nalopen op gebreken ({len(todo)} van {len(items)}, "
        f"waarvan {eu_count} in de EU)..."
    )
    checked = 0
    for item in todo:
        # Marktplaats en Kleinanzeigen leveren hun tekst al mee; alleen voor
        # eBay is een extra verzoek nodig.
        html = item.get("description")
        if not html:
            legacy_id = item_key(item.get("url"))
            if not legacy_id or not legacy_id.isdigit():
                continue
            try:
                html = get_item_description(legacy_id, marketplace_for(item.get("url")))
            except Exception as e:
                item["flaws"] = f"(ophalen mislukt: {e})"
                continue
        if html is None:
            item["flaws"] = "(geen beschrijving)"
            continue
        found, clean = flaws.scan(html)
        item["flaws"] = flaws.summarize(found, clean)
        item["flaw_detail"] = "; ".join(
            f"{cat}: {frags[0]}" for cat, frags in list(found.items())[:3]
        )
        checked += 1
    print(f"  {checked} beschrijvingen gecontroleerd")
    return items


def item_key(url):
    """eBay hangt per zoekterm andere tracking-parameters aan dezelfde URL,
    dus ontdubbelen gebeurt op het advertentie-ID, niet op de volledige URL."""
    if not url:
        return None
    m = re.search(r"/itm/(\d+)", url)                      # eBay
    if m:
        return m.group(1)
    m = re.search(r"/(m\d{6,})", url)                      # Marktplaats
    if m:
        return m.group(1)
    m = re.search(r"/s-anzeige/[^/]+/(\d{6,})", url)       # Kleinanzeigen
    if m:
        return m.group(1)
    return url.split("?")[0]


def deduplicate(items):
    seen = set()
    unique = []
    for item in items:
        key = item_key(item.get("url"))
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def collect(queries, region_passes=EBAY_PASSES):
    items = []
    stats = []
    for query in queries:
        for label, region_filter, marketplace in region_passes:
            try:
                raw = search_ebay(
                    query,
                    limit=200,
                    category_id=None,
                    region_filter=with_delivery(region_filter),
                    marketplace=marketplace,
                )
                norm = normalize_items(raw, source="ebay")
                for n in norm:
                    n["region"] = label
                items.extend(norm)
                stats.append((query, label, len(norm), None))
                print(f"  {query} -> {label}: {len(norm)} treffers")
            except Exception as e:
                stats.append((query, label, 0, str(e)))
                print(f"  {query} -> {label}: FOUT {e}", file=sys.stderr)

    # Particuliere advertentiesites: geen veiling, vaak scherper geprijsd, maar
    # ook geen kopersbescherming. Een mislukking mag niet als lege lijst
    # verdwijnen, dus de diagnose gaat mee in de statistieken.
    for module, label in ((marktplaats, "Marktplaats"),
                          (kleinanzeigen, "Kleinanzeigen"),
                          (winkels, "Winkels")):
        try:
            found, notes = module.search_many(queries)
            items.extend(found)
            for query, count, problem in notes:
                stats.append((query, label, count, problem))
                print(f"  {query} -> {label}: {count} treffers"
                      + (f" ⚠️ {problem}" if problem else ""))
        except Exception as e:
            stats.append(("(alle termen)", label, 0, f"{type(e).__name__}: {e}"))
            print(f"  {label}: FOUT {e}", file=sys.stderr)

    return items, stats


def render(label, queries, include_terms, exclude_terms, stats, items):
    lines = [
        f"# RUWE LISTINGS — {label}",
        "",
        f"**Datum:** {date.today().isoformat()}  ",
        f"**Zoektermen:** `{queries}`  ",
        f"**Include:** `{include_terms}`  ",
        f"**Exclude:** `{exclude_terms}`  ",
        f"**Verzendt naar:** `{SHIP_TO}` (aanbiedingen zonder verzending hierheen zijn weggelaten)  ",
        f"**Aantal na filtering:** {len(items)}",
        "",
        "## Treffers per pass",
        "",
    ]
    for query, region, count, err in stats:
        line = f"- `{query}` → {region}: **{count}**"
        if err:
            line += f" ⚠️ {err}"
        lines.append(line)

    lines += [
        "", "## Listings", "",
        "| Regio | Land | Prijs | Staat | Verkoper | FB% | Gebreken (uit beschrijving) | Titel | URL |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for i in items:
        title = (i.get("title") or "").replace("|", "/")
        url = (i.get("url") or "").split("?")[0]  # tracking-parameters eraf
        flaw = (i.get("flaws") or "niet gecontroleerd").replace("|", "/")
        lines.append(
            f"| {i.get('region') or '?'} "
            f"| {i.get('location') or '?'} "
            f"| {i.get('price') or '?'} {i.get('currency') or ''} "
            f"| {i.get('condition') or '?'} "
            f"| {i.get('seller') or '?'} "
            f"| {i.get('seller_feedback') or '?'} "
            f"| {flaw} "
            f"| {title} "
            f"| {url} |"
        )

    if not items:
        lines.append("| — | — | — | — | — | — | — | *Geen listings na filtering* | — |")

    detail = [i for i in items if i.get("flaw_detail")]
    if detail:
        lines += ["", "## Gevonden gebreken — letterlijke fragmenten", ""]
        for i in detail:
            lines.append(
                f"- **{(i.get('title') or '')[:70]}** — {i['flaw_detail'][:300]}"
            )

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "spec",
        nargs="?",
        help='Alles-in-een: "label || query1, query2 || include1 || exclude1, exclude2"',
    )
    parser.add_argument("--label")
    parser.add_argument("--queries", help="komma-gescheiden")
    parser.add_argument("--include", default="", help="komma-gescheiden (OR)")
    parser.add_argument("--exclude", default="", help="komma-gescheiden")
    args = parser.parse_args()

    if args.spec:
        parts = [p.strip() for p in args.spec.split("||")]
        parts += [""] * (4 - len(parts))
        label, raw_queries, raw_include, raw_exclude = parts[:4]
    else:
        label = args.label
        raw_queries = args.queries
        raw_include = args.include
        raw_exclude = args.exclude

    if not label or not raw_queries:
        parser.error("label en queries zijn verplicht")

    queries = split_arg(raw_queries)
    include_terms = split_arg(raw_include)
    exclude_terms = split_arg(raw_exclude)

    print(f"Zoeken: {label}")
    all_items, stats = collect(queries)

    unique = deduplicate(all_items)
    filtered = filter_items(unique, include_terms, exclude_terms)
    print(f"\n{len(all_items)} ruw, {len(unique)} uniek, {len(filtered)} na filtering")

    inspect_descriptions(filtered)

    body = render(label, queries, include_terms, exclude_terms, stats, filtered)
    title = f"{label} – {date.today().isoformat()}"

    if os.environ.get("GITHUB_ACTIONS"):
        from output.github_issue import save_to_github_issue
        save_to_github_issue(title, body)
    else:
        print(body)


if __name__ == "__main__":
    main()
