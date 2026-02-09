import json
from dataclasses import dataclass
from typing import Optional
from openai import OpenAI


@dataclass
class SearchSpec:
    display_name: str
    search_queries: list
    include_terms: list
    exclude_terms: list
    ebay_category: Optional[str]
    ranking_criteria: str


INTAKE_SYSTEM_PROMPT = """\
Je bent een zoekassistent voor tweedehands fotografiemateriaal.
Je ontvangt een beschrijving van wat de gebruiker zoekt en het fotografisch profiel
van de gebruiker.

Je taak:
1. Genereer 4-10 zoektermen die breed genoeg zijn om alle relevante aanbiedingen
   te vinden op eBay en Marktplaats, maar niet zo breed dat irrelevante items
   meekomen. Gebruik varianten: merk-afkortingen, alternatieve schrijfwijzen,
   gangbare benamingen bij verzamelaars en fotografen.
   BELANGRIJK: vermijd schuine strepen (/) in zoektermen — gebruik bijv.
   "f2" in plaats van "f/2" om URL-problemen te voorkomen.

2. Bepaal include_terms: woorden waarvan minstens één in de titel van een
   aanbieding moet voorkomen (OR-logica). Dit is je grove voorfilter.

3. Bepaal exclude_terms: woorden die een item direct diskwalificeren.
   Wees grondig: denk aan nabijgelegen modellen, andere lichtsterkte-varianten,
   zoom-varianten, defecte items, etc.

4. Bepaal optioneel een eBay-categorie-ID (lenses = "3323", camera bodies = "31388",
   of null als niet van toepassing).

5. Schrijf gedetailleerde beoordelingscriteria voor de AI-ranker.
   Gebruik het fotografisch profiel als context. De criteria moeten bevatten:
   - Wat wordt gezocht en waarom
   - Context van de bestaande uitrusting (duplicaatcheck)
   - Harde afkeur (direct uitsluiten): defecten, schimmel, haze, etc.
   - Sterk negatieve signalen
   - Positieve weging
   - Prijs-context en importkosten (EU vs. buiten EU)
   - Scoringsmodel (totaal 10 punten, verdeeld over 4-5 categorieën)
   - Score-interpretatie (≥8 aanbevelen, 7-7.9 overwegen, <7 laten lopen)
   - Output-instructies per listing (score, motivatie, oordeel, URL)
   Schrijf de criteria in het Nederlands.

Antwoord UITSLUITEND met een geldig JSON-object in dit formaat:
{
  "display_name": "Korte naam voor deze zoekopdracht",
  "search_queries": ["term1", "term2", ...],
  "include_terms": ["woord1", "woord2", ...],
  "exclude_terms": ["woord1", "woord2", ...],
  "ebay_category": "3323" of null,
  "ranking_criteria": "Volledige beoordelingstekst..."
}

Geen uitleg, geen markdown, alleen JSON."""


def generate_search_spec(description, user_context):
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": INTAKE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"FOTOGRAFISCH PROFIEL:\n{user_context}\n\n"
                    f"WAT IK ZOEK:\n{description}"
                ),
            },
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    raw = json.loads(response.choices[0].message.content)

    spec = SearchSpec(
        display_name=raw["display_name"],
        search_queries=raw["search_queries"],
        include_terms=raw["include_terms"],
        exclude_terms=raw["exclude_terms"],
        ebay_category=raw.get("ebay_category"),
        ranking_criteria=raw["ranking_criteria"],
    )

    if len(spec.search_queries) < 3:
        raise ValueError(
            f"Intake genereerde slechts {len(spec.search_queries)} zoektermen — "
            "te weinig voor een betrouwbare zoekopdracht."
        )
    if not spec.include_terms:
        raise ValueError("Intake genereerde geen include_terms — filter ontbreekt.")

    return spec
