def filter_items(items, include_terms, exclude_terms):
    filtered = []
    for item in items:
        title = (item.get("title") or "").lower()

        if any(term.lower() in title for term in exclude_terms):
            continue

        if include_terms and not any(term.lower() in title for term in include_terms):
            continue

        filtered.append(item)
    return filtered
