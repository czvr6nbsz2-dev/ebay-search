import os
import time
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

_token_cache = {
    "access_token": None,
    "expires_at": 0,
}


def get_ebay_token():
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    client_id = os.environ["EBAY_CLIENT_ID"]
    client_secret = os.environ["EBAY_CLIENT_SECRET"]

    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    response = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data="grant_type=client_credentials&scope=https://api.ebay.com/oauth/api_scope",
    )
    response.raise_for_status()
    token_data = response.json()

    _token_cache["access_token"] = token_data["access_token"]
    _token_cache["expires_at"] = time.time() + token_data["expires_in"] - 60

    return _token_cache["access_token"]


def search_ebay(query, limit=10, category_id=None):
    params = {"q": query, "limit": limit}
    if category_id:
        params["category_ids"] = category_id

    response = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers={
            "Authorization": f"Bearer {get_ebay_token()}",
            "Content-Type": "application/json",
        },
        params=params,
    )
    response.raise_for_status()
    return response.json().get("itemSummaries", [])
