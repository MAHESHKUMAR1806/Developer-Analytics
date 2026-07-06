"""
GitHub data fetching utilities.

Uses the public GitHub REST API (unauthenticated, rate-limited to 60
requests/hour per IP). For higher limits, set a GITHUB_TOKEN environment
variable and it will be used automatically.
"""

import os
import collections
from datetime import datetime

import requests

GITHUB_API_BASE = "https://api.github.com"


def _headers():
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_github_data(username: str) -> dict:
    """
    Fetch public profile + repository data for a GitHub username.

    Returns a dict with keys:
        available (bool), error (str|None), profile (dict),
        repos (list[dict]), languages (dict), commit_activity (dict)
    """
    result = {
        "available": False,
        "error": None,
        "profile": {},
        "repos": [],
        "languages": {},
        "commit_activity": {},
    }

    if not username:
        result["error"] = "No username provided."
        return result

    try:
        profile_resp = requests.get(
            f"{GITHUB_API_BASE}/users/{username}", headers=_headers(), timeout=10
        )
        if profile_resp.status_code == 404:
            result["error"] = f"GitHub user '{username}' not found."
            return result
        if profile_resp.status_code == 403:
            result["error"] = "GitHub API rate limit exceeded. Try again later or set GITHUB_TOKEN."
            return result
        profile_resp.raise_for_status()
        profile = profile_resp.json()

        repos = []
        page = 1
        while True:
            repos_resp = requests.get(
                f"{GITHUB_API_BASE}/users/{username}/repos",
                params={"per_page": 100, "page": page, "sort": "updated"},
                headers=_headers(),
                timeout=10,
            )
            if repos_resp.status_code != 200:
                break
            batch = repos_resp.json()
            if not batch:
                break
            repos.extend(batch)
            page += 1
            if page > 5:  # safety cap: 500 repos max
                break

        language_counts = collections.Counter()
        for repo in repos:
            lang = repo.get("language")
            if lang:
                language_counts[lang] += 1

        commit_activity = {}
        top_repos = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:3]
        for repo in top_repos:
            try:
                commits_resp = requests.get(
                    f"{GITHUB_API_BASE}/repos/{username}/{repo['name']}/commits",
                    params={"per_page": 100},
                    headers=_headers(),
                    timeout=10,
                )
                if commits_resp.status_code == 200:
                    monthly = collections.Counter()
                    for c in commits_resp.json():
                        date_str = c.get("commit", {}).get("author", {}).get("date")
                        if date_str:
                            dt = datetime.strptime(date_str[:7], "%Y-%m")
                            monthly[dt.strftime("%Y-%m")] += 1
                    commit_activity[repo["name"]] = dict(monthly)
            except requests.RequestException:
                continue

        result["available"] = True
        result["profile"] = {
            "login": profile.get("login"),
            "name": profile.get("name") or profile.get("login"),
            "avatar_url": profile.get("avatar_url"),
            "bio": profile.get("bio"),
            "public_repos": profile.get("public_repos", 0),
            "followers": profile.get("followers", 0),
            "following": profile.get("following", 0),
            "created_at": profile.get("created_at"),
            "location": profile.get("location"),
            "blog": profile.get("blog"),
            "company": profile.get("company"),
        }
        result["repos"] = [
            {
                "name": r.get("name"),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "language": r.get("language"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
                "pushed_at": r.get("pushed_at"),
                "description": r.get("description"),
                "fork": r.get("fork", False),
            }
            for r in repos
        ]
        result["languages"] = dict(language_counts)
        result["commit_activity"] = commit_activity

    except requests.RequestException as exc:
        result["error"] = f"Network error while fetching GitHub data: {exc}"

    return result
