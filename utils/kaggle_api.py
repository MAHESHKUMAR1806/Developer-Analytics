"""
Kaggle data fetching utilities.

Kaggle's official API requires an authenticated API token (kaggle.json)
and is oriented around competitions/datasets search rather than public
profile statistics. There is no fully public, unauthenticated endpoint
for arbitrary user profile stats, so this module:

  1. Tries the official Kaggle API (if KAGGLE_USERNAME / KAGGLE_KEY
     environment variables are configured) to pull competitions,
     datasets, and kernels (notebooks) authored by the user.
  2. Falls back to marking data as unavailable with a clear message
     if credentials are not configured, so the rest of the app can
     display a graceful "data not available" state per platform.

To enable full Kaggle integration, set the following environment
variables (or place a kaggle.json in ~/.kaggle/):
    KAGGLE_USERNAME
    KAGGLE_KEY
"""

import os
import collections


def _kaggle_credentials_available() -> bool:
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        return True
    kaggle_json = os.path.expanduser("~/.kaggle/kaggle.json")
    return os.path.exists(kaggle_json)


def fetch_kaggle_data(username: str) -> dict:
    """
    Fetch public profile data for a Kaggle username.

    Returns a dict with keys:
        available (bool), error (str|None), profile (dict),
        competitions (list[dict]), datasets (list[dict]),
        notebooks (list[dict])
    """
    result = {
        "available": False,
        "error": None,
        "profile": {},
        "competitions": [],
        "datasets": [],
        "notebooks": [],
    }

    if not username:
        result["error"] = "No username provided."
        return result

    if not _kaggle_credentials_available():
        result["error"] = (
            "Kaggle API credentials not configured. Set KAGGLE_USERNAME and "
            "KAGGLE_KEY environment variables (or add ~/.kaggle/kaggle.json) "
            "to enable Kaggle data retrieval. Displaying unavailable state."
        )
        return result

    try:
        # Imported lazily so the app still runs without the kaggle package
        # installed / configured.
        from kaggle.api.kaggle_api_extended import KaggleApi

        api = KaggleApi()
        api.authenticate()

        datasets = api.dataset_list(user=username)
        notebooks = api.kernels_list(user=username)

        dataset_info = [
            {
                "title": d.title,
                "votes": getattr(d, "voteCount", 0),
                "size": getattr(d, "totalBytes", 0),
            }
            for d in datasets
        ]
        notebook_info = [
            {
                "title": k.title,
                "votes": getattr(k, "totalVotes", 0),
                "language": getattr(k, "language", "unknown"),
            }
            for k in notebooks
        ]

        result["available"] = True
        result["profile"] = {
            "username": username,
            "datasets_count": len(dataset_info),
            "notebooks_count": len(notebook_info),
        }
        result["datasets"] = dataset_info
        result["notebooks"] = notebook_info
        # Competitions are not directly queryable by-user via the public
        # API, so this is left as an empty list unless extended with
        # scraping / an authenticated endpoint the user provides.
        result["competitions"] = []

    except ImportError:
        result["error"] = (
            "The 'kaggle' package is not installed. Run 'pip install kaggle' "
            "to enable Kaggle data retrieval."
        )
    except Exception as exc:  # noqa: BLE001 - surface any API error to the UI
        result["error"] = f"Error while fetching Kaggle data: {exc}"

    return result
