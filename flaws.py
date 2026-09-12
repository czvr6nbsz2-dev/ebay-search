"""Herken gebreken in een verkopersbeschrijving.

De zoek-API geeft alleen titels. Gebreken als "leichter Nebel", schimmel,
krassen of separatie staan vrijwel altijd alleen in de beschrijving. Deze
module scant die tekst, en houdt rekening met ontkenningen: "kein Nebel"
en "no fungus" zijn juist geruststellend en mogen niet als gebrek tellen.
"""

import re

# gebrek -> woorden die erop wijzen (DE / EN / NL / FR / IT)
FLAW_TERMS = {
    "nevel/haze": [
        "nebel", "neblig", "dunst", "schleier", "milchig", "trüb", "trueb",
        "haze", "hazy", "hazing", "fog", "foggy", "mist",
        "nevel", "waas", "beslagen", "melkachtig",
        "voile", "brume", "velatur", "foschia",
    ],
    "schimmel/fungus": [
        "pilz", "pilzbefall", "schimmel", "fungus", "fungi", "mold", "mould",
        "muffa", "champignon", "moisissure",
    ],
    "krassen": [
        "kratzer", "verkratzt", "scratch", "scratches", "scratched",
        "kras", "krassen", "bekrast", "rayure", "graffio",
    ],
    "stof/deeltjes": [
        "staub", "staubkorn", "staubeinschluss", "dust", "particle",
        "stof", "stofje", "poussière", "polvere",
    ],
    "separatie/coating": [
        "separation", "trennung", "balsam", "coating damage", "beschichtung",
        "delaminat", "putzspuren", "cleaning marks", "wischspuren",
    ],
    "olie op diafragma": [
        "öl", "oel", "oil", "ölig", "oelig", "oily", "olie", "huile",
    ],
    "mechanisch": [
        "klemmt", "hakt", "schwergängig", "schwergaengig", "stiff", "sticky",
        "wackelt", "loose", "spiel", "dent", "delle", "beule",
        "klemt", "stroef",
    ],
    "niet getest": [
        "ungetestet", "nicht getestet", "untested", "not tested",
        "as-is", "as is", "ungeprüft", "ungeprueft", "ongetest",
        "bastler", "for parts",
    ],
}

NEGATIONS = [
    "kein", "keine", "keinen", "keiner", "ohne", "frei von", "freier von",
    "no ", "not ", "free of", "free from", "without", "never",
    "geen", "zonder", "vrij van",
    "nessun", "senza", "sans", "pas de", "aucun",
]

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def clean_text(html):
    if not html:
        return ""
    text = _TAG.sub(" ", html)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return _WS.sub(" ", text).lower()


_CLAUSE_END = re.compile(r"[,.;:!?•|]|\s[-–—]\s")


def _negated(text, start):
    """Staat er in dezelfde bijzin vóór deze treffer een ontkenning?

    De ontkenning mag niet over een zins- of bijzingrens heen lekken:
    "geen nevel of schimmel, wel een klein krasje" is geen schone lens.
    """
    window = text[max(0, start - 45):start]
    boundaries = list(_CLAUSE_END.finditer(window))
    if boundaries:
        window = window[boundaries[-1].end():]
    return any(neg in window for neg in NEGATIONS)


def scan(description_html):
    """Geeft (gebreken, geruststellingen) terug als twee dicts.

    gebreken: {categorie: [gevonden fragment, ...]}
    geruststellingen: {categorie: aantal ontkende vermeldingen}
    """
    text = clean_text(description_html)
    flaws, reassurances = {}, {}
    if not text:
        return flaws, reassurances

    for label, terms in FLAW_TERMS.items():
        for term in terms:
            for m in re.finditer(r"\b" + re.escape(term), text):
                if _negated(text, m.start()):
                    reassurances[label] = reassurances.get(label, 0) + 1
                else:
                    fragment = text[max(0, m.start() - 40):m.start() + 60].strip()
                    flaws.setdefault(label, [])
                    if len(flaws[label]) < 2:
                        flaws[label].append(fragment)
    return flaws, reassurances


def summarize(flaws, reassurances):
    if flaws:
        return "⚠️ " + ", ".join(sorted(flaws))
    if reassurances:
        return "✅ expliciet vrij van: " + ", ".join(sorted(reassurances))
    return "—"
