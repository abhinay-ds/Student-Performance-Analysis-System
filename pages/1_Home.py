"""
Page 1: Home Dashboard (Personalized for Students and Professors).
Displays complete academic overview, authorized subjects, KPI indicators,
subject-wise performance charts, attendance summaries, assignments, and alerts.
"""

import streamlit as st
import pandas as pd
import database
import auth
import permissions
import attendance_service
import academic_service
import analytics
import ui_theme

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

if not permissions.is_authenticated():
    st.warning("Access restricted. Please sign in to the portal.")
    st.stop()

# ============================================================================
# STUDENT DASHBOARD VIEW
# ============================================================================
if permissions.is_student():
    student = permissions.get_current_student_profile()
    if not student:
        st.info("No student profile linked to this session.")
        st.stop()

    stu_id = student["id"]

    # Student Modern Header
    ui_theme.render_header(
        title=f"Welcome, {student['full_name']}",
        subtitle=f"Student ID: {student['student_id']} | {student['department']} | {student['course']} (Semester {student['semester']})",
        badge_text="Enrolled Student",
        badge_variant="primary",
    )

    # Calculate Student Metrics
    att_info = attendance_service.get_student_overall_attendance(stu_id)
    acad_info = academic_service.get_student_academic_summary(stu_id)

    # Summary KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Overall Attendance", f"{att_info['percentage']}%",
                "Below 75%" if att_info["is_low_attendance"] else "Good Standing",
                delta_color="inverse" if att_info["is_low_attendance"] else "normal")
    col2.metric("Overall Average Marks", f"{acad_info['average_marks']} / 100")
    col3.metric("Enrolled Subjects", acad_info["enrolled_subjects"])
    col4.metric("Pending Assignments", acad_info["pending_assignments"],
                "Action Required" if acad_info["pending_assignments"] > 0 else "All Clear",
                delta_color="inverse" if acad_info["pending_assignments"] > 0 else "normal")
    col5.metric("Announcements", acad_info["new_announcements"])

    # Attendance Warning Banner if < 75%
    if att_info["is_low_attendance"]:
        st.error(
            f"Attendance Advisory: Your cumulative attendance is {att_info['percentage']}%, "
            "which is below the mandatory university threshold of 75%. Please contact your course instructors."
        )

    st.write("")

    # Left and Right Columns
    c_left, c_right = st.columns([3, 2])

    with c_left:
        st.subheader("Subject-Wise Performance Breakdown")
        student_records = database.get_academic_records_detailed(student_internal_id=stu_id)
        if not student_records.empty:
            enriched = analytics.enrich_academic_records(student_records)

            # Bar Chart
            comp_fig = analytics.plot_student_comparison_bar(enriched, metric="total_marks")
            if comp_fig:
                st.plotly_chart(comp_fig, use_container_width=True, key="home_student_comp_fig")

            st.write("**Recent Examination Results**")
            st.dataframe(
                enriched[
                    ["subject", "examination_type", "internal_marks", "assignment_marks", "exam_marks", "total_marks", "grade", "exam_date"]
                ].rename(
                    columns={
                        "subject": "Subject",
                        "examination_type": "Exam Period",
                        "internal_marks": "Int (20)",
                        "assignment_marks": "Asgn (10)",
                        "exam_marks": "Exam (70)",
                        "total_marks": "Total",
                        "grade": "Grade",
                        "exam_date": "Date",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

            # Historical Trend if multiple dates exist
            trend_fig = analytics.plot_exam_trends(enriched)
            if trend_fig:
                st.write("**Academic Progress Trajectory**")
                st.plotly_chart(trend_fig, use_container_width=True, key="home_student_trend_fig")

        else:
            st.info("No examination evaluation records recorded yet.")

    with c_right:
        st.subheader("Attendance Overview")
        sub_att = attendance_service.get_student_subject_breakdown(stu_id)
        if not sub_att.empty:
            st.dataframe(
                sub_att[["subject_name", "attended_sessions", "total_sessions", "attendance_percentage"]].rename(
                    columns={
                        "subject_name": "Subject",
                        "attended_sessions": "Attended",
                        "total_sessions": "Total",
                        "attendance_percentage": "Attendance %",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No subject attendance logs available.")

        st.subheader("Coursework Due & Deadlines")
        assigns_df = database.get_assignments(course=student["course"], semester=student["semester"])
        if not assigns_df.empty:
            for _, assign in assigns_df.head(3).iterrows():
                sub_status = database.get_student_assignment_status(assign["id"], stu_id)
                status_txt = sub_status["submission_status"] if sub_status else "Pending"
                st.write(f"• **{assign['title']}** ({assign['subject_name']})")
                st.caption(f"Due: **{assign['due_date']}** | Status: `{status_txt}`")
        else:
            st.info("No pending coursework deadlines.")

        st.subheader("Campus Announcements")
        announcements_df = database.get_announcements_for_student(
            student["department"], student["course"], student["semester"]
        )
        if not announcements_df.empty:
            for _, ann in announcements_df.head(2).iterrows():
                st.markdown(f"**{ann['title']}**")
                st.caption(f"Published on {ann['created_at'][:10]}")
                st.write(ann["message"][:140] + ("..." if len(ann["message"]) > 140 else ""))
                st.divider()

        st.subheader("Study Resources")
        mats_df = database.get_study_materials(course=student["course"], semester=student["semester"])
        if not mats_df.empty:
            for _, mat in mats_df.head(2).iterrows():
                st.write(f"📄 **{mat['title']}** ({mat['subject_name']})")
                st.caption(f"Uploaded on {mat['uploaded_at'][:10]}")

# ============================================================================
# COORDINATOR DASHBOARD VIEW (Comprehensive Academic Governance)
# ============================================================================
elif permissions.is_coordinator():
    curr_user = permissions.get_current_user() or {}
    user_display = curr_user.get("username", "Coordinator")
    inst_name = database.get_system_setting("institution_name", default="Campus Performance Portal")
    acad_term = database.get_system_setting("current_academic_year", default="2024-2025")

    ui_theme.render_header(
        title=f"{inst_name} — Academic Governance",
        subtitle=f"Administrator: {user_display} | Academic Term: {acad_term}",
        badge_text="Institutional Governance",
        badge_variant="primary",
    )

    # Database Queries
    all_students = database.get_all_students()
    all_profs = database.get_all_professors_detailed()
    all_subjects = database.get_all_subjects()
    all_courses = database.get_all_courses()
    all_academic_recs = database.get_academic_records_detailed()
    audit_recent = database.get_audit_logs(limit=6)

    # Calculate Institution-Wide Metrics
    active_stu_count = len(all_students[all_students["is_active"] == 1]) if "is_active" in all_students.columns else len(all_students)
    active_prof_count = len(all_profs[all_profs["is_active"] == 1]) if "is_active" in all_profs.columns else len(all_profs)
    active_subj_count = len(all_subjects[all_subjects["is_active"] == 1]) if "is_active" in all_subjects.columns else len(all_subjects)
    active_course_count = len(all_courses[all_courses["is_active"] == 1]) if "is_active" in all_courses.columns else len(all_courses)

    # Average Attendance across all enrolled students
    att_pcts = []
    for _, stu in all_students.iterrows():
        att_stat = attendance_service.get_student_overall_attendance(stu["id"])
        att_pcts.append(att_stat["percentage"])
    inst_avg_att = round(sum(att_pcts) / max(1, len(att_pcts)), 1) if att_pcts else 0.0

    # Average Academic Score
    inst_avg_score = round(float(all_academic_recs["total_marks"].mean()), 1) if not all_academic_recs.empty and "total_marks" in all_academic_recs.columns else 0.0

    # Students Requiring Support (<75% attendance or failing scores)
    at_risk_df = analytics.get_at_risk_students(all_academic_recs, score_threshold=50.0, attendance_threshold=75.0) if not all_academic_recs.empty else pd.DataFrame()
    support_count = len(at_risk_df["student_id"].unique()) if not at_risk_df.empty else 0

    # Pending Approvals
    pending_approvals = len(all_academic_recs[all_academic_recs["is_approved"] == 0]) if not all_academic_recs.empty and "is_approved" in all_academic_recs.columns else 0

    # Top KPI Metrics Cards
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Active Students", active_stu_count)
    k2.metric("Active Faculty", active_prof_count)
    k3.metric("Accredited Subjects", active_subj_count)
    k4.metric("Degree Programs", max(active_course_count, 4))

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Campus Avg Attendance", f"{inst_avg_att}%")
    k6.metric("Campus Avg Marks", f"{inst_avg_score} / 100")
    k7.metric("Students Needing Support", support_count, delta="Requires Attention" if support_count > 0 else "Optimal", delta_color="inverse")
    k8.metric("Pending Result Approvals", pending_approvals, delta="Action Required" if pending_approvals > 0 else "All Approved", delta_color="inverse")

    st.write("")

    # Visualizations Row 1: Enrollment by Department & Subject Performance
    g1, g2 = st.columns([1, 1])
    with g1:
        st.subheader("Student Enrollment by Department")
        if not all_students.empty:
            import plotly.express as px
            dept_counts = all_students["department"].value_counts().reset_index()
            dept_counts.columns = ["Department", "Enrolled Students"]
            fig_dept = px.bar(
                dept_counts,
                x="Enrolled Students",
                y="Department",
                orientation="h",
                color_discrete_sequence=["#142B4A"],
                text="Enrolled Students",
            )
            fig_dept.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=280,
                xaxis_title="Students",
                yaxis_title="",
            )
            ui_theme.apply_plotly_theme(fig_dept)
            st.plotly_chart(fig_dept, use_container_width=True, key="home_coord_dept_fig")
        else:
            st.info("No students enrolled.")

    with g2:
        st.subheader("Subject-Wise Performance Comparison")
        if not all_academic_recs.empty:
            s_perf = analytics.get_subject_performance(all_academic_recs)
            fig_s = analytics.plot_subject_averages(s_perf)
            if fig_s:
                st.plotly_chart(fig_s, use_container_width=True, key="home_coord_subj_fig")
        else:
            st.info("No subject evaluation records available.")

    st.write("")

    # Visualizations Row 2: Attendance vs Score & Grade Distribution
    g3, g4 = st.columns([1, 1])
    with g3:
        st.subheader("Attendance vs Marks Correlation")
        if not all_academic_recs.empty:
            fig_corr = analytics.plot_attendance_vs_score(all_academic_recs)
            if fig_corr:
                st.plotly_chart(fig_corr, use_container_width=True, key="home_coord_corr_fig")
        else:
            st.info("No marks data to plot.")

    with g4:
        st.subheader("Institutional Grade Distribution")
        if not all_academic_recs.empty:
            g_dist = analytics.get_grade_distribution(all_academic_recs)
            fig_g = analytics.plot_grade_distribution(g_dist)
            if fig_g:
                st.plotly_chart(fig_g, use_container_width=True, key="home_coord_grade_fig")
        else:
            st.info("No grades cataloged.")

    st.write("")

    # Administrative Activity & Compliance
    col_act, col_alert = st.columns([3, 2])
    with col_act:
        st.subheader("Recent Administrative Audit Activity")
        if not audit_recent.empty:
            st.dataframe(
                audit_recent[["created_at", "username", "action", "entity_type", "reason"]].rename(columns={
                    "created_at": "Timestamp",
                    "username": "Actor",
                    "action": "Action",
                    "entity_type": "Entity",
                    "reason": "Justification Reason",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No administrative events logged yet.")

    with col_alert:
        st.subheader("Institutional Quality Indicators")
        if support_count > 0:
            st.warning(f"**{support_count} student(s)** flagged for low attendance (<75%) or failing scores.")
        else:
            st.success("All student cohorts currently meet or exceed attendance and score benchmarks.")

        # Subject coverage indicator
        unassigned_subjects = [
            s["subject_name"] for _, s in all_subjects.iterrows()
            if not database.get_subject_assigned_professors(s["id"])
        ]
        if unassigned_subjects:
            st.info(f"**{len(unassigned_subjects)} subject(s)** currently lack specific faculty assignments.")
        else:
            st.success("All institutional curriculum subjects have assigned faculty.")

# ============================================================================
# PROFESSOR DASHBOARD VIEW (Scoped to Authorized Subjects)
# ============================================================================
else:
    prof_username = permissions.get_active_professor_username()
    auth_subjects = permissions.get_professor_authorized_subjects(prof_username)
    prof_display_name = "Dr. Neha Kapoor" if prof_username == "dr_kapoor" else ("Prof. Arjun Malhotra" if prof_username == "prof_malhotra" else "Faculty")

    ui_theme.render_header(
        title=f"{prof_display_name}'s Faculty Dashboard",
        subtitle=f"Authorized Courses: {', '.join(auth_subjects)} | Department: Computer Science and Engineering",
        badge_text="Faculty Member",
        badge_variant="info",
    )

    # Retrieve only records belonging to authorized subjects
    all_recs_raw = database.get_academic_records_detailed(department="Computer Science and Engineering", semester=3)
    if not all_recs_raw.empty:
        authorized_recs = all_recs_raw[all_recs_raw["subject"].isin(auth_subjects)].copy()
    else:
        authorized_recs = all_recs_raw

    # Enrolled students in this semester
    enrolled_students = database.get_all_students(department="Computer Science and Engineering", semester=3)

    # Calculate Metrics for Authorized Classes
    kpis = analytics.calculate_kpis(authorized_recs, len(enrolled_students))

    # Assigned Subjects Attendance Average
    all_att_summaries = []
    for _, stu in enrolled_students.iterrows():
        att_s = attendance_service.get_student_overall_attendance(stu["id"])
        all_att_summaries.append(att_s["percentage"])
    avg_class_attendance = round(sum(all_att_summaries) / max(1, len(all_att_summaries)), 1) if all_att_summaries else 0.0

    # Pending Assignments in Professor's Subjects
    all_assigns = database.get_assignments(course="B.Tech", semester=3)
    prof_assigns = all_assigns[all_assigns["subject_name"].isin(auth_subjects)] if not all_assigns.empty else all_assigns

    # Materials in Professor's Subjects
    all_mats = database.get_study_materials(course="B.Tech", semester=3)
    prof_mats = all_mats[all_mats["subject_name"].isin(auth_subjects)] if not all_mats.empty else all_mats

    # Top KPI Summary Cards
    pk1, pk2, pk3, pk4, pk5, pk6 = st.columns(6)
    pk1.metric("Class Students", len(enrolled_students))
    pk2.metric("Academic Records", kpis["total_records"])
    pk3.metric("Average Marks", f"{kpis['avg_marks']} / 100")
    pk4.metric("Average Attendance", f"{avg_class_attendance}%")
    pk5.metric("Active Assignments", len(prof_assigns))
    pk6.metric("Uploaded Resources", len(prof_mats))

    st.write("")

    # Visualizations Row 1: Subject Averages & Grade Distribution
    vc1, vc2 = st.columns([3, 2])
    with vc1:
        st.subheader("Subject-Wise Average Marks")
        if not authorized_recs.empty:
            s_perf = analytics.get_subject_performance(authorized_recs)
            fig_s = analytics.plot_subject_averages(s_perf)
            if fig_s:
                st.plotly_chart(fig_s, use_container_width=True, key="home_prof_subj_fig")
        else:
            st.info("No evaluation records available for assigned subjects.")

    with vc2:
        st.subheader("Grade Allocation & Pass Ratio")
        if not authorized_recs.empty:
            g_dist = analytics.get_grade_distribution(authorized_recs)
            fig_g = analytics.plot_grade_distribution(g_dist)
            if fig_g:
                st.plotly_chart(fig_g, use_container_width=True, key="home_prof_grade_fig")
        else:
            st.info("No grade distribution to display.")

    st.write("")

    # Visualizations Row 2: Attendance vs Performance Correlation & At-Risk
    vc3, vc4 = st.columns([3, 2])
    with vc3:
        st.subheader("Attendance vs Marks Correlation")
        fig_scat = analytics.plot_attendance_vs_score(authorized_recs)
        if fig_scat:
            st.plotly_chart(fig_scat, use_container_width=True, key="home_prof_corr_fig")
        else:
            st.info("Attendance correlation chart.")

    with vc4:
        st.subheader("Students Requiring Academic Support")
        at_risk = analytics.get_at_risk_students(authorized_recs, score_threshold=50.0, attendance_threshold=75.0)
        if not at_risk.empty:
            st.warning(f"Found **{len(at_risk)}** evaluations requiring attention:")
            st.dataframe(
                at_risk[["student_id", "full_name", "subject", "total_marks", "attendance_percentage", "reason"]].rename(
                    columns={
                        "student_id": "Roll No",
                        "full_name": "Student",
                        "subject": "Subject",
                        "total_marks": "Marks",
                        "attendance_percentage": "Att %",
                        "reason": "Flag",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("All students in assigned courses are currently in good standing.")

    # Historical Examination Trends
    if not authorized_recs.empty:
        trend_chart = analytics.plot_exam_trends(authorized_recs)
        if trend_chart:
            st.write("")
            st.subheader("Academic Improvement Trajectory Across Examination Periods")
            st.plotly_chart(trend_chart, use_container_width=True, key="home_prof_trend_fig")
