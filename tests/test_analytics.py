"""
Tests for Academic Analytics, Aggregations, Rankings, and Empty State Handling.
"""

import pytest
import pandas as pd
import analytics
import database


def test_empty_database_analytics():
    """Verify analytics handle empty DataFrames safely without crashing."""
    empty_df = pd.DataFrame()
    kpis = analytics.calculate_kpis(empty_df, total_students_count=0)

    assert kpis["total_students"] == 0
    assert kpis["total_records"] == 0
    assert kpis["avg_marks"] == 0.0
    assert kpis["pass_percentage"] == 0.0

    assert analytics.get_subject_performance(empty_df).empty
    assert analytics.get_grade_distribution(empty_df).empty
    assert analytics.get_student_rankings(empty_df).empty
    assert analytics.get_at_risk_students(empty_df).empty


def test_populated_analytics_metrics(populated_db):
    """Test analytics calculations against populated database."""
    students = database.get_all_students(db_path=populated_db)
    records = database.get_academic_records_detailed(db_path=populated_db)

    kpis = analytics.calculate_kpis(records, len(students))

    assert kpis["total_students"] == 2
    assert kpis["total_records"] == 2
    # Marks: 18+9+60=87 (Pass) and 10+5+20=35 (Fail)
    assert kpis["pass_count"] == 1
    assert kpis["fail_count"] == 1
    assert kpis["pass_percentage"] == 50.0
    # Mean marks: (87 + 35) / 2 = 61.0
    assert kpis["avg_marks"] == 61.0
    # Student 2 needs support (score 35, att 65)
    assert kpis["support_needed_count"] == 1


def test_subject_performance_aggregation(populated_db):
    """Test aggregation by subject."""
    records = database.get_academic_records_detailed(db_path=populated_db)
    subj_df = analytics.get_subject_performance(records)

    assert len(subj_df) == 1
    math_row = subj_df.iloc[0]
    assert math_row["subject"] == "Mathematics"
    assert math_row["record_count"] == 2
    assert math_row["avg_total"] == 61.0
    assert math_row["max_marks"] == 87.0
    assert math_row["min_marks"] == 35.0


def test_at_risk_student_detection(populated_db):
    """Verify at-risk students are correctly identified."""
    records = database.get_academic_records_detailed(db_path=populated_db)
    flagged = analytics.get_at_risk_students(records, score_threshold=50.0, attendance_threshold=75.0)

    assert len(flagged) == 1
    assert flagged.iloc[0]["student_id"] == "TEST102"
    assert "Low Marks & Low Attendance" in flagged.iloc[0]["reason"]


def test_plotly_chart_builders_do_not_fail(populated_db):
    """Verify Plotly figure generators execute cleanly without errors."""
    records = database.get_academic_records_detailed(db_path=populated_db)
    subj_df = analytics.get_subject_performance(records)
    grade_df = analytics.get_grade_distribution(records)

    fig_subj = analytics.plot_subject_averages(subj_df)
    assert fig_subj is not None

    fig_grade = analytics.plot_grade_distribution(grade_df)
    assert fig_grade is not None

    fig_scatter = analytics.plot_attendance_vs_score(records)
    assert fig_scatter is not None

    fig_donut = analytics.plot_pass_fail_donut(1, 1)
    assert fig_donut is not None
