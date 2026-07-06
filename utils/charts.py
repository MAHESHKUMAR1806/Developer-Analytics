"""Reusable Plotly chart builders for each platform dashboard."""

import collections
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PALETTE = px.colors.qualitative.Set2


# ---------------------------------------------------------------------------
# GitHub charts
# ---------------------------------------------------------------------------

def github_language_pie(languages: dict):
    if not languages:
        return None
    df = pd.DataFrame({"language": list(languages.keys()), "count": list(languages.values())})
    fig = px.pie(df, names="language", values="count", title="Language Distribution", hole=0.35,
                 color_discrete_sequence=PALETTE)
    fig.update_traces(textinfo="percent+label")
    return fig


def github_repo_creation_trend(repos: list):
    if not repos:
        return None
    years = collections.Counter()
    for r in repos:
        created = r.get("created_at")
        if created:
            years[created[:4]] += 1
    if not years:
        return None
    df = pd.DataFrame(sorted(years.items()), columns=["year", "repos_created"])
    fig = px.line(df, x="year", y="repos_created", markers=True, title="Repository Creation Trend")
    return fig


def github_commit_history(commit_activity: dict):
    if not commit_activity:
        return None
    monthly_total = collections.Counter()
    for repo_commits in commit_activity.values():
        for month, count in repo_commits.items():
            monthly_total[month] += count
    if not monthly_total:
        return None
    df = pd.DataFrame(sorted(monthly_total.items()), columns=["month", "commits"])
    fig = px.bar(df, x="month", y="commits", title="Monthly Commit Activity (Top Repositories)")
    return fig


def github_top_repos_bar(repos: list, metric="stars"):
    if not repos:
        return None
    top = sorted(repos, key=lambda r: r.get(metric, 0), reverse=True)[:10]
    if not top:
        return None
    df = pd.DataFrame(top)
    fig = px.bar(df, x=metric, y="name", orientation="h",
                 title=f"Top Repositories by {metric.title()}", color=metric,
                 color_continuous_scale="Blues")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


def github_activity_timeline(repos: list):
    if not repos:
        return None
    events = []
    for r in repos[:15]:
        if r.get("created_at"):
            events.append({"repo": r["name"], "event": "Created", "date": r["created_at"][:10]})
        if r.get("pushed_at"):
            events.append({"repo": r["name"], "event": "Last Push", "date": r["pushed_at"][:10]})
    if not events:
        return None
    df = pd.DataFrame(events)
    df["date"] = pd.to_datetime(df["date"])
    fig = px.scatter(df, x="date", y="repo", color="event", title="Repository Activity Timeline",
                      color_discrete_sequence=PALETTE)
    return fig


# ---------------------------------------------------------------------------
# LeetCode charts
# ---------------------------------------------------------------------------

def leetcode_difficulty_pie(difficulty_counts: dict):
    total = sum(difficulty_counts.values())
    if not total:
        return None
    df = pd.DataFrame({"difficulty": list(difficulty_counts.keys()), "count": list(difficulty_counts.values())})
    fig = px.pie(df, names="difficulty", values="count", title="Problem Difficulty Distribution",
                 color="difficulty",
                 color_discrete_map={"Easy": "#8FBC8F", "Medium": "#F4B400", "Hard": "#DB4437"})
    return fig


def leetcode_weekly_activity(submission_calendar: dict):
    if not submission_calendar:
        return None
    weekday_counts = collections.Counter()
    for timestamp, count in submission_calendar.items():
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            weekday_counts[dt.strftime("%A")] += int(count)
        except (ValueError, OSError):
            continue
    if not weekday_counts:
        return None
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df = pd.DataFrame({"day": order, "submissions": [weekday_counts.get(d, 0) for d in order]})
    fig = px.bar(df, x="day", y="submissions", title="Weekly Solving Activity")
    return fig


def leetcode_submission_trend(submission_calendar: dict):
    if not submission_calendar:
        return None
    monthly = collections.Counter()
    for timestamp, count in submission_calendar.items():
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            monthly[dt.strftime("%Y-%m")] += int(count)
        except (ValueError, OSError):
            continue
    if not monthly:
        return None
    df = pd.DataFrame(sorted(monthly.items()), columns=["month", "submissions"])
    fig = px.line(df, x="month", y="submissions", markers=True, title="Submission Trend Over Time")
    return fig


def leetcode_submission_heatmap(submission_calendar: dict):
    if not submission_calendar:
        return None
    records = []
    for timestamp, count in submission_calendar.items():
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            records.append({"date": dt.date(), "count": int(count)})
        except (ValueError, OSError):
            continue
    if not records:
        return None
    df = pd.DataFrame(records)
    df["week"] = pd.to_datetime(df["date"]).dt.isocalendar().week
    df["weekday"] = pd.to_datetime(df["date"]).dt.day_name()
    pivot = df.pivot_table(index="weekday", columns="week", values="count", aggfunc="sum", fill_value=0)
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = pivot.reindex(weekday_order)
    fig = go.Figure(data=go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, colorscale="Greens"))
    fig.update_layout(title="Submission Calendar Heatmap")
    return fig


# ---------------------------------------------------------------------------
# Kaggle charts
# ---------------------------------------------------------------------------

def kaggle_contribution_pie(profile: dict, competitions_count=0):
    labels = ["Competitions", "Datasets", "Notebooks"]
    values = [
        competitions_count,
        profile.get("datasets_count", 0),
        profile.get("notebooks_count", 0),
    ]
    if sum(values) == 0:
        return None
    df = pd.DataFrame({"category": labels, "count": values})
    fig = px.pie(df, names="category", values="count", title="Contribution Distribution",
                 color_discrete_sequence=PALETTE)
    return fig


def kaggle_notebook_activity(notebooks: list):
    if not notebooks:
        return None
    df = pd.DataFrame(notebooks)
    if "votes" not in df.columns:
        return None
    df = df.sort_values("votes", ascending=False).head(10)
    fig = px.bar(df, x="title", y="votes", title="Notebook Activity by Votes")
    fig.update_xaxes(tickangle=45)
    return fig
