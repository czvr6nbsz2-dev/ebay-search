from openai import OpenAI


def rank_items(items, criteria, user_context=""):
    """
    Beoordeel en rangschik aanbiedingen op basis van opgegeven criteria.
    """

    client = OpenAI()

    system_msg = (
        "Je bent een zeer kritische beoordelaar van fotografiemateriaal. "
        "Je beoordeelt strikt volgens het opgegeven kader en bent expliciet, "
        "terughoudend en concreet in je aanbevelingen."
    )
    if user_context:
        system_msg += f"\n\nFOTOGRAFISCH PROFIEL VAN DE KOPER:\n{user_context}"

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": system_msg,
            },
            {
                "role": "user",
                "content": (
                    "Beoordeel de onderstaande aanbiedingen strikt volgens deze criteria.\n\n"
                    f"CRITERIA:\n{criteria}\n\n"
                    f"AANBIEDINGEN:\n{items}\n\n"
                    "INSTRUCTIES VOOR OUTPUT:\n"
                    "- Negeer en vermeld GEEN aanbiedingen met een totaalscore lager dan 5.0.\n"
                    "- Toon alleen items met score ≥ 5.0.\n"
                    "- Structureer de output in drie secties:\n"
                    "  1. Actief aanbevelen (score ≥ 8.0)\n"
                    "  2. Overwegen bij juiste prijs (score 7.0–7.9)\n"
                    "  3. Overige (score 5.0–6.9, kort en zakelijk)\n"
                    "- Bij elk item altijd expliciet vermelden:\n"
                    "  • Titel van de aanbieding\n"
                    "  • Vraagprijs zoals aangeboden (incl. valuta; indien relevant: eBay/MPB/Marktplaats)\n"
                    "  • Score (1–10)\n"
                    "  • Kort gemotiveerd oordeel (2–3 zinnen)\n"
                    "  • Expliciet oordeel: kopen / overwegen / laten lopen\n"
                    "  • DIRECTE LINK naar de aanbieding (URL)\n"
                    "- Wees streng: liever te weinig dan te veel aanbevelingen.\n"
                    "- Focus op concreet aangeboden items, geen algemene beschouwingen."
                )
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
