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
import sys
from datetime import date

from dotenv import load_dotenv

load_dotenv()

from sources.ebay import search_ebay
from normalize import normalize_items
from filter import filter_items

EBAY_PASSES = [
    ("Japan", "itemLocationCountry:JP", "EBAY_US"),
    ("Europa", "itemLocationRegion:EUROPE", "EBAY_DE"),
]


def split_arg(value):
    return [t.strip() for t in (value or "").split(",") if t.strip()]


def deduplicate(items):
    seen = set()
    unique = []
    for item in items:
        url = item.get("url")
        if url and url not in seen:
            seen.add(url)
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
                    region_filter=region_filter,
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
    return items, stats


def render(label, queries, include_terms, exclude_terms, stats, items):
    lines = [
        f"# RUWE LISTINGS — {label}",
        "",
        f"**Datum:** {date.today().isoformat()}  ",
        f"**Zoektermen:** `{queries}`  ",
        f"**Include:** `{include_terms}`  ",
        f"**Exclude:** `{exclude_terms}`  ",
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

    lines += ["", "## Listings", "", "| Regio | Land | Prijs | Staat | Verkoper | FB% | Titel | URL |", "|---|---|---|---|---|---|---|---|"]

    for i in items:
        title = (i.get("title") or "").replace("|", "/")
        lines.append(
            f"| {i.get('region') or '?'} "
            f"| {i.get('location') or '?'} "
            f"| {i.get('price') or '?'} {i.get('currency') or ''} "
            f"| {i.get('condition') or '?'} "
            f"| {i.get('seller') or '?'} "
            f"| {i.get('seller_feedback') or '?'} "
            f"| {title} "
            f"| {i.get('url') or ''} |"
        )

    if not items:
        lines.append("| — | — | — | — | — | — | *Geen listings na filtering* | — |")

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

    body = render(label, queries, include_terms, exclude_terms, stats, filtered)
    title = f"{label} – {date.today().isoformat()}"

    if os.environ.get("GITHUB_ACTIONS"):
        from output.github_issue import save_to_github_issue
        save_to_github_issue(title, body)
    else:
        print(body)


if __name__ == "__main__":
    main()
