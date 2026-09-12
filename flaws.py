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
        # "balsam" niet los: in "balsam separation: none" staat de ontkenning
        # achter het tweede woord, en dan wordt de treffer niet herkend.
        "separation", "trennung", "balsamtrennung", "coating damage",
        "beschichtung", "delaminat", "putzspuren", "cleaning marks",
        "wischspuren",
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


# Harde zinsgrenzen. Komma's tellen alleen als grens bij een tegenstelling,
# want "no fungus, haze, or scratches" is één ontkende opsomming.
_HARD_END = re.compile(r"[.;!?•|]|\s[-–—]\s(?=[a-z])")
_CONTRAST = re.compile(
    r",\s*(?:wel\b|maar\b|but\b|however\b|though\b|aber\b|jedoch\b|doch\b|"
    r"echter\b|alleen\b|mais\b|per[oò]\b|there (?:is|are)\b|has\b|hat\b)"
)
# Ontkenning die ACHTER de term staat: "there is fog -no", "fungus: none".
_POST_NEG = re.compile(
    r"^[\s)\]\-–—:,]*(?:no\b|none\b|nope\b|nil\b|nein\b|keine?n?\b|geen\b|"
    r"nessun\w*\b|aucun\w*\b|0\b)"
)


def _negated(text, start, end):
    """Wordt deze treffer ontkend — ervóór of erachter?"""
    # 1. ontkenning erachter: "there is fog -no", "fungus : none"
    if _POST_NEG.match(text[end:end + 18]):
        return True

    # 2. ontkenning ervóór, binnen dezelfde zin
    window = text[max(0, start - 60):start]
    hard = list(_HARD_END.finditer(window))
    if hard:
        window = window[hard[-1].end():]
    contrast = list(_CONTRAST.finditer(window))
    if contrast:
        window = window[contrast[-1].end():]
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
            # \w* consumeert de rest van het woord, zodat bij "scratches -no"
            # de ontkenning erachter nog wordt gezien (en niet de "es" ervoor).
            for m in re.finditer(r"\b" + re.escape(term) + r"\w*", text):
                if _negated(text, m.start(), m.end()):
                    reassurances[label] = reassurances.get(label, 0) + 1
                else:
                    fragment = text[max(0, m.start() - 40):m.start() + 60].strip()
                    flaws.setdefault(label, [])
                    if len(flaws[label]) < 2:
                        flaws[label].append(fragment)
    return flaws, reassurances


# Gebreken die een lens diskwalificeren, tegenover slijtage die je erbij neemt.
DEALBREAKERS = {
    "nevel/haze", "schimmel/fungus", "separatie/coating",
    "olie op diafragma", "mechanisch", "niet getest",
}


def summarize(flaws, reassurances):
    serious = sorted(c for c in flaws if c in DEALBREAKERS)
    minor = sorted(c for c in flaws if c not in DEALBREAKERS)
    parts = []
    if serious:
        parts.append("⚠️ " + ", ".join(serious))
    if minor:
        parts.append("· licht: " + ", ".join(minor))
    if parts:
        return " ".join(parts)
    if reassurances:
        return "✅ vrij van: " + ", ".join(sorted(reassurances))
    return "—"
