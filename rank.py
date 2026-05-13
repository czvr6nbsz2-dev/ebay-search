from openai import OpenAI


def rank_items(items, criteria, user_context=""):
    """
    Beoordeel aanbiedingen en presenteer ze ALTIJD gesplitst per regio
    (Japan vs. Europees continent) zodat de koper kan vergelijken.
    """

    client = OpenAI()

    system_msg = (
        "Je bent een kritische, transparante beoordelaar van fotografiemateriaal. "
        "Je toont niet alleen de absolute winnaar, maar geeft per regio een eerlijke "
        "selectie zodat de koper kan vergelijken. Je bent eerlijk over zwakke en "
        "sterke punten, maar je houdt items uit Japan en Europa NIET buiten beeld "
        "tenzij ze echt onbruikbaar zijn."
    )
    if user_context:
        system_msg += f"\n\nFOTOGRAFISCH PROFIEL VAN DE KOPER:\n{user_context}"

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_msg},
            {
                "role": "user",
                "content": (
                    "Beoordeel de onderstaande aanbiedingen volgens deze criteria.\n\n"
                    f"CRITERIA:\n{criteria}\n\n"
                    f"AANBIEDINGEN ({len(items)} items):\n{items}\n\n"
                    "OUTPUT-FORMAT (VERPLICHT):\n\n"
                    "## A. JAPAN (incl. ~25% importkosten op vraagprijs)\n"
                    "Toon hier de top 5 listings met locatie Japan. Sorteer op "
                    "aantrekkelijkheid (staat \u00d7 landed prijs \u00d7 verkopersbetrouwbaarheid).\n\n"
                    "## B. EUROPEES CONTINENT (geen importkosten)\n"
                    "Toon hier de top 5 listings met locatie in Europa (EU + UK + CH + NO etc.). "
                    "Sorteer op aantrekkelijkheid.\n\n"
                    "REGELS PER LISTING:\n"
                    "- Negeer items met locatie buiten Japan en buiten Europees continent.\n"
                    "- Minimumscore voor opname: 3.0/10. Items < 3.0 weglaten.\n"
                    "- Per listing tonen:\n"
                    "  \u2022 Titel\n"
                    "  \u2022 Vraagprijs incl. valuta (en bron, bv. eBay)\n"
                    "  \u2022 Locatie (landcode)\n"
                    "  \u2022 Score 1\u201310\n"
                    "  \u2022 Voor JAPAN ook: landed-prijs in EUR (vraagprijs \u00d7 1.25)\n"
                    "  \u2022 Korte motivatie (2-3 zinnen)\n"
                    "  \u2022 Oordeel: KOPEN / OVERWEGEN / LATEN LOPEN\n"
                    "  \u2022 Directe URL\n\n"
                    "SLUIT AF MET een sectie:\n"
                    "## Vergelijking & advies\n"
                    "3-5 regels: welke regio biedt op dit moment de beste kandidaat, "
                    "hoe groot het landed prijsverschil is, en wat je concreet aanraadt.\n\n"
                    "BELANGRIJK: toon ALTIJD beide regio-secties \u2014 ook als een regio "
                    "maar 1-2 listings heeft die de drempel halen. Als een regio echt "
                    "leeg is, schrijf dan 'Geen geschikte aanbiedingen in deze regio op "
                    "dit moment.' en leg in 1 zin uit waarom (te duur, geen treffers, "
                    "alleen defecte items, etc.). Liever eerlijk en breed dan superkort."
                )
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
