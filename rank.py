from openai import OpenAI


def rank_items(items, criteria, user_context=""):
    """
    Output: compacte vergelijkingstabel per regio + kort eindadvies.
    """
    client = OpenAI()

    system_msg = (
        "Je bent een kritische beoordelaar van fotografiemateriaal. "
        "Je produceert een COMPACTE vergelijkingstabel \u2014 geen lange beschouwingen, "
        "alleen feiten en oordelen in tabelvorm."
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
                    "Beoordeel onderstaande aanbiedingen volgens de criteria.\n\n"
                    f"CRITERIA:\n{criteria}\n\n"
                    f"AANBIEDINGEN ({len(items)} items):\n{items}\n\n"
                    "OUTPUT-FORMAT (LETTERLIJK volgen \u2014 niets toevoegen, niets weglaten):\n\n"
                    "## A. JAPAN \u2014 top 5 (incl. ~25% landed)\n\n"
                    "| # | Listing | Vraagprijs | Landed | Score | Oordeel |\n"
                    "|---|---|---|---|---|---|\n"
                    "| 1 | [titel-ingekort](https://volledige-url) | $XXX (~\u20acYYY) | **\u20acZZZ** | S.S | **KOPEN** |\n"
                    "(rijen 2..5 idem; sorteer op landed prijs)\n\n"
                    "## B. EUROPEES CONTINENT \u2014 top 5 (geen import)\n\n"
                    "| # | Listing | Prijs | Score | Oordeel |\n"
                    "|---|---|---|---|---|\n"
                    "| 1 | [titel-ingekort](https://volledige-url) | **\u20acXXX** | S.S | **KOPEN** |\n"
                    "(rijen 2..5 idem; sorteer op prijs/score)\n\n"
                    "## Eindadvies\n\n"
                    "> 2-4 zinnen: welke listing concreet kopen en waarom (regio, "
                    "hoeveel goedkoper, welk risico).\n\n"
                    "REGELS:\n"
                    "- Toon ALTIJD beide regio-secties.\n"
                    "- Per regio max 5 listings.\n"
                    "- Items met score < 3.0: weglaten.\n"
                    "- Locatie buiten Japan en buiten Europees continent: NIET tonen.\n"
                    "- Listing-titel inkorten tot ~55 tekens als nodig, leesbaar laten.\n"
                    "- Japan: vraagprijs in USD met (~\u20acxxx) erbij. Landed = vraagprijs \u00d7 1.25 in EUR, "
                    "koers 1 USD = 0.92 EUR.\n"
                    "- Europa: oorspronkelijke valuta (meestal EUR).\n"
                    "- Oordeel: KOPEN (\u22658.0), OVERWEGEN (7.0\u20137.9), LATEN LOPEN (<7.0). "
                    "Alleen KOPEN in bold.\n"
                    "- GEEN motivatie per regel \u2014 alleen feiten. Motivatie staat in eindadvies-blockquote.\n"
                    "- Als een regio echt leeg is: \u00e9\u00e9n rij '| \u2014 | *Geen geschikte aanbieding "
                    "vandaag.* | | | | |' (passend aantal kolommen)."
                )
            }
        ],
        temperature=0.2
    )
    return response.choices[0].message.content
