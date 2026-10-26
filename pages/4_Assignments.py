"""
Page 4: Coursework Assignments Management.
Dual-mode: Students view deadlines, download resources, and submit coursework.
Professors create assignments, upload attachments, review submissions, and award grades.
"""

from datetime import date
from pathlib import Path
import streamlit as st
import database
import auth
import permissions
import academic_service
import ui_theme
from config import COURSES, SEMESTERS, DEPARTMENTS

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

if not permissions.is_authenticated():
    st.warning("Access restricted. Please sign in to the portal.")
    st.stop()

# ============================================================================
# STUDENT ASSIGNMENTS VIEW
# ============================================================================
if permissions.is_student():
    student = permissions.get_current_student_profile()
    if not student:
        st.info("No student profile linked.")
        st.stop()

    stu_id = student["id"]
    assigns_df = database.get_assignments(course=student["course"], semester=student["semester"])

    ui_theme.render_header(
        title="Coursework Assignments",
        subtitle=f"Active assignments and submissions for {student['full_name']} ({student['course']} Sem {student['semester']})",
        badge_text=f"{len(assigns_df)} Total Assigned" if not assigns_df.empty else "No Deadlines",
        badge_variant="info",
    )

    if assigns_df.empty:
        st.info("No coursework assignments currently scheduled for your course and semester.")
    else:
        for _, assign in assigns_df.iterrows():
            sub = database.get_student_assignment_status(assign["id"], stu_id)
            status = sub["submission_status"] if sub else "Pending"
            badge_var = "success" if status == "Graded" else ("info" if status == "Submitted" else "warning")

            with st.expander(f"{assign['title']} — {assign['subject_name']} (Due: {assign['due_date']})", expanded=True):
                st.markdown(f"**Status:** {ui_theme.render_badge(status, badge_var)} &nbsp;&nbsp; **Max Marks:** `{assign['max_marks']}`", unsafe_allow_html=True)
                st.write(f"**Instructions:** {assign['description']}")

                if sub and sub.get("marks_awarded") is not None:
                    st.success(f"Marks Awarded: **{sub['marks_awarded']} / {assign['max_marks']}** | Feedback: *{sub.get('feedback', 'Completed.')}*")

                # Download assignment resource if available
                if assign.get("attachment_path") and Path(assign["attachment_path"]).exists():
                    with open(assign["attachment_path"], "rb") as f:
                        st.download_button(
                            "Download Assignment Prompt File",
                            data=f.read(),
                            file_name=Path(assign["attachment_path"]).name,
                            key=f"dl_assign_{assign['id']}",
                        )

                st.write("---")
                st.subheader("Your Submission")

                if sub:
                    st.info(f"Submitted on: {sub['submitted_at']} | Content: {sub.get('submission_text', 'File uploaded')}")

                with st.form(f"submit_form_{assign['id']}"):
                    sub_text = st.text_area("Submission Notes / Answers", value=sub.get("submission_text", "") if sub else "", placeholder="Enter written solution or repository link...")
                    sub_file = st.file_uploader("Upload Solution Document (PDF, ZIP, DOCX)", key=f"file_{assign['id']}")
                    submit_btn = st.form_submit_button("Submit Assignment", type="primary")

                    if submit_btn:
                        if permissions.prevent_demo_mutation():
                            pass
                        elif not sub_text and not sub_file:
                            st.error("Please provide written answers or upload a solution file.")
                        else:
                            academic_service.record_student_submission(
                                assignment_id=assign["id"],
                                student_id=stu_id,
                                submission_text=sub_text,
                                uploaded_file=sub_file,
                            )
                            st.success("Assignment submitted successfully!")
                            st.rerun()

# ============================================================================
# PROFESSOR ASSIGNMENTS MANAGEMENT VIEW
# ============================================================================
else:
    auth_subjects = permissions.get_professor_authorized_subjects()

    ui_theme.render_header(
        title="Assignment Management",
        subtitle="Publish coursework prompts, download student files, and evaluate submissions",
        badge_text="Faculty Operations",
        badge_variant="primary",
    )

    tab_create, tab_view_subs = st.tabs(["Create Assignment", "Review & Grade Submissions"])

    with tab_create:
        st.subheader("Publish New Coursework Assignment")
        with st.form("create_assign_form"):
            c1, c2 = st.columns(2)
            with c1:
                a_title = st.text_input("Assignment Title *", placeholder="e.g. Unit 3 Relational Normalization")
                a_subject = st.selectbox("Subject Name *", auth_subjects)
                a_course = st.selectbox("Course *", COURSES)
            with c2:
                a_sem = st.selectbox("Semester *", SEMESTERS)
                a_due = st.date_input("Due Date *", value=date.today())
                a_marks = st.number_input("Maximum Marks *", min_value=1.0, max_value=100.0, value=10.0, step=1.0)

            a_desc = st.text_area("Assignment Instructions & Rubric *", placeholder="Detailed instructions for students...")
            a_file = st.file_uploader("Attach Resource / Problem Sheet (Optional)")

            submit_create = st.form_submit_button("Publish Assignment", type="primary", use_container_width=True)

            if submit_create:
                if permissions.prevent_demo_mutation():
                    pass
                elif not a_title or not a_subject or not a_desc:
                    st.error("Title, Subject, and Instructions are required.")
                else:
                    curr_user = permissions.get_current_user() or {}
                    academic_service.publish_assignment(
                        title=a_title,
                        subject_name=a_subject,
                        course=a_course,
                        semester=a_sem,
                        due_date=str(a_due),
                        description=a_desc,
                        max_marks=a_marks,
                        uploaded_file=a_file,
                        created_by=curr_user.get("id"),
                    )
                    st.success(f"Assignment '{a_title}' published successfully!")
                    st.rerun()

    with tab_view_subs:
        st.subheader("Review Student Submissions")
        all_assigns = database.get_assignments()
        if not all_assigns.empty:
            all_assigns = all_assigns[all_assigns["subject_name"].isin(auth_subjects)]
        if all_assigns.empty:
            st.info("No assignments created yet for your authorized subjects.")
        else:
            assign_opts = {f"{r['title']} ({r['course']} Sem {r['semester']})": r["id"] for _, r in all_assigns.iterrows()}
            chosen_assign_lbl = st.selectbox("Select Assignment", list(assign_opts.keys()))
            chosen_assign_id = assign_opts[chosen_assign_lbl]

            subs_df = database.get_submissions_for_assignment(chosen_assign_id)
            if subs_df.empty:
                st.info("No students have submitted solutions for this assignment yet.")
            else:
                for _, s_row in subs_df.iterrows():
                    sub_st = s_row["submission_status"]
                    b_var = "success" if sub_st == "Graded" else ("info" if sub_st == "Submitted" else "warning")
                    with st.expander(f"{s_row['full_name']} ({s_row['student_id']}) — Status: {sub_st}"):
                        st.markdown(f"**Evaluation Status:** {ui_theme.render_badge(sub_st, b_var)} &nbsp;|&nbsp; **Submitted On:** {s_row['submitted_at']}", unsafe_allow_html=True)
                        st.write(f"**Submission Notes:** {s_row['submission_text']}")
                        if s_row.get("submission_path") and Path(s_row["submission_path"]).exists():
                            with open(s_row["submission_path"], "rb") as f:
                                st.download_button(
                                    "Download Student File",
                                    data=f.read(),
                                    file_name=Path(s_row["submission_path"]).name,
                                    key=f"dl_sub_{s_row['submission_id']}",
                                )

                        with st.form(f"grade_form_{s_row['submission_id']}"):
                            c_g1, c_g2 = st.columns([1, 3])
                            with c_g1:
                                curr_marks = float(s_row["marks_awarded"]) if s_row["marks_awarded"] is not None else 8.0
                                awarded_m = st.number_input("Award Marks", min_value=0.0, max_value=100.0, value=curr_marks, step=0.5)
                            with c_g2:
                                feedback_txt = st.text_input("Feedback", value=s_row.get("feedback", "") or "Good work.")

                            submit_grade = st.form_submit_button("Save Grade", type="primary")
                            if submit_grade:
                                if permissions.prevent_demo_mutation():
                                    pass
                                else:
                                    database.grade_assignment_submission(s_row["submission_id"], awarded_m, feedback_txt)
                                    st.success(f"Graded submission for {s_row['full_name']}.")
                                    st.rerun()
