"""
Page 3: Student Academic Performance.
Presents detailed subject marks, internal/continuous assessments, final exam scores,
automatic letter grades, GPA points, and interactive performance charts.
Read-only for students.
"""

import streamlit as st
import database
import auth
import permissions
import analytics
import ui_theme

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

if not permissions.is_authenticated():
    st.warning("Access restricted. Please sign in to the portal.")
    st.stop()

student = permissions.get_current_student_profile()
if not student:
    st.info("No student profile linked to this session.")
    st.stop()

stu_id = student["id"]

ui_theme.render_header(
    title="Academic Performance & Results",
    subtitle=f"Official evaluations and grade transcripts for {student['full_name']} ({student['student_id']})",
    badge_text="Academic Results",
    badge_variant="primary",
)

# Fetch Academic Records for this student only
records_df = database.get_academic_records_detailed(student_internal_id=stu_id)

if records_df.empty:
    st.info("No official examination marks or evaluation records found for your account.")
    st.stop()

enriched = analytics.enrich_academic_records(records_df)

# Executive Performance Metrics
m_avg = round(float(enriched["total_marks"].mean()), 1)
m_high = round(float(enriched["total_marks"].max()), 1)
m_low = round(float(enriched["total_marks"].min()), 1)
cleared_count = int((enriched["total_marks"] >= 40.0).sum())
total_subs = len(enriched)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cumulative Average", f"{m_avg} / 100")
c2.metric("Highest Subject Score", f"{m_high}")
c3.metric("Lowest Subject Score", f"{m_low}")
c4.metric("Subjects Cleared", f"{cleared_count} / {total_subs}")

st.write("")

# Subject Marks Table
st.subheader("Subject Score Details & Letter Grades")
st.dataframe(
    enriched[
        [
            "subject",
            "internal_marks",
            "assignment_marks",
            "exam_marks",
            "total_marks",
            "grade",
            "grade_desc",
            "grade_point",
            "attendance_percentage",
            "exam_date",
        ]
    ].rename(
        columns={
            "subject": "Subject Name",
            "internal_marks": "Internal (20)",
            "assignment_marks": "Asgn (10)",
            "exam_marks": "Exam (70)",
            "total_marks": "Total Score",
            "grade": "Grade",
            "grade_desc": "Remarks",
            "grade_point": "GPA Point",
            "attendance_percentage": "Attendance %",
            "exam_date": "Evaluation Date",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

st.write("")

# Interactive Performance Chart
st.subheader("Performance Visualizations")
chart_col1, chart_col2 = st.columns([3, 2])

with chart_col1:
    fig_comp = analytics.plot_student_comparison_bar(enriched, metric="total_marks")
    if fig_comp:
        st.plotly_chart(fig_comp, use_container_width=True, key="student_perf_comp_bar")

with chart_col2:
    fig_donut = analytics.plot_pass_fail_donut(cleared_count, total_subs - cleared_count)
    if fig_donut:
        st.plotly_chart(fig_donut, use_container_width=True, key="student_perf_pass_donut")
