import sys
import os
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


def main():
    if len(sys.argv) < 2:
        print("Gebruik: python main.py \"beschrijving van wat je zoekt\"")
        print()
        print("Voorbeelden:")
        print('  python main.py "Nikkor 35mm f/2 AI lens"')
        print('  python main.py "35mm lens voor straatfotografie"')
        print('  python main.py "Nikon D700 body"')
        sys.exit(1)

    description = sys.argv[1]
    context_path = Path(__file__).parent / "user_context.md"
    user_context = context_path.read_text(encoding="utf-8")

    # 1. AI Intake: beschrijving -> zoekspecificatie
    print(f"Zoekopdracht: {description}")
    print("Intake-agent genereert zoekprofiel...\n")
    spec = generate_search_spec(description, user_context)

    print(f"Zoekprofiel: {spec.display_name}")
    print(f"Zoektermen:  {spec.search_queries}")
    print(f"Include:     {spec.include_terms}")
    print(f"Exclude:     {spec.exclude_terms}")
    print(f"eBay cat:    {spec.ebay_category}")
    print()

    # Bevestiging (alleen lokaal, niet in CI)
    if not os.environ.get("CI") and not os.environ.get("GITHUB_ACTIONS"):
        confirm = input("Doorgaan met zoeken? [J/n] ").strip().lower()
        if confirm == "n":
            print("Gestopt.")
            sys.exit(0)

    # 2. Zoeken op eBay en Marktplaats
    all_items = []
    for i, query in enumerate(spec.search_queries, 1):
        print(f"[{i}/{len(spec.search_queries)}] Zoeken: {query}")

        try:
            ebay_raw = search_ebay(query, limit=10, category_id=spec.ebay_category)
            ebay_norm = normalize_items(ebay_raw, source="ebay")
            all_items.extend(ebay_norm)
        except Exception as e:
            print(f"  eBay fout: {e}")

        try:
            mp_raw = search_marktplaats(query)
            mp_norm = normalize_marktplaats(mp_raw)
            all_items.extend(mp_norm)
        except Exception as e:
            print(f"  Marktplaats fout: {e}")

    # 3. Deduplicatie
    unique = deduplicate(all_items)
    print(f"\nGevonden: {len(all_items)} items, {len(unique)} uniek")

    # 4. Filteren
    candidates = filter_items(unique, spec.include_terms, spec.exclude_terms)
    print(f"Na filtering: {len(candidates)} kandidaten\n")

    if not candidates:
        print("Geen kandidaten gevonden na filtering. Probeer een bredere zoekopdracht.")
        sys.exit(0)

    # 5. AI Ranking
    print("AI-ranker beoordeelt kandidaten...\n")
    result = rank_items(candidates, spec.ranking_criteria, user_context)

    # 6. Output
    title = f"{spec.display_name} \u2013 {date.today().isoformat()}"

    if os.environ.get("GITHUB_ACTIONS"):
        from output.github_issue import save_to_github_issue
        save_to_github_issue(title, result)
    else:
        save_to_apple_notes(title, result)
        print(f"Resultaten opgeslagen in Apple Notities: \"{title}\"")


if __name__ == "__main__":
    main()
