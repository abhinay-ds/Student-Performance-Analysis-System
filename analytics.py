"""
Analytics and Visualizations Module for Student Performance Analysis System.
Computes KPIs, grade allocations, subject performance aggregations, attendance
correlations, and renders interactive Plotly figures.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from validators import calculate_grade, is_passing, is_academic_support_needed
from config import PASS_MARK_THRESHOLD, ATTENDANCE_SUPPORT_THRESHOLD, SUPPORT_NEEDED_SCORE_THRESHOLD
import ui_theme


# ============================================================================
# Core Statistical Metrics and KPIs
# ============================================================================

def enrich_academic_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich records DataFrame with computed columns:
    - total_marks
    - grade
    - grade_point
    - grade_desc
    - is_pass
    - needs_support
    """
    if df.empty:
        return df.copy()

    df = df.copy()
    if "total_marks" not in df.columns:
        df["total_marks"] = df["internal_marks"] + df["assignment_marks"] + df["exam_marks"]

    grades_info = df["total_marks"].apply(calculate_grade)
    df["grade"] = [g[0] for g in grades_info]
    df["grade_point"] = [g[1] for g in grades_info]
    df["grade_desc"] = [g[2] for g in grades_info]

    df["is_pass"] = df["total_marks"].apply(is_passing)
    df["needs_support"] = df.apply(
        lambda r: is_academic_support_needed(r["total_marks"], r["attendance_percentage"]),
        axis=1,
    )
    return df


def calculate_kpis(records_df: pd.DataFrame, total_students_count: int) -> Dict[str, Any]:
    """
    Compute executive summary KPIs from enriched academic records.
    Handles empty state gracefully.
    """
    if records_df.empty:
        return {
            "total_students": total_students_count,
            "total_records": 0,
            "avg_marks": 0.0,
            "highest_marks": 0.0,
            "lowest_marks": 0.0,
            "pass_percentage": 0.0,
            "pass_count": 0,
            "fail_count": 0,
            "avg_attendance": 0.0,
            "support_needed_count": 0,
        }

    df = enrich_academic_records(records_df)

    # Calculate student-level support needs
    student_support = df.groupby("student_id")["needs_support"].any()
    support_students_count = int(student_support.sum())

    total_records = len(df)
    pass_count = int(df["is_pass"].sum())
    fail_count = total_records - pass_count
    pass_pct = round((pass_count / total_records) * 100.0, 1) if total_records > 0 else 0.0

    return {
        "total_students": total_students_count,
        "total_records": total_records,
        "avg_marks": round(float(df["total_marks"].mean()), 2),
        "highest_marks": round(float(df["total_marks"].max()), 2),
        "lowest_marks": round(float(df["total_marks"].min()), 2),
        "pass_percentage": pass_pct,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "avg_attendance": round(float(df["attendance_percentage"].mean()), 1),
        "support_needed_count": support_students_count,
    }


def get_subject_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group academic records by subject, computing average marks, average attendance,
    highest, lowest, and pass rate.
    """
    if df.empty:
        return pd.DataFrame()

    enriched = enrich_academic_records(df)
    grouped = enriched.groupby("subject").agg(
        record_count=("record_id", "count"),
        avg_total=("total_marks", "mean"),
        avg_internal=("internal_marks", "mean"),
        avg_assignment=("assignment_marks", "mean"),
        avg_exam=("exam_marks", "mean"),
        avg_attendance=("attendance_percentage", "mean"),
        max_marks=("total_marks", "max"),
        min_marks=("total_marks", "min"),
        passed_count=("is_pass", "sum"),
    ).reset_index()

    grouped["avg_total"] = grouped["avg_total"].round(2)
    grouped["avg_internal"] = grouped["avg_internal"].round(2)
    grouped["avg_assignment"] = grouped["avg_assignment"].round(2)
    grouped["avg_exam"] = grouped["avg_exam"].round(2)
    grouped["avg_attendance"] = grouped["avg_attendance"].round(1)
    grouped["pass_percentage"] = (
        (grouped["passed_count"] / grouped["record_count"]) * 100.0
    ).round(1)

    return grouped.sort_values(by="avg_total", ascending=False)


def get_grade_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Return count and percentage for each letter grade."""
    if df.empty:
        return pd.DataFrame()

    enriched = enrich_academic_records(df)
    order = ["O", "A+", "A", "B+", "B", "C", "F"]
    counts = enriched["grade"].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ["grade", "count"]
    total = counts["count"].sum()
    counts["percentage"] = ((counts["count"] / total) * 100.0).round(1) if total > 0 else 0.0
    return counts


def get_student_rankings(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate student-level aggregate performance across all their taken subjects."""
    if df.empty:
        return pd.DataFrame()

    enriched = enrich_academic_records(df)
    summary = enriched.groupby(["student_id", "full_name", "department", "semester"]).agg(
        subjects_taken=("subject", "count"),
        avg_marks=("total_marks", "mean"),
        avg_attendance=("attendance_percentage", "mean"),
        total_score=("total_marks", "sum"),
        failed_subjects=("is_pass", lambda x: int((~x).sum())),
    ).reset_index()

    summary["avg_marks"] = summary["avg_marks"].round(2)
    summary["avg_attendance"] = summary["avg_attendance"].round(1)
    summary["overall_grade"] = summary["avg_marks"].apply(lambda m: calculate_grade(m)[0])
    summary["rank"] = summary["avg_marks"].rank(ascending=False, method="min").astype(int)

    return summary.sort_values(by="rank")


def get_at_risk_students(
    df: pd.DataFrame,
    score_threshold: float = SUPPORT_NEEDED_SCORE_THRESHOLD,
    attendance_threshold: float = ATTENDANCE_SUPPORT_THRESHOLD,
) -> pd.DataFrame:
    """Filter records of students needing academic intervention."""
    if df.empty:
        return pd.DataFrame()

    enriched = enrich_academic_records(df)
    flagged = enriched[
        (enriched["total_marks"] < score_threshold)
        | (enriched["attendance_percentage"] < attendance_threshold)
    ].copy()

    flagged["reason"] = flagged.apply(
        lambda r: (
            "Low Marks & Low Attendance"
            if r["total_marks"] < score_threshold and r["attendance_percentage"] < attendance_threshold
            else ("Low Marks" if r["total_marks"] < score_threshold else "Low Attendance")
        ),
        axis=1,
    )
    return flagged


# ============================================================================
# Plotly Interactive Visualizations
# ============================================================================

def plot_subject_averages(subject_df: pd.DataFrame) -> Optional[go.Figure]:
    """Bar chart comparing subject-wise average marks and components."""
    if subject_df.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=subject_df["subject"],
        y=subject_df["avg_internal"],
        name="Internal (Max 20)",
        marker_color="#2563EB",
    ))
    fig.add_trace(go.Bar(
        x=subject_df["subject"],
        y=subject_df["avg_assignment"],
        name="Assignment (Max 10)",
        marker_color="#16A34A",
    ))
    fig.add_trace(go.Bar(
        x=subject_df["subject"],
        y=subject_df["avg_exam"],
        name="Exam (Max 70)",
        marker_color="#142B4A",
    ))

    fig.update_layout(
        barmode="stack",
        title="Subject-wise Marks Breakdown (Internal + Assignment + Exam)",
        xaxis_title="Subject",
        yaxis_title="Average Score",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        height=420,
    )
    return ui_theme.apply_plotly_theme(fig)


def plot_grade_distribution(grade_df: pd.DataFrame) -> Optional[go.Figure]:
    """Donut chart for grade distribution."""
    if grade_df.empty or grade_df["count"].sum() == 0:
        return None

    palette = {
        "O": "#16A34A",
        "A+": "#22C55E",
        "A": "#34D399",
        "B+": "#2563EB",
        "B": "#0284C7",
        "C": "#D97706",
        "F": "#DC2626",
    }
    colors = [palette.get(g, "#94A3B8") for g in grade_df["grade"]]

    fig = go.Figure(data=[go.Pie(
        labels=grade_df["grade"],
        values=grade_df["count"],
        hole=0.52,
        marker=dict(colors=colors),
        textinfo="label+percent",
        hoverinfo="label+value+percent",
    )])
    fig.update_layout(
        title="Overall Grade Distribution",
        template="plotly_white",
        height=380,
    )
    return ui_theme.apply_plotly_theme(fig)


def plot_pass_fail_donut(pass_count: int, fail_count: int) -> Optional[go.Figure]:
    """Donut chart for pass versus fail classification."""
    total = pass_count + fail_count
    if total == 0:
        return None

    fig = go.Figure(data=[go.Pie(
        labels=["Passed", "Failed"],
        values=[pass_count, fail_count],
        hole=0.6,
        marker=dict(colors=["#16A34A", "#DC2626"]),
        textinfo="label+percent",
    )])
    fig.update_layout(
        title="Pass vs Fail Ratio",
        template="plotly_white",
        height=300,
        annotations=[dict(text=f"{round((pass_count/total)*100, 1)}%", x=0.5, y=0.5, font_size=20, font_family="-apple-system, sans-serif", font_color="#142B4A", showarrow=False)],
    )
    return ui_theme.apply_plotly_theme(fig)


def plot_attendance_vs_score(df: pd.DataFrame) -> Optional[go.Figure]:
    """
    Scatter plot illustrating correlation between attendance and total marks.
    Includes threshold highlight lines.
    """
    if df.empty or len(df) < 2:
        return None

    enriched = enrich_academic_records(df)

    fig = px.scatter(
        enriched,
        x="attendance_percentage",
        y="total_marks",
        color="grade",
        hover_data=["student_id", "full_name", "subject"],
        title="Relationship Between Attendance & Academic Performance",
        labels={"attendance_percentage": "Attendance Percentage (%)", "total_marks": "Total Marks (out of 100)"},
        template="plotly_white",
    )

    # Reference threshold lines
    fig.add_hline(
        y=PASS_MARK_THRESHOLD,
        line_dash="dash",
        line_color="#DC2626",
        annotation_text=f"Pass Threshold ({PASS_MARK_THRESHOLD})",
    )
    fig.add_vline(
        x=ATTENDANCE_SUPPORT_THRESHOLD,
        line_dash="dot",
        line_color="#D97706",
        annotation_text=f"Min Attendance ({ATTENDANCE_SUPPORT_THRESHOLD}%)",
    )

    fig.update_layout(height=420)
    return ui_theme.apply_plotly_theme(fig)


def plot_student_comparison_bar(df: pd.DataFrame, metric: str = "total_marks") -> Optional[go.Figure]:
    """Bar chart comparing selected students across subjects."""
    if df.empty:
        return None

    enriched = enrich_academic_records(df)
    fig = px.bar(
        enriched,
        x="subject",
        y=metric,
        color="student_id",
        barmode="group",
        title=f"Student Score Comparison by Subject ({metric.replace('_', ' ').title()})",
        labels={"subject": "Subject", metric: "Score", "student_id": "Student ID"},
        template="plotly_white",
    )
    fig.update_layout(height=400)
    return ui_theme.apply_plotly_theme(fig)


def plot_exam_trends(df: pd.DataFrame) -> Optional[go.Figure]:
    """Line chart tracking average marks across examination periods."""
    if df.empty or "exam_date" not in df.columns:
        return None

    enriched = enrich_academic_records(df)
    date_group = enriched.groupby("exam_date").agg(
        avg_score=("total_marks", "mean"),
        count=("record_id", "count"),
    ).reset_index().sort_values(by="exam_date")

    if len(date_group) < 2:
        return None  # Trend line requires at least two points to avoid misleading chart

    fig = px.line(
        date_group,
        x="exam_date",
        y="avg_score",
        markers=True,
        title="Historical Academic Performance Trend",
        labels={"exam_date": "Examination Date", "avg_score": "Average Total Marks"},
        template="plotly_white",
    )
    fig.update_layout(height=350)
    return ui_theme.apply_plotly_theme(fig)
