import re


def _matches(term, title):
    if not term:
        return False
    return bool(re.search(r"\b" + re.escape(term.lower()) + r"\b", title))


def filter_items(items, include_terms, exclude_terms):
    filtered = []
    for item in items:
        title = (item.get("title") or "").lower()

        if any(_matches(t, title) for t in exclude_terms):
            continue

        if include_terms and not any(_matches(t, title) for t in include_terms):
            continue

        filtered.append(item)
    return filtered
