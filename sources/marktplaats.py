import requests
from bs4 import BeautifulSoup
import urllib.parse


BASE_URL = "https://www.marktplaats.nl"


def search_marktplaats(query, limit=10):
    encoded_query = urllib.parse.quote_plus(query)
    url = f"{BASE_URL}/q/{encoded_query}/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    for item in soup.select(".hz-Listing")[:limit]:
        title_el = item.select_one(".hz-Text--bodyLarge")
        price_el = item.select_one(".hz-Listing-price")
        link_el = item.select_one('a[href*="/v/"]')

        href = None
        if link_el and link_el.has_attr("href"):
            href = link_el["href"]
            if href.startswith("/"):
                href = BASE_URL + href

        results.append({
            "title": title_el.get_text(strip=True) if title_el else None,
            "price": price_el.get_text(strip=True) if price_el else None,
            "url": href,
            "source": "marktplaats",
        })

    return results
