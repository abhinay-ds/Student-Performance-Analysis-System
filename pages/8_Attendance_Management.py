"""
Page 8: Attendance Management (Professor / Administrator Portal).
Schedule lecture sessions, mark student roll calls (Present, Absent, Late),
inspect session history, and view/export class attendance matrices.
"""

from datetime import date
import streamlit as st
import database
import auth
import permissions
import attendance_service
import ui_theme
from config import COURSES, SEMESTERS

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

permissions.require_role(["professor", "admin"])

ui_theme.render_header(
    title="Attendance Management & Tracking",
    subtitle="Record session roll-calls, review attendance matrices, and submit audited corrections",
    badge_text="Attendance Operations",
    badge_variant="primary",
)

tab_mark, tab_history, tab_matrix, tab_correct = st.tabs(
    ["Mark Session Attendance", "Session History Log", "Class Attendance Matrix", "Attendance Corrections"]
)

# ============================================================================
# Tab 1: Mark Daily Session Attendance
# ============================================================================
with tab_mark:
    st.subheader("Take Class Roll Call")

    # Select Subject & Session Info
    subjects_df = database.get_all_subjects()
    auth_subjects = permissions.get_professor_authorized_subjects()
    if not subjects_df.empty:
        subjects_df = subjects_df[subjects_df["subject_name"].isin(auth_subjects)]

    if subjects_df.empty:
        st.warning("No authorized subjects assigned to this faculty profile.")
    else:
        sub_opts = {f"{r['subject_code']} - {r['subject_name']} ({r['course']} Sem {r['semester']})": r["id"] for _, r in subjects_df.iterrows()}
        c_sub, c_date, c_label = st.columns([2, 1, 1])
        with c_sub:
            chosen_sub_label = st.selectbox("Select Subject *", list(sub_opts.keys()), key="att_sub_sel")
            chosen_sub_id = sub_opts[chosen_sub_label]
            sub_info = database.get_subject_by_id(chosen_sub_id)

        with c_date:
            session_dt = st.date_input("Session Date *", value=date.today())

        with c_label:
            session_lbl = st.text_input("Session Label *", value="Regular Lecture")

        # Fetch enrolled students for this course & semester
        enrolled_students = database.get_all_students(course=sub_info["course"], semester=sub_info["semester"])

        if enrolled_students.empty:
            st.info(f"No students enrolled in {sub_info['course']} (Semester {sub_info['semester']}).")
        else:
            st.write(f"Marking attendance for **{len(enrolled_students)}** student(s):")

            # Check if session already exists to preload values
            existing_sessions = database.get_attendance_sessions(subject_id=chosen_sub_id, date_str=str(session_dt))
            session_existing_id = None
            for _, s_row in existing_sessions.iterrows():
                if s_row["session_label"] == session_lbl:
                    session_existing_id = s_row["session_id"]
                    break

            with st.form("mark_attendance_form"):
                attendance_selections = {}

                for _, stu in enrolled_students.iterrows():
                    col_name, col_status = st.columns([2, 2])
                    with col_name:
                        st.markdown(f"**{stu['full_name']}** (`{stu['student_id']}`)")
                    with col_status:
                        stat = st.radio(
                            "Status",
                            ["Present", "Absent", "Late"],
                            index=0,
                            key=f"roll_{stu['id']}",
                            horizontal=True,
                            label_visibility="collapsed",
                        )
                        attendance_selections[stu["id"]] = stat

                submit_roll_call = st.form_submit_button("Save Session Attendance", type="primary", use_container_width=True)

                if submit_roll_call:
                    if permissions.prevent_demo_mutation():
                        pass
                    else:
                        try:
                            # Create or retrieve session ID
                            curr_user = permissions.get_current_user() or {}
                            if not session_existing_id:
                                sess_id = database.create_attendance_session(
                                    subject_id=chosen_sub_id,
                                    session_date=str(session_dt),
                                    session_label=session_lbl,
                                    created_by=curr_user.get("id"),
                                )
                            else:
                                sess_id = session_existing_id

                            attendance_service.save_session_attendance(sess_id, attendance_selections)
                            st.success(f"Attendance recorded successfully for {len(attendance_selections)} students on {session_dt}!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error recording attendance: {e}")

# ============================================================================
# Tab 2: Session History Log
# ============================================================================
with tab_history:
    st.subheader("Attendance Sessions Log")
    sessions_df = database.get_attendance_sessions()
    if sessions_df.empty:
        st.info("No lecture sessions recorded yet.")
    else:
        st.dataframe(
            sessions_df[
                ["session_id", "subject_code", "subject_name", "department", "session_date", "session_label"]
            ].rename(
                columns={
                    "session_id": "Session ID",
                    "subject_code": "Code",
                    "subject_name": "Subject",
                    "department": "Department",
                    "session_date": "Date",
                    "session_label": "Session Label",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

# ============================================================================
# Tab 3: Class Attendance Matrix
# ============================================================================
with tab_matrix:
    st.subheader("Class Attendance Matrix")
    if not subjects_df.empty:
        mat_sub_lbl = st.selectbox("Select Subject for Attendance Matrix", list(sub_opts.keys()), key="mat_sub_sel")
        mat_sub_id = sub_opts[mat_sub_lbl]

        matrix_df = attendance_service.get_class_attendance_matrix(mat_sub_id)
        if matrix_df.empty:
            st.info("No recorded sessions found for this subject.")
        else:
            st.dataframe(matrix_df, use_container_width=True, hide_index=True)
            csv_mat = matrix_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Export Matrix (CSV)", data=csv_mat, file_name="class_attendance_matrix.csv", mime="text/csv")

# ============================================================================
# Tab 4: Attendance Corrections (Audited)
# ============================================================================
with tab_correct:
    st.subheader("Attendance Mistake Correction & Audit Trail")
    st.caption("Coordinators and faculty can correct attendance entries. Every modification requires a documented justification and is logged in the immutable audit log.")

    all_sess = database.get_attendance_sessions()
    if not all_sess.empty:
        sess_options = {
            r["session_id"]: f"{r['session_date']} — {r['subject_code']}: {r['subject_name']} ({r['session_label']})"
            for _, r in all_sess.iterrows()
        }
        sel_sess_id = st.selectbox("Select Lecture Session", list(sess_options.keys()), format_func=lambda k: sess_options[k], key="corr_sess_sel")
        sess_meta = all_sess[all_sess["session_id"] == sel_sess_id].iloc[0]

        # Get students for this session's course/semester
        stus = database.get_all_students(course=sess_meta.get("course", "B.Tech"), semester=sess_meta.get("semester", 3))
        if stus.empty:
            stus = database.get_all_students()

        stu_corr_opts = {r["id"]: f"{r['student_id']} - {r['full_name']}" for _, r in stus.iterrows()}
        sel_corr_stu_id = st.selectbox("Select Student", list(stu_corr_opts.keys()), format_func=lambda k: stu_corr_opts[k], key="corr_stu_sel")

        # Fetch current record
        with database.get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT status FROM attendance_records WHERE attendance_session_id = ? AND student_id = ?", (sel_sess_id, sel_corr_stu_id))
            cur_r = c.fetchone()
            cur_status_val = cur_r["status"] if cur_r else "Not Recorded"

        c_stat1, c_stat2 = st.columns(2)
        c_stat1.write(f"Current Recorded Status: **`{cur_status_val}`**")
        new_stat_choice = c_stat2.selectbox("New Corrected Status", ["Present", "Absent", "Late"], key="new_stat_sel")

        corr_reason = st.text_input("Mandatory Reason for Correction *", placeholder="e.g. Medical leave slip submitted, clerical miscount on physical roll sheet")

        if st.button("Apply Attendance Correction", type="primary", key="btn_apply_corr"):
            if not corr_reason.strip():
                st.error("A documented reason is mandatory when correcting attendance records.")
            else:
                curr_user = permissions.get_current_user()
                database.correct_student_attendance(
                    session_id=sel_sess_id,
                    student_id=sel_corr_stu_id,
                    new_status=new_stat_choice,
                    reason=corr_reason,
                    actor_user=curr_user,
                )
                st.success(f"Attendance for {stu_corr_opts[sel_corr_stu_id]} updated from '{cur_status_val}' to '{new_stat_choice}'. Audit log recorded.")
                st.rerun()

        st.divider()
        st.write("##### 📜 Recent Attendance Correction Audit Entries")
        corr_audits = database.get_audit_logs(limit=10, action_filter="CORRECT_ATTENDANCE")
        if not corr_audits.empty:
            st.dataframe(
                corr_audits[["created_at", "username", "entity_id", "old_values", "new_values", "reason"]].rename(columns={
                    "created_at": "Timestamp",
                    "username": "User",
                    "entity_id": "Session & Student",
                    "old_values": "Old Status",
                    "new_values": "New Status",
                    "reason": "Documented Reason",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No attendance corrections logged yet.")
    else:
        st.info("No attendance sessions available to correct.")
