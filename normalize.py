def normalize_items(items, source="ebay"):
    normalized = []

    for i in items:
        normalized.append({
            "source": source,
            "title": i.get("title"),
            "price": i.get("price", {}).get("value"),
            "currency": i.get("price", {}).get("currency"),
            "condition": i.get("condition"),
            "seller": i.get("seller", {}).get("username"),
            "seller_feedback": i.get("seller", {}).get("feedbackPercentage"),
            "location": i.get("itemLocation", {}).get("country"),
            "url": i.get("itemWebUrl"),
        })

    return normalized

def normalize_marktplaats(items):
    normalized = []

    for i in items:
        normalized.append({
            "source": "marktplaats",
            "title": i.get("title"),
            "price": i.get("price"),
            "currency": "EUR",
            "condition": None,
            "seller": None,
            "seller_feedback": None,
            "location": None,
            "url": i.get("url"),
        })

    return normalized

def normalize_mpb(items):
    normalized = []

    for i in items:
        normalized.append({
            "source": "mpb",
            "title": i.get("title"),
            "price": i.get("price"),
            "currency": "EUR",
            "condition": i.get("condition"),
            "seller": "MPB",
            "seller_feedback": "professional reseller, warranty",
            "location": "EU",
            "url": i.get("url"),
        })

    return normalized