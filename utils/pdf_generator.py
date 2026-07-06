"""
PDF report generation using ReportLab.

Generates a single professional PDF summarizing whichever platform data
is available (GitHub, LeetCode, Kaggle). Charts are rendered to PNG via
Plotly/Kaleido first, then embedded as images in the PDF.
"""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)

PRIMARY_COLOR = colors.HexColor("#2E3440")
ACCENT_COLOR = colors.HexColor("#5E81AC")
LIGHT_BG = colors.HexColor("#ECEFF4")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            fontSize=22,
            leading=26,
            textColor=PRIMARY_COLOR,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            fontSize=15,
            leading=18,
            textColor=ACCENT_COLOR,
            spaceBefore=14,
            spaceAfter=8,
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(
            name="MetaText",
            fontSize=9,
            textColor=colors.grey,
        )
    )
    return styles


def _metric_table(pairs, col_widths=(6 * cm, 6 * cm)):
    data = [[Paragraph(f"<b>{k}</b>", ParagraphStyle("k", fontSize=10)),
             Paragraph(str(v), ParagraphStyle("v", fontSize=10))] for k, v in pairs]
    table = Table(data, colWidths=list(col_widths))
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def _fig_to_image(fig, width=15 * cm, height=8 * cm):
    """Convert a Plotly figure to a ReportLab Image via PNG bytes (requires kaleido)."""
    try:
        png_bytes = fig.to_image(format="png", width=900, height=480, scale=2)
        return Image(io.BytesIO(png_bytes), width=width, height=height)
    except Exception:
        return None


def generate_pdf_report(username_summary: dict, github_data: dict, leetcode_data: dict,
                         kaggle_data: dict, figures: dict = None) -> bytes:
    """
    Build the combined PDF report.

    username_summary: {"github": str, "leetcode": str, "kaggle": str}
    figures: optional dict of Plotly figures keyed by a descriptive name,
             e.g. {"github_languages": fig, "leetcode_difficulty": fig, ...}
    """
    figures = figures or {}
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )
    styles = _styles()
    story = []

    story.append(Paragraph("Developer Analytics Report", styles["ReportTitle"]))
    story.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}",
            styles["MetaText"],
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    identity_pairs = [
        ("GitHub Username", username_summary.get("github") or "Not provided"),
        ("LeetCode Username", username_summary.get("leetcode") or "Not provided"),
        ("Kaggle Username", username_summary.get("kaggle") or "Not provided"),
    ]
    story.append(_metric_table(identity_pairs))
    story.append(Spacer(1, 0.4 * cm))

    # ---------------- GitHub Section ----------------
    story.append(Paragraph("GitHub Summary", styles["SectionHeader"]))
    if github_data.get("available"):
        profile = github_data["profile"]
        pairs = [
            ("Name", profile.get("name")),
            ("Public Repositories", profile.get("public_repos")),
            ("Followers", profile.get("followers")),
            ("Following", profile.get("following")),
            ("Account Created", (profile.get("created_at") or "")[:10]),
            ("Location", profile.get("location") or "Not available"),
        ]
        story.append(_metric_table(pairs))
        top_repos = sorted(github_data["repos"], key=lambda r: r.get("stars", 0), reverse=True)[:5]
        if top_repos:
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph("Top Repositories", styles["Heading4"]))
            repo_rows = [["Repository", "Stars", "Forks", "Language"]]
            for r in top_repos:
                repo_rows.append([r["name"], str(r["stars"]), str(r["forks"]), r.get("language") or "N/A"])
            repo_table = Table(repo_rows, colWidths=[6 * cm, 2.5 * cm, 2.5 * cm, 3 * cm])
            repo_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), ACCENT_COLOR),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(repo_table)
        if "github_languages" in figures:
            img = _fig_to_image(figures["github_languages"])
            if img:
                story.append(Spacer(1, 0.3 * cm))
                story.append(img)
    else:
        story.append(
            Paragraph(
                f"Data not available. {github_data.get('error') or ''}",
                styles["BodyText"],
            )
        )

    story.append(PageBreak())

    # ---------------- LeetCode Section ----------------
    story.append(Paragraph("LeetCode Summary", styles["SectionHeader"]))
    if leetcode_data.get("available"):
        profile = leetcode_data["profile"]
        counts = leetcode_data["difficulty_counts"]
        pairs = [
            ("Total Solved", profile.get("total_solved")),
            ("Easy", counts.get("Easy")),
            ("Medium", counts.get("Medium")),
            ("Hard", counts.get("Hard")),
            ("Global Ranking", profile.get("ranking") or "Not available"),
            ("Contest Rating", profile.get("contest_rating") or "Not available"),
        ]
        story.append(_metric_table(pairs))
        if leetcode_data.get("badges"):
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph("Badges: " + ", ".join(leetcode_data["badges"]), styles["BodyText"]))
        if "leetcode_difficulty" in figures:
            img = _fig_to_image(figures["leetcode_difficulty"])
            if img:
                story.append(Spacer(1, 0.3 * cm))
                story.append(img)
    else:
        story.append(
            Paragraph(
                f"Data not available. {leetcode_data.get('error') or ''}",
                styles["BodyText"],
            )
        )

    story.append(PageBreak())

    # ---------------- Kaggle Section ----------------
    story.append(Paragraph("Kaggle Summary", styles["SectionHeader"]))
    if kaggle_data.get("available"):
        profile = kaggle_data["profile"]
        pairs = [
            ("Datasets Published", profile.get("datasets_count")),
            ("Notebooks Published", profile.get("notebooks_count")),
        ]
        story.append(_metric_table(pairs))
        if "kaggle_contributions" in figures:
            img = _fig_to_image(figures["kaggle_contributions"])
            if img:
                story.append(Spacer(1, 0.3 * cm))
                story.append(img)
    else:
        story.append(
            Paragraph(
                f"Data not available. {kaggle_data.get('error') or ''}",
                styles["BodyText"],
            )
        )

    story.append(Spacer(1, 1 * cm))
    story.append(
        Paragraph(
            "Report generated by Developer Analytics Dashboard.",
            styles["MetaText"],
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
