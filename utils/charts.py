"""Reusable Plotly chart builders for each platform dashboard.

All builder functions are defensive: if the underlying data is missing,
malformed, or triggers an unexpected error, they return None instead of
raising, so a single bad chart never takes down the whole dashboard.
"""

import collections
import functools
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Light-theme chart styling
# ---------------------------------------------------------------------------
px.defaults.template = "plotly_white"

PALETTE = ["#4F46E5", "#0EA5E9", "#14B8A6", "#F59E0B", "#EC4899", "#8B5CF6", "#22C55E"]
DIFFICULTY_COLORS = {"Easy": "#22C55E", "Medium": "#F59E0B", "Hard": "#EF4444"}

FONT_FAMILY = "Inter, Manrope, -apple-system, sans-serif"


def _apply_light_layout(fig, title=None):
    """Apply consistent light-theme chrome to any figure."""
    fig.update_layout(
        template="plotly_white",
        font=dict(family=FONT_FAMILY, color="#1E293B", size=13),
        title_font=dict(size=16, color="#1E293B", family=FONT_FAMILY),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="#EEF2F7", linecolor="#E2E8F0", zerolinecolor="#E2E8F0")
    fig.update_yaxes(gridcolor="#EEF2F7", linecolor="#E2E8F0", zerolinecolor="#E2E8F0")
    if title:
        fig.update_layout(title=title)
    return fig


def safe_chart(fn):
    """Decorator: catch any exception in a chart builder and return None."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            fig = fn(*args, **kwargs)
            if fig is None:
                return None
            return _apply_light_layout(fig)
        except Exception:  # noqa: BLE001 - a broken chart should never crash the page
            return None

    return wrapper


# ---------------------------------------------------------------------------
# GitHub charts
# ---------------------------------------------------------------------------

@safe_chart
def github_language_pie(languages: dict):
    if not languages:
        return None
    df = pd.DataFrame({"language": list(languages.keys()), "count": list(languages.values())})
    fig = px.pie(df, names="language", values="count", title="Language Distribution", hole=0.45,
                 color_discrete_sequence=PALETTE)
    fig.update_traces(textinfo="percent+label", marker=dict(line=dict(color="#FFFFFF", width=2)))
    return fig


@safe_chart
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
    fig = px.line(df, x="year", y="repos_created", markers=True, title="Repository Creation Trend",
                  color_discrete_sequence=[PALETTE[0]])
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    return fig


@safe_chart
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
    fig = px.bar(df, x="month", y="commits", title="Monthly Commit Activity (Top Repositories)",
                 color_discrete_sequence=[PALETTE[1]])
    return fig


@safe_chart
def github_top_repos_bar(repos: list, metric="stars"):
    if not repos:
        return None
    top = sorted(repos, key=lambda r: r.get(metric, 0) or 0, reverse=True)[:10]
    top = [r for r in top if r.get("name")]
    if not top:
        return None
    df = pd.DataFrame(top)
    if metric not in df.columns:
        return None
    fig = px.bar(df, x=metric, y="name", orientation="h",
                 title=f"Top Repositories by {metric.title()}", color=metric,
                 color_continuous_scale=["#C7D2FE", "#4F46E5"])
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
    return fig


@safe_chart
def github_activity_timeline(repos: list):
    if not repos:
        return None
    events = []
    for r in repos[:15]:
        name = r.get("name")
        if not name:
            continue
        if r.get("created_at"):
            events.append({"repo": name, "event": "Created", "date": r["created_at"][:10]})
        if r.get("pushed_at"):
            events.append({"repo": name, "event": "Last Push", "date": r["pushed_at"][:10]})
    if not events:
        return None
    df = pd.DataFrame(events)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    if df.empty:
        return None
    fig = px.scatter(df, x="date", y="repo", color="event", title="Repository Activity Timeline",
                      color_discrete_sequence=[PALETTE[0], PALETTE[2]])
    fig.update_traces(marker=dict(size=11))
    return fig


# ---------------------------------------------------------------------------
# LeetCode charts
# ---------------------------------------------------------------------------

@safe_chart
def leetcode_difficulty_pie(difficulty_counts: dict):
    if not difficulty_counts or sum(difficulty_counts.values()) == 0:
        return None
    df = pd.DataFrame({"difficulty": list(difficulty_counts.keys()), "count": list(difficulty_counts.values())})
    fig = px.pie(df, names="difficulty", values="count", title="Problem Difficulty Distribution",
                 hole=0.45, color="difficulty", color_discrete_map=DIFFICULTY_COLORS)
    fig.update_traces(marker=dict(line=dict(color="#FFFFFF", width=2)))
    return fig


@safe_chart
def leetcode_weekly_activity(submission_calendar: dict):
    if not submission_calendar:
        return None
    weekday_counts = collections.Counter()
    for timestamp, count in submission_calendar.items():
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            weekday_counts[dt.strftime("%A")] += int(count)
        except (ValueError, OSError, TypeError):
            continue
    if not weekday_counts:
        return None
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df = pd.DataFrame({"day": order, "submissions": [weekday_counts.get(d, 0) for d in order]})
    fig = px.bar(df, x="day", y="submissions", title="Weekly Solving Activity",
                 color_discrete_sequence=[PALETTE[3]])
    return fig


@safe_chart
def leetcode_submission_trend(submission_calendar: dict):
    if not submission_calendar:
        return None
    monthly = collections.Counter()
    for timestamp, count in submission_calendar.items():
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            monthly[dt.strftime("%Y-%m")] += int(count)
        except (ValueError, OSError, TypeError):
            continue
    if not monthly:
        return None
    df = pd.DataFrame(sorted(monthly.items()), columns=["month", "submissions"])
    fig = px.line(df, x="month", y="submissions", markers=True, title="Submission Trend Over Time",
                  color_discrete_sequence=[PALETTE[2]])
    fig.update_traces(line=dict(width=3), marker=dict(size=7))
    return fig


@safe_chart
def leetcode_submission_heatmap(submission_calendar: dict):
    if not submission_calendar:
        return None
    records = []
    for timestamp, count in submission_calendar.items():
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            records.append({"date": dt.date(), "count": int(count)})
        except (ValueError, OSError, TypeError):
            continue
    if not records:
        return None
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    # Use a year-week label (not the bare ISO week number) so weeks from
    # different years don't collapse onto the same column.
    iso = df["date"].dt.isocalendar()
    df["year_week"] = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
    df["weekday"] = df["date"].dt.day_name()

    pivot = df.pivot_table(index="weekday", columns="year_week", values="count", aggfunc="sum", fill_value=0)
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = pivot.reindex(weekday_order).fillna(0)
    # Keep the most recent ~26 weeks so the heatmap stays readable.
    pivot = pivot[sorted(pivot.columns)[-26:]]

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale=[[0, "#F1F5F9"], [0.5, "#5EEAD4"], [1, "#0D9488"]],
            showscale=True,
        )
    )
    fig.update_layout(title="Submission Calendar Heatmap")
    return fig


# ---------------------------------------------------------------------------
# Kaggle charts
# ---------------------------------------------------------------------------

@safe_chart
def kaggle_contribution_pie(profile: dict, competitions_count=0):
    if not profile:
        return None
    labels = ["Competitions", "Datasets", "Notebooks"]
    values = [
        competitions_count,
        profile.get("datasets_count", 0) or 0,
        profile.get("notebooks_count", 0) or 0,
    ]
    if sum(values) == 0:
        return None
    df = pd.DataFrame({"category": labels, "count": values})
    fig = px.pie(df, names="category", values="count", title="Contribution Distribution",
                 hole=0.45, color_discrete_sequence=PALETTE)
    fig.update_traces(marker=dict(line=dict(color="#FFFFFF", width=2)))
    return fig


@safe_chart
def kaggle_notebook_activity(notebooks: list):
    if not notebooks:
        return None
    df = pd.DataFrame(notebooks)
    if df.empty or "votes" not in df.columns or "title" not in df.columns:
        return None
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0)
    df = df.sort_values("votes", ascending=False).head(10)
    if df.empty:
        return None
    fig = px.bar(df, x="title", y="votes", title="Notebook Activity by Votes",
                 color_discrete_sequence=[PALETTE[4]])
    fig.update_xaxes(tickangle=45)
    return fig
