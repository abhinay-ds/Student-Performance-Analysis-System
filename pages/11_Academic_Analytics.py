"""
Page 11: Academic Analytics & Cohort Insights (Professor / Administrator Portal).
Interactive Plotly visualizations, subject performance breakdown, grade donuts,
attendance vs marks correlation scatter, and early academic intervention alerts.
"""

import streamlit as st
import pandas as pd
import numpy as np
import database
import auth
import permissions
import analytics
import ui_theme
from config import DEPARTMENTS, SEMESTERS, SUPPORT_NEEDED_SCORE_THRESHOLD, ATTENDANCE_SUPPORT_THRESHOLD

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

permissions.require_role(["professor", "admin"])

ui_theme.render_header(
    title="Academic Analytics & Cohort Insights",
    subtitle="Multi-dimensional performance evaluation, statistical correlation, and academic support alerts",
    badge_text="Cohort Analytics",
    badge_variant="primary",
)

# Sidebar Filters
with st.sidebar:
    st.header("Analytics Filters")
    f_dept = st.selectbox("Department", ["All"] + DEPARTMENTS, key="ana_p_dept")
    f_sem = st.selectbox("Semester", ["All"] + [str(s) for s in SEMESTERS], key="ana_p_sem")

    dept_val = f_dept if f_dept != "All" else None
    sem_val = int(f_sem) if f_sem != "All" else None

    # Retrieve authorized subject choices
    auth_subjects = permissions.get_professor_authorized_subjects()
    prelim_df = database.get_academic_records_detailed(department=dept_val, semester=sem_val)
    if not prelim_df.empty:
        prelim_df = prelim_df[prelim_df["subject"].isin(auth_subjects)]
    subjects_avail = ["All Authorized"] + sorted(prelim_df["subject"].dropna().unique().tolist()) if not prelim_df.empty else ["All Authorized"]
    f_subj = st.selectbox("Subject", subjects_avail, key="ana_p_subj")

    st.write("")
    st.subheader("Support Thresholds")
    thresh_marks = st.slider("Low Score Threshold", 30.0, 70.0, float(SUPPORT_NEEDED_SCORE_THRESHOLD), 5.0)
    thresh_att = st.slider("Low Attendance Threshold (%)", 50.0, 90.0, float(ATTENDANCE_SUPPORT_THRESHOLD), 5.0)

filtered_df = database.get_academic_records_detailed(
    department=dept_val,
    semester=sem_val,
    subject=f_subj if f_subj != "All Authorized" else None,
)
if not filtered_df.empty and f_subj == "All Authorized":
    filtered_df = filtered_df[filtered_df["subject"].isin(auth_subjects)]

if filtered_df.empty:
    st.info("ℹ️ No records match the active filters. Expand your filter selections.")
    st.stop()

enriched_df = analytics.enrich_academic_records(filtered_df)

# Top KPI Summary Cards
k1, k2, k3, k4, k5, k6 = st.columns(6)
n_evals = len(enriched_df)
m_avg = round(float(enriched_df["total_marks"].mean()), 1)
m_max = round(float(enriched_df["total_marks"].max()), 1)
m_min = round(float(enriched_df["total_marks"].min()), 1)
pass_n = int(enriched_df["is_pass"].sum())
pass_pct = round((pass_n / n_evals) * 100.0, 1)
att_avg = round(float(enriched_df["attendance_percentage"].mean()), 1)

k1.metric("Evaluations", n_evals)
k2.metric("Cohort Mean", f"{m_avg} / 100")
k3.metric("Highest Mark", m_max)
k4.metric("Lowest Mark", m_min)
k5.metric("Pass Rate", f"{pass_pct}%", f"{pass_n} passed")
k6.metric("Avg Attendance", f"{att_avg}%")

st.divider()

# Visualizations Row 1: Subject Performance & Grade Distribution
c1, c2 = st.columns([3, 2])
with c1:
    st.subheader("Subject-Wise Breakdown")
    s_perf = analytics.get_subject_performance(filtered_df)
    fig_s = analytics.plot_subject_averages(s_perf)
    if fig_s:
        st.plotly_chart(fig_s, use_container_width=True, key="analytics_subj_breakdown_fig")

with c2:
    st.subheader("Grade Distribution")
    g_dist = analytics.get_grade_distribution(filtered_df)
    fig_g = analytics.plot_grade_distribution(g_dist)
    if fig_g:
        st.plotly_chart(fig_g, use_container_width=True, key="analytics_grade_dist_fig")

st.divider()

# Visualizations Row 2: Attendance vs Score Correlation
c3, c4 = st.columns([3, 2])
with c3:
    st.subheader("Attendance vs Marks Correlation")
    fig_scat = analytics.plot_attendance_vs_score(filtered_df)
    if fig_scat:
        st.plotly_chart(fig_scat, use_container_width=True, key="analytics_att_score_corr_fig")
    else:
        st.info("Provide at least two records to plot correlation.")

with c4:
    st.subheader("Statistical Correlation Insights")
    if len(enriched_df) >= 3:
        corr = enriched_df["attendance_percentage"].corr(enriched_df["total_marks"])
        corr_val = round(float(corr), 3) if not np.isnan(corr) else 0.0
        st.metric("Pearson Correlation (r)", corr_val)
        if corr_val > 0.4:
            st.success("Strong positive correlation: Regular class attendance significantly improves evaluation scores.")
        elif corr_val > 0.1:
            st.info("Moderate positive correlation detected.")
        else:
            st.caption("Weak or negligible linear relationship in this sample.")
    else:
        st.caption("Requires at least 3 records for Pearson calculation.")

st.divider()

# Section: Early Intervention & At-Risk Identification
st.subheader("Academic Intervention & At-Risk Roster")
st.caption(f"Students flagged with Total Marks < {thresh_marks} OR Attendance < {thresh_att}%")

at_risk = analytics.get_at_risk_students(filtered_df, score_threshold=thresh_marks, attendance_threshold=thresh_att)
if at_risk.empty:
    st.success("All students in current filtered cohort meet or exceed the specified academic thresholds.")
else:
    st.warning(f"Found **{len(at_risk)}** student record(s) requiring academic intervention:")
    st.dataframe(
        at_risk[
            ["student_id", "full_name", "department", "semester", "subject", "total_marks", "grade", "attendance_percentage", "reason"]
        ].rename(
            columns={
                "student_id": "Student ID",
                "full_name": "Full Name",
                "department": "Department",
                "semester": "Sem",
                "subject": "Subject",
                "total_marks": "Score",
                "grade": "Grade",
                "attendance_percentage": "Attendance %",
                "reason": "Flagged For",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
