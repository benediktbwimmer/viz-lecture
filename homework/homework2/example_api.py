# timeseries_api_examples.py
"""
Demonstration script: Making GET and POST requests to a (fictional) time‑series API
showing:
  • Unauthenticated requests (public endpoints)
  • Authenticated requests (private endpoints) using an API key

The API key is expected in an environment variable called ``SOME_API_KEY`` and
is loaded with ``python‑dotenv``.

Each request returns JSON shaped like
{
    "symbol": "XYZ",
    "data": [
        {"timestamp": "2025‑05‑12T00:00:00Z", "value": 123.45},
        ...
    ]
}
which we immediately load into a ``pandas.DataFrame`` for further analysis.

Note: Because the API is fictional, running this script will raise HTTP errors
unless you swap the base‑URL and parameters for a real data provider or mock
server.
"""

import os
from typing import Any, Dict

import requests
import pandas as pd
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from a .env file located in the working directory
load_dotenv()

API_BASE = "https://api.fictionaltimeseries.com"  # Placeholder base‑URL
API_KEY_VAR = "SOME_API_KEY"  # Name of the environment variable storing the key


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    """Return the API key or raise a helpful error if it is missing."""
    key = os.getenv(API_KEY_VAR)
    if not key:
        raise RuntimeError(
            f"Environment variable '{API_KEY_VAR}' is not set. "
            "Create a .env file or export the variable before running authenticated examples."
        )
    return key


def _json_to_frame(json_resp: Dict[str, Any]) -> pd.DataFrame:
    """Convert the standard API response body into a pandas DataFrame."""
    return pd.DataFrame(json_resp["data"]).set_index("timestamp")


# ---------------------------------------------------------------------------
# GET request examples
# ---------------------------------------------------------------------------

def get_timeseries_public(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Public GET request – no API key required."""
    endpoint = f"{API_BASE}/timeseries"
    params = {"symbol": symbol, "start": start, "end": end}
    response = requests.get(endpoint, params=params, timeout=10)
    response.raise_for_status()
    return _json_to_frame(response.json())


def get_timeseries_private(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Authenticated GET request – API key sent in the *Authorization* header."""
    endpoint = f"{API_BASE}/timeseries"
    params = {"symbol": symbol, "start": start, "end": end}
    headers = {"Authorization": f"Bearer {_get_api_key()}"}
    response = requests.get(endpoint, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    return _json_to_frame(response.json())


# ---------------------------------------------------------------------------
# POST request examples
# ---------------------------------------------------------------------------

def post_timeseries_public(symbol: str, frequency: str = "1h") -> pd.DataFrame:
    """Public POST request – no API key required."""
    endpoint = f"{API_BASE}/timeseries"
    payload = {"symbol": symbol, "frequency": frequency}
    response = requests.post(endpoint, json=payload, timeout=10)
    response.raise_for_status()
    return _json_to_frame(response.json())


def post_timeseries_private(symbol: str, frequency: str = "1h") -> pd.DataFrame:
    """Authenticated POST request – API key sent in the *Authorization* header."""
    endpoint = f"{API_BASE}/timeseries"
    payload = {"symbol": symbol, "frequency": frequency}
    headers = {"Authorization": f"Bearer {_get_api_key()}"}
    response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return _json_to_frame(response.json())


# ---------------------------------------------------------------------------
# Main – run only when executed directly
# ---------------------------------------------------------------------------

def main() -> None:  # pragma: no cover
    """Run a quick demo fetching the first few rows for each request type."""

    symbol = "XYZ"
    date_range = {"start": "2025-05-01", "end": "2025-05-12"}

    try:
        print("\n--- GET (public) ----------------------------------------------------------")
        print(get_timeseries_public(symbol, **date_range).head())

        print("\n--- GET (with key) --------------------------------------------------------")
        print(get_timeseries_private(symbol, **date_range).head())

        print("\n--- POST (public) ---------------------------------------------------------")
        print(post_timeseries_public(symbol).head())

        print("\n--- POST (with key) -------------------------------------------------------")
        print(post_timeseries_private(symbol).head())

    except requests.HTTPError as exc:
        print("Request failed – this is expected when hitting a fictional endpoint.")
        print(str(exc))


if __name__ == "__main__":
    main()
