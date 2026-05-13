import sys
import os
import traceback
from pathlib import Path
from datetime import date
from dotenv import load_dotenv

load_dotenv()

from intake import generate_search_spec
from sources.ebay import search_ebay
from sources.marktplaats import search_marktplaats
from normalize import normalize_items, normalize_marktplaats
from filter import filter_items
from rank import rank_items
from output.apple_notes import save_to_apple_notes


def deduplicate(items):
    seen = set()
    unique = []
    for item in items:
        url = item.get("url")
        if url and url not in seen:
            seen.add(url)
            unique.append(item)
    return unique


def post(title, body):
    if os.environ.get("GITHUB_ACTIONS"):
        from output.github_issue import save_to_github_issue
        save_to_github_issue(title, body)
    else:
        save_to_apple_notes(title, body)
        print(f"Apple Note aangemaakt: \"{title}\"")


def main():
    if len(sys.argv) < 2:
        print("Gebruik: python main.py \"beschrijving\"")
        sys.exit(1)

    description = sys.argv[1]
    context_path = Path(__file__).parent / "user_context.md"
    user_context = context_path.read_text(encoding="utf-8")

    print(f"Zoekopdracht: {description}")
    spec = generate_search_spec(description, user_context)
    print(f"Zoekprofiel: {spec.display_name}")
    print(f"Zoektermen:  {spec.search_queries}")
    print(f"Include:     {spec.include_terms}")
    print(f"Exclude:     {spec.exclude_terms}")
    print(f"eBay cat:    {spec.ebay_category}\n")

    if not os.environ.get("CI") and not os.environ.get("GITHUB_ACTIONS"):
        confirm = input("Doorgaan met zoeken? [J/n] ").strip().lower()
        if confirm == "n":
            sys.exit(0)

    all_items = []
    pass_stats = []
    ebay_passes = [
        ("Japan", "itemLocationCountry:JP", "EBAY_US"),
        ("Europa", "itemLocationRegion:EUROPE", "EBAY_DE"),
    ]
    for i, query in enumerate(spec.search_queries, 1):
        print(f"[{i}/{len(spec.search_queries)}] Zoeken: {query}")
        for label, region_filter, marketplace in ebay_passes:
            try:
                raw = search_ebay(
                    query, limit=200,
                    category_id=None,
                    region_filter=region_filter,
                    marketplace=marketplace,
                )
                norm = normalize_items(raw, source="ebay")
                print(f"  eBay {label} ({marketplace}): {len(norm)} treffers")
                pass_stats.append((query, label, marketplace, len(norm), None))
                all_items.extend(norm)
            except Exception as e:
                print(f"  eBay {label} fout: {e}")
                pass_stats.append((query, label, marketplace, 0, str(e)))
        try:
            mp_raw = search_marktplaats(query)
            mp_norm = normalize_marktplaats(mp_raw)
            print(f"  Marktplaats: {len(mp_norm)} treffers")
            all_items.extend(mp_norm)
        except Exception as e:
            print(f"  Marktplaats fout: {e}")

    unique = deduplicate(all_items)
    print(f"\nGevonden: {len(all_items)} items, {len(unique)} uniek")

    candidates = filter_items(unique, spec.include_terms, spec.exclude_terms)
    print(f"Na filtering: {len(candidates)} kandidaten\n")

    title = f"{spec.display_name} \u2013 {date.today().isoformat()}"

    if not candidates:
        diag = [
            f"## Geen kandidaten na filtering \u2014 diagnose\n",
            f"**Zoekopdracht:** {description}\n",
            f"**Zoekprofiel:** {spec.display_name}\n",
            f"**eBay categorie:** `{spec.ebay_category}`\n",
            f"**Include terms:** `{spec.include_terms}`\n",
            f"**Exclude terms:** `{spec.exclude_terms}`\n\n",
            f"### Zoektermen \u00e9n treffers per pass\n",
        ]
        for q, label, mp, n, err in pass_stats:
            line = f"- `{q}` \u2192 {label} ({mp}): **{n}** treffers"
            if err:
                line += f" \u26a0\ufe0f {err}"
            diag.append(line + "\n")
        diag.append(f"\n**Totaal ruw:** {len(all_items)} items, {len(unique)} uniek\n\n")
        diag.append("### Voorbeelden van ruwe vondsten (eerste 30 uniek)\n")
        for item in unique[:30]:
            diag.append(
                f"- {item.get('source')} | {item.get('location') or '?'} | "
                f"{item.get('price')} {item.get('currency')} | "
                f"{item.get('title')}\n"
            )
        body = "".join(diag)
        post(title, body)
        sys.exit(0)

    print("AI-ranker beoordeelt kandidaten...\n")
    try:
        result = rank_items(candidates, spec.ranking_criteria, user_context)
        post(title, result)
    except Exception:
        tb = traceback.format_exc()
        body = f"## Ranker-fout\n\n```\n{tb}\n```\n\nAantal kandidaten dat naar ranker ging: {len(candidates)}"
        post(title, body)
        sys.exit(1)


if __name__ == "__main__":
    main()
