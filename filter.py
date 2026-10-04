import re


def _matches(term, title):
    if not term:
        return False
    return bool(re.search(r"\b" + re.escape(term.lower()) + r"\b", title))


def filter_items(items, include_terms, exclude_terms, require_groups=None):
    """Filter op titel.

    include_terms: minstens één moet voorkomen (OF-logica), het grove voorfilter.
    exclude_terms: één treffer diskwalificeert.
    require_groups: lijst van groepen; uit ELKE groep moet minstens één term
        voorkomen. Daarmee is een EN-eis mogelijk, bijvoorbeeld "35" én "1.4".
        Dat is nodig zodra camera's meedoen: in "Nikon FE2 35mm SLR Film
        Camera" slaat 35mm op het filmformaat, niet op een lens.
    """
    filtered = []
    for item in items:
        title = (item.get("title") or "").lower()

        if any(_matches(t, title) for t in exclude_terms):
            continue

        if include_terms and not any(_matches(t, title) for t in include_terms):
            continue

        if require_groups and not all(
            any(_matches(t, title) for t in groep) for groep in require_groups
        ):
            continue

        filtered.append(item)
    return filtered
