"""
LeetCode data fetching utilities.

LeetCode does not offer an official public REST API. This module uses
LeetCode's public GraphQL endpoint (the same one leetcode.com's own
frontend uses), which does not require authentication for public
profile data. If LeetCode changes or blocks this endpoint, the function
degrades gracefully and reports the data as unavailable.
"""

import json
import requests

LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"

PROFILE_QUERY = """
query userProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      ranking
      realName
      userAvatar
    }
    submitStats {
      acSubmissionNum {
        difficulty
        count
      }
    }
    badges {
      displayName
    }
    submissionCalendar
  }
  userContestRanking(username: $username) {
    attendedContestsCount
    rating
    globalRanking
  }
}
"""


def fetch_leetcode_data(username: str) -> dict:
    """
    Fetch public profile data for a LeetCode username.

    Returns a dict with keys:
        available (bool), error (str|None), profile (dict),
        difficulty_counts (dict), badges (list[str]),
        submission_calendar (dict[str, int])
    """
    result = {
        "available": False,
        "error": None,
        "profile": {},
        "difficulty_counts": {"Easy": 0, "Medium": 0, "Hard": 0},
        "badges": [],
        "submission_calendar": {},
    }

    if not username:
        result["error"] = "No username provided."
        return result

    try:
        resp = requests.post(
            LEETCODE_GRAPHQL_URL,
            json={"query": PROFILE_QUERY, "variables": {"username": username}},
            headers={
                "Content-Type": "application/json",
                "Referer": f"https://leetcode.com/{username}/",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        matched_user = data.get("matchedUser")

        if not matched_user:
            result["error"] = f"LeetCode user '{username}' not found or profile is private."
            return result

        stats = matched_user.get("submitStats", {}).get("acSubmissionNum", [])
        difficulty_counts = {"Easy": 0, "Medium": 0, "Hard": 0}
        total = 0
        for entry in stats:
            diff = entry.get("difficulty")
            count = entry.get("count", 0)
            if diff in difficulty_counts:
                difficulty_counts[diff] = count
            if diff == "All":
                total = count

        calendar_raw = matched_user.get("submissionCalendar") or "{}"
        try:
            submission_calendar = json.loads(calendar_raw)
        except (json.JSONDecodeError, TypeError):
            submission_calendar = {}

        contest = data.get("userContestRanking") or {}

        result["available"] = True
        result["profile"] = {
            "username": matched_user.get("username"),
            "real_name": matched_user.get("profile", {}).get("realName"),
            "ranking": matched_user.get("profile", {}).get("ranking"),
            "avatar": matched_user.get("profile", {}).get("userAvatar"),
            "total_solved": total,
            "contest_rating": contest.get("rating"),
            "contest_global_ranking": contest.get("globalRanking"),
            "contests_attended": contest.get("attendedContestsCount"),
        }
        result["difficulty_counts"] = difficulty_counts
        result["badges"] = [b.get("displayName") for b in matched_user.get("badges", [])]
        result["submission_calendar"] = submission_calendar

    except requests.RequestException as exc:
        result["error"] = f"Network error while fetching LeetCode data: {exc}"
    except (ValueError, KeyError) as exc:
        result["error"] = f"Unexpected response format from LeetCode: {exc}"

    return result
