"""
Enrollment & Academic Allocations Management (Coordinator / Admin Only).
Allows batch and individual student enrollment in academic subjects,
and assigning professors to teaching responsibilities.
"""

import streamlit as st
import database
import auth
import permissions
import ui_theme
from config import ROLE_COORDINATOR, ROLE_ADMIN, COURSES, SEMESTERS

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

permissions.require_role([ROLE_COORDINATOR, ROLE_ADMIN, "demo_coordinator"])

ui_theme.render_header(
    title="Enrollments & Academic Allocations",
    subtitle="Administer student course enrollments, cohort batch registrations, and faculty teaching allocations",
    badge_text="Curricular Allocations",
    badge_variant="primary",
)

current_user = permissions.get_current_user()

tab_stu_enroll, tab_cohort_enroll, tab_overview = st.tabs([
    "Individual Student Enrollment",
    "Batch Cohort Enrollment",
    "Institutional Allocation Matrix"
])

all_students = database.get_all_students()
all_subjects = database.get_all_subjects()

# ============================================================================
# TAB 1: Individual Student Enrollment
# ============================================================================
with tab_stu_enroll:
    st.subheader("Manage Individual Student Subject Enrollments")
    if not all_students.empty and not all_subjects.empty:
        stu_opts = {r["id"]: f"{r['student_id']} - {r['full_name']} ({r['course']} Sem {r['semester']})" for _, r in all_students.iterrows()}
        sel_stu_id = st.selectbox("Select Student", list(stu_opts.keys()), format_func=lambda k: stu_opts[k], key="single_stu_sel")
        stu_row = all_students[all_students["id"] == sel_stu_id].iloc[0]

        # Enrolled Subjects
        col_en1, col_en2 = st.columns([1, 1])
        with col_en1:
            st.write(f"##### 📚 Enrolled Subjects for {stu_row['full_name']}")
            enrolled_df = database.get_student_enrolled_subjects(sel_stu_id)
            if not enrolled_df.empty:
                for _, s_row in enrolled_df.iterrows():
                    c_txt, c_btn = st.columns([3, 1])
                    c_txt.write(f"• **{s_row['subject_code']}**: {s_row['subject_name']} ({s_row['credits']} Credits)")
                    if c_btn.button("Unenroll", key=f"unenroll_{sel_stu_id}_{s_row['subject_id']}"):
                        database.unenroll_student_from_subject(sel_stu_id, s_row["subject_id"])
                        database.log_audit_action(
                            username=current_user.get("username", "coordinator") if current_user else "coordinator",
                            role="coordinator",
                            action="UNENROLL_STUDENT",
                            entity_type="STUDENT_SUBJECT",
                            entity_id=f"student:{sel_stu_id}_subject:{s_row['subject_id']}",
                            old_values=f"Unenrolled {stu_row['student_id']} from {s_row['subject_name']}",
                            reason="Individual enrollment modified by coordinator",
                        )
                        st.rerun()
            else:
                st.info("Student is not currently enrolled in any subjects.")

        with col_en2:
            st.write("##### ➕ Enroll in New Subject")
            # Suggest matching course & semester
            filtered_subs = all_subjects[
                (all_subjects["course"] == stu_row["course"]) &
                (all_subjects["semester"] == stu_row["semester"]) &
                (all_subjects["is_active"] == 1)
            ]
            if filtered_subs.empty:
                filtered_subs = all_subjects[all_subjects["is_active"] == 1]

            sub_opts = {r["id"]: f"{r['subject_code']} - {r['subject_name']} (Sem {r['semester']})" for _, r in filtered_subs.iterrows()}
            enroll_sub_id = st.selectbox("Select Subject to Add", list(sub_opts.keys()), format_func=lambda k: sub_opts[k])
            acad_yr = st.text_input("Academic Term Year", value="2024-2025", key="single_acad_yr")

            if st.button("Enroll Student in Subject", type="primary"):
                database.enroll_student_in_subject(sel_stu_id, enroll_sub_id, academic_year=acad_yr)
                database.log_audit_action(
                    username=current_user.get("username", "coordinator") if current_user else "coordinator",
                    role="coordinator",
                    action="ENROLL_STUDENT",
                    entity_type="STUDENT_SUBJECT",
                    entity_id=f"student:{sel_stu_id}_subject:{enroll_sub_id}",
                    new_values=f"Enrolled {stu_row['student_id']} in {sub_opts[enroll_sub_id]}",
                    reason="Manual subject enrollment by coordinator",
                )
                st.success("Enrollment saved successfully.")
                st.rerun()
    else:
        st.info("No students or subjects available.")

# ============================================================================
# TAB 2: Batch Cohort Enrollment
# ============================================================================
with tab_cohort_enroll:
    st.subheader("Batch Cohort Auto-Enrollment")
    st.caption("Enroll an entire batch or semester cohort into all curriculum subjects matching their course and semester.")

    b_course = st.selectbox("Cohort Degree Program", COURSES, key="batch_c")
    b_sem = st.selectbox("Cohort Semester", SEMESTERS, index=2, key="batch_s")
    b_year = st.text_input("Academic Term Year", value="2024-2025", key="batch_yr")

    cohort_students = database.get_all_students(course=b_course, semester=b_sem)
    cohort_subjects = database.get_all_subjects(course=b_course, semester=b_sem)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.write(f"**Cohort Students Found:** `{len(cohort_students)}`")
        if not cohort_students.empty:
            st.dataframe(cohort_students[["student_id", "full_name", "department"]], use_container_width=True, hide_index=True)
    with col_b2:
        st.write(f"**Cohort Curriculum Subjects:** `{len(cohort_subjects)}`")
        if not cohort_subjects.empty:
            st.dataframe(cohort_subjects[["subject_code", "subject_name", "credits"]], use_container_width=True, hide_index=True)

    if not cohort_students.empty and not cohort_subjects.empty:
        if st.button("🚀 Enroll Entire Cohort into Matching Subjects", type="primary"):
            enrolled_count = 0
            for _, s_row in cohort_students.iterrows():
                for _, sub_row in cohort_subjects.iterrows():
                    database.enroll_student_in_subject(s_row["id"], sub_row["id"], academic_year=b_year)
                    enrolled_count += 1

            database.log_audit_action(
                username=current_user.get("username", "coordinator") if current_user else "coordinator",
                role="coordinator",
                action="BATCH_ENROLL_COHORT",
                entity_type="STUDENT_SUBJECT",
                entity_id=f"{b_course}_SEM{b_sem}",
                new_values=f"Batch enrolled {len(cohort_students)} students across {len(cohort_subjects)} subjects ({enrolled_count} links)",
                reason="Curriculum semester enrollment automated by coordinator",
            )
            st.success(f"Cohort enrollment complete! {enrolled_count} enrollment records verified.")
            st.rerun()

# ============================================================================
# TAB 3: Institutional Allocation Matrix
# ============================================================================
with tab_overview:
    st.subheader("Subject-Student Enrollment Summary")
    if not all_subjects.empty:
        matrix_data = []
        for _, s in all_subjects.iterrows():
            sid = s["id"]
            stus = database.get_subject_enrolled_students(sid)
            profs = database.get_subject_assigned_professors(sid)
            matrix_data.append({
                "Subject Code": s["subject_code"],
                "Subject Name": s["subject_name"],
                "Course": s["course"],
                "Semester": s["semester"],
                "Credits": s.get("credits", 3),
                "Assigned Faculty": ", ".join([p["full_name"] for p in profs]) if profs else "Unassigned",
                "Total Students Enrolled": len(stus),
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)
    else:
        st.info("No subjects cataloged.")
