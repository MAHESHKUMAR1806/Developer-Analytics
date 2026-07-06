"""
Developer Analytics Dashboard
=============================

A Streamlit application that aggregates a developer's public activity
across GitHub, LeetCode, and Kaggle into a single interactive dashboard,
with downloadable PDF report generation.

Run with:
    streamlit run app.py
"""

import streamlit as st

from utils.github_api import fetch_github_data
from utils.leetcode_api import fetch_leetcode_data
from utils.kaggle_api import fetch_kaggle_data
from utils.pdf_generator import generate_pdf_report
from utils import charts

st.set_page_config(
    page_title="Developer Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
DEFAULTS = {
    "page": "home",
    "analyzed": False,
    "github_data": None,
    "leetcode_data": None,
    "kaggle_data": None,
    "usernames": {"github": "", "leetcode": "", "kaggle": ""},
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def go_to(page: str):
    st.session_state.page = page


# ---------------------------------------------------------------------------
# Global styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #2E3440;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #4C566A;
        margin-top: 0.2rem;
        margin-bottom: 1.5rem;
    }
    div[data-testid="stMetric"] {
        background-color: #ECEFF4;
        border-radius: 10px;
        padding: 12px 16px;
    }
    .platform-card {
        border-radius: 14px;
        padding: 24px;
        text-align: center;
        border: 1px solid #E5E9F0;
        background: linear-gradient(180deg, #ffffff 0%, #F7F9FC 100%);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------
def render_home():
    st.markdown('<p class="main-title">📊 Developer Analytics Dashboard</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Analyze a developer\'s public activity across GitHub, LeetCode, '
        "and Kaggle from a single place — then export a professional PDF report.</p>",
        unsafe_allow_html=True,
    )

    with st.form("username_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            gh_user = st.text_input("GitHub Username", value=st.session_state.usernames["github"])
        with col2:
            lc_user = st.text_input("LeetCode Username", value=st.session_state.usernames["leetcode"])
        with col3:
            kg_user = st.text_input("Kaggle Username", value=st.session_state.usernames["kaggle"])

        submitted = st.form_submit_button("🔍 Analyze", use_container_width=True, type="primary")

    if submitted:
        if not (gh_user or lc_user or kg_user):
            st.warning("Please enter at least one username to analyze.")
        else:
            st.session_state.usernames = {"github": gh_user, "leetcode": lc_user, "kaggle": kg_user}
            with st.spinner("Fetching public profile data..."):
                st.session_state.github_data = fetch_github_data(gh_user) if gh_user else None
                st.session_state.leetcode_data = fetch_leetcode_data(lc_user) if lc_user else None
                st.session_state.kaggle_data = fetch_kaggle_data(kg_user) if kg_user else None
            st.session_state.analyzed = True

    if st.session_state.analyzed:
        st.divider()
        st.subheader("Select a platform to explore")
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown('<div class="platform-card">', unsafe_allow_html=True)
            st.markdown("### 🐙 GitHub")
            data = st.session_state.github_data
            if data and data.get("available"):
                st.metric("Public Repos", data["profile"].get("public_repos", 0))
                if st.button("Open GitHub Dashboard", key="open_github", use_container_width=True):
                    go_to("github")
                    st.rerun()
            elif data:
                st.info(data.get("error") or "No data available.")
            else:
                st.caption("No username provided.")
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="platform-card">', unsafe_allow_html=True)
            st.markdown("### 💻 LeetCode")
            data = st.session_state.leetcode_data
            if data and data.get("available"):
                st.metric("Problems Solved", data["profile"].get("total_solved", 0))
                if st.button("Open LeetCode Dashboard", key="open_leetcode", use_container_width=True):
                    go_to("leetcode")
                    st.rerun()
            elif data:
                st.info(data.get("error") or "No data available.")
            else:
                st.caption("No username provided.")
            st.markdown("</div>", unsafe_allow_html=True)

        with c3:
            st.markdown('<div class="platform-card">', unsafe_allow_html=True)
            st.markdown("### 📈 Kaggle")
            data = st.session_state.kaggle_data
            if data and data.get("available"):
                st.metric("Notebooks Published", data["profile"].get("notebooks_count", 0))
                if st.button("Open Kaggle Dashboard", key="open_kaggle", use_container_width=True):
                    go_to("kaggle")
                    st.rerun()
            elif data:
                st.info(data.get("error") or "No data available.")
            else:
                st.caption("No username provided.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
        render_report_section()


def render_report_section():
    st.subheader("📄 Download Full Report")
    st.caption("Generates a combined PDF covering every platform that returned data.")

    if st.button("Generate PDF Report", type="secondary"):
        github_data = st.session_state.github_data or {"available": False, "error": "Not requested."}
        leetcode_data = st.session_state.leetcode_data or {"available": False, "error": "Not requested."}
        kaggle_data = st.session_state.kaggle_data or {"available": False, "error": "Not requested."}

        figures = {}
        if github_data.get("available"):
            fig = charts.github_language_pie(github_data.get("languages", {}))
            if fig:
                figures["github_languages"] = fig
        if leetcode_data.get("available"):
            fig = charts.leetcode_difficulty_pie(leetcode_data.get("difficulty_counts", {}))
            if fig:
                figures["leetcode_difficulty"] = fig
        if kaggle_data.get("available"):
            fig = charts.kaggle_contribution_pie(kaggle_data.get("profile", {}))
            if fig:
                figures["kaggle_contributions"] = fig

        try:
            pdf_bytes = generate_pdf_report(
                st.session_state.usernames, github_data, leetcode_data, kaggle_data, figures
            )
            st.download_button(
                "⬇️ Download Report PDF",
                data=pdf_bytes,
                file_name="developer_analytics_report.pdf",
                mime="application/pdf",
            )
        except Exception as exc:  # noqa: BLE001
            st.error(
                "Could not embed charts in the PDF (kaleido may be missing). "
                f"Generating a text-only report instead. Details: {exc}"
            )
            pdf_bytes = generate_pdf_report(
                st.session_state.usernames, github_data, leetcode_data, kaggle_data, {}
            )
            st.download_button(
                "⬇️ Download Report PDF (no charts)",
                data=pdf_bytes,
                file_name="developer_analytics_report.pdf",
                mime="application/pdf",
            )


# ---------------------------------------------------------------------------
# GitHub dashboard page
# ---------------------------------------------------------------------------
def render_github_dashboard():
    data = st.session_state.github_data
    st.button("⬅ Back to Home", on_click=go_to, args=("home",))
    st.title("🐙 GitHub Analytics")

    if not data or not data.get("available"):
        st.warning(data.get("error") if data else "No GitHub data available.")
        return

    profile = data["profile"]
    st.markdown(f"### {profile.get('name')} (@{profile.get('login')})")
    if profile.get("bio"):
        st.caption(profile["bio"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Public Repositories", profile.get("public_repos", 0))
    c2.metric("Followers", profile.get("followers", 0))
    c3.metric("Following", profile.get("following", 0))
    c4.metric("Account Created", (profile.get("created_at") or "N/A")[:10])

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        fig = charts.github_language_pie(data["languages"])
        st.plotly_chart(fig, use_container_width=True) if fig else st.info("No language data available.")
    with col2:
        fig = charts.github_repo_creation_trend(data["repos"])
        st.plotly_chart(fig, use_container_width=True) if fig else st.info("No repository creation data available.")

    col3, col4 = st.columns(2)
    with col3:
        fig = charts.github_commit_history(data["commit_activity"])
        st.plotly_chart(fig, use_container_width=True) if fig else st.info("No commit history available.")
    with col4:
        fig = charts.github_top_repos_bar(data["repos"], metric="stars")
        st.plotly_chart(fig, use_container_width=True) if fig else st.info("No repository comparison data available.")

    fig = charts.github_activity_timeline(data["repos"])
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Repositories")
    recent = sorted(data["repos"], key=lambda r: r.get("updated_at") or "", reverse=True)[:10]
    if recent:
        st.dataframe(
            [{"Name": r["name"], "Language": r.get("language") or "N/A", "Stars": r["stars"],
              "Forks": r["forks"], "Last Updated": (r.get("updated_at") or "")[:10]} for r in recent],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No repository data available.")


# ---------------------------------------------------------------------------
# LeetCode dashboard page
# ---------------------------------------------------------------------------
def render_leetcode_dashboard():
    data = st.session_state.leetcode_data
    st.button("⬅ Back to Home", on_click=go_to, args=("home",))
    st.title("💻 LeetCode Analytics")

    if not data or not data.get("available"):
        st.warning(data.get("error") if data else "No LeetCode data available.")
        return

    profile = data["profile"]
    counts = data["difficulty_counts"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Solved", profile.get("total_solved", 0))
    c2.metric("Easy", counts.get("Easy", 0))
    c3.metric("Medium", counts.get("Medium", 0))
    c4.metric("Hard", counts.get("Hard", 0))

    c5, c6 = st.columns(2)
    c5.metric("Global Ranking", profile.get("ranking") or "Not available")
    c6.metric("Contest Rating", profile.get("contest_rating") or "Not available")

    if data.get("badges"):
        st.write("**Badges:** " + ", ".join(data["badges"]))

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        fig = charts.leetcode_difficulty_pie(counts)
        st.plotly_chart(fig, use_container_width=True) if fig else st.info("No difficulty data available.")
    with col2:
        fig = charts.leetcode_weekly_activity(data["submission_calendar"])
        st.plotly_chart(fig, use_container_width=True) if fig else st.info("No weekly activity data available.")

    col3, col4 = st.columns(2)
    with col3:
        fig = charts.leetcode_submission_trend(data["submission_calendar"])
        st.plotly_chart(fig, use_container_width=True) if fig else st.info("No submission trend data available.")
    with col4:
        fig = charts.leetcode_submission_heatmap(data["submission_calendar"])
        st.plotly_chart(fig, use_container_width=True) if fig else st.info("No submission calendar data available.")


# ---------------------------------------------------------------------------
# Kaggle dashboard page
# ---------------------------------------------------------------------------
def render_kaggle_dashboard():
    data = st.session_state.kaggle_data
    st.button("⬅ Back to Home", on_click=go_to, args=("home",))
    st.title("📈 Kaggle Analytics")

    if not data or not data.get("available"):
        st.warning(data.get("error") if data else "No Kaggle data available.")
        st.caption(
            "Tip: Kaggle requires API credentials (KAGGLE_USERNAME / KAGGLE_KEY) "
            "to retrieve profile statistics — see utils/kaggle_api.py for setup."
        )
        return

    profile = data["profile"]
    c1, c2 = st.columns(2)
    c1.metric("Datasets Published", profile.get("datasets_count", 0))
    c2.metric("Notebooks Published", profile.get("notebooks_count", 0))

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        fig = charts.kaggle_contribution_pie(profile)
        st.plotly_chart(fig, use_container_width=True) if fig else st.info("No contribution data available.")
    with col2:
        fig = charts.kaggle_notebook_activity(data["notebooks"])
        st.plotly_chart(fig, use_container_width=True) if fig else st.info("No notebook activity data available.")

    st.subheader("Published Datasets")
    if data["datasets"]:
        st.dataframe(data["datasets"], use_container_width=True, hide_index=True)
    else:
        st.info("No dataset data available.")

    st.subheader("Published Notebooks")
    if data["notebooks"]:
        st.dataframe(data["notebooks"], use_container_width=True, hide_index=True)
    else:
        st.info("No notebook data available.")


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
PAGES = {
    "home": render_home,
    "github": render_github_dashboard,
    "leetcode": render_leetcode_dashboard,
    "kaggle": render_kaggle_dashboard,
}

PAGES[st.session_state.page]()
