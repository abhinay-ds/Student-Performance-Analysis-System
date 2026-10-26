"""
Page 9: Marks and Results Management (Professor / Administrator Portal).
Enter individual assessment marks, validate against limits, calculate grades,
edit existing evaluation scores, and review/export class result sheets.
"""

from datetime import date
import streamlit as st
import database
import auth
import permissions
import validators
import analytics
import ui_theme
from config import MAX_INTERNAL_MARKS, MAX_ASSIGNMENT_MARKS, MAX_EXAM_MARKS, MAX_TOTAL_MARKS, GRADE_RULES

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

permissions.require_role(["professor", "admin"])

ui_theme.render_header(
    title="Marks and Results Management",
    subtitle="Record examination evaluations, calculate letter grades, and maintain scorecards",
    badge_text="Academic Evaluations",
    badge_variant="primary",
)

tab_records, tab_add, tab_edit, tab_del, tab_approve = st.tabs(
    ["All Academic Evaluations", "Record Assessment", "Edit Record", "Delete Record", "Result Approval"]
)

# ============================================================================
# Tab 1: View Evaluations Table & Class Performance
# ============================================================================
with tab_records:
    st.subheader("Academic Evaluations Directory")
    auth_subjects = permissions.get_professor_authorized_subjects()

    c1, c2, c3 = st.columns(3)
    with c1:
        f_stu = st.text_input("Filter by Student ID", placeholder="e.g. STU1001")
    with c2:
        f_sub = st.selectbox("Subject Filter", ["All Authorized"] + auth_subjects)
    with c3:
        f_status = st.selectbox("Status", ["All", "Passed Only", "Failed Only", "Needs Support"])

    target_subj = f_sub if f_sub != "All Authorized" else None
    recs_df = database.get_academic_records_detailed(
        student_id_str=f_stu if f_stu else None,
        subject=target_subj,
    )

    if not recs_df.empty and target_subj is None:
        recs_df = recs_df[recs_df["subject"].isin(auth_subjects)]

    if recs_df.empty:
        st.info("No academic records match the search criteria.")
    else:
        enriched = analytics.enrich_academic_records(recs_df)
        if f_status == "Passed Only":
            enriched = enriched[enriched["is_pass"] == True]
        elif f_status == "Failed Only":
            enriched = enriched[enriched["is_pass"] == False]
        elif f_status == "Needs Support":
            enriched = enriched[enriched["needs_support"] == True]

        st.write(f"Showing **{len(enriched)}** evaluation record(s):")
        st.dataframe(
            enriched[
                [
                    "record_id",
                    "student_id",
                    "full_name",
                    "department",
                    "semester",
                    "subject",
                    "internal_marks",
                    "assignment_marks",
                    "exam_marks",
                    "total_marks",
                    "grade",
                    "attendance_percentage",
                    "exam_date",
                ]
            ].rename(
                columns={
                    "record_id": "Ref #",
                    "student_id": "Student ID",
                    "full_name": "Full Name",
                    "department": "Department",
                    "semester": "Sem",
                    "subject": "Subject",
                    "internal_marks": f"Int ({MAX_INTERNAL_MARKS})",
                    "assignment_marks": f"Asgn ({MAX_ASSIGNMENT_MARKS})",
                    "exam_marks": f"Exam ({MAX_EXAM_MARKS})",
                    "total_marks": "Total",
                    "grade": "Grade",
                    "attendance_percentage": "Attendance %",
                    "exam_date": "Exam Date",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

# ============================================================================
# Tab 2: Record New Assessment
# ============================================================================
with tab_add:
    st.subheader("Record Student Assessment Score")
    all_students_df = database.get_all_students()

    if all_students_df.empty:
        st.warning("No students found. Please enroll students first.")
    else:
        stu_opts = {f"{r['student_id']} - {r['full_name']} ({r['department']}, Sem {r['semester']})": r["id"] for _, r in all_students_df.iterrows()}

        with st.form("record_marks_form"):
            col1, col2 = st.columns(2)
            with col1:
                sel_stu_lbl = st.selectbox("Select Student *", list(stu_opts.keys()))
                sel_stu_id = stu_opts[sel_stu_lbl]
                sub_name = st.selectbox("Subject *", auth_subjects)
                exam_type = st.selectbox("Evaluation Type", ["End Semester", "Mid-Term", "Class Test", "Lab Practical"])
                exam_dt = st.date_input("Examination Date *", value=date.today())

            with col2:
                int_m = st.number_input(f"Internal Marks (0 to {MAX_INTERNAL_MARKS}) *", min_value=0.0, max_value=float(MAX_INTERNAL_MARKS), value=15.0, step=0.5)
                asgn_m = st.number_input(f"Assignment Marks (0 to {MAX_ASSIGNMENT_MARKS}) *", min_value=0.0, max_value=float(MAX_ASSIGNMENT_MARKS), value=8.0, step=0.5)
                exam_m = st.number_input(f"Final Exam Marks (0 to {MAX_EXAM_MARKS}) *", min_value=0.0, max_value=float(MAX_EXAM_MARKS), value=55.0, step=0.5)
                att_pct = st.number_input("Attendance % (0 to 100%)", min_value=0.0, max_value=100.0, value=85.0, step=0.5)

            calc_tot = round(int_m + asgn_m + exam_m, 2)
            calc_grade, calc_gpa, calc_desc = validators.calculate_grade(calc_tot)
            st.info(f"📊 **Calculated Score:** Total = **{calc_tot} / 100** | Grade = **{calc_grade}** ({calc_desc}) | GPA = **{calc_gpa}**")

            submit_rec = st.form_submit_button("Save Assessment Record", type="primary", use_container_width=True)

            if submit_rec:
                if permissions.prevent_demo_mutation():
                    pass
                elif not sub_name:
                    st.error("Subject name is required.")
                else:
                    v_ok, v_msg, c_int, c_asgn, c_exam, c_tot = validators.validate_marks(int_m, asgn_m, exam_m)
                    if not v_ok:
                        st.error(v_msg)
                    else:
                        curr_u = permissions.get_current_user() or {}
                        payload = {
                            "student_id": sel_stu_id,
                            "subject": sub_name,
                            "examination_type": exam_type,
                            "internal_marks": c_int,
                            "assignment_marks": c_asgn,
                            "exam_marks": c_exam,
                            "attendance_percentage": att_pct,
                            "grade": calc_grade,
                            "exam_date": str(exam_dt),
                            "created_by": curr_u.get("id"),
                        }
                        try:
                            database.add_academic_record(payload)
                            st.success(f"Assessment recorded for '{sub_name}'!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error (duplicate entry for same student, subject, and date): {e}")

# ============================================================================
# Tab 3: Edit Record
# ============================================================================
with tab_edit:
    st.subheader("Update Academic Record")
    all_recs = database.get_academic_records_detailed()
    if all_recs.empty:
        st.info("No records to edit.")
    else:
        r_opts = {f"#{r['record_id']}: {r['student_id']} - {r['subject']} ({r['exam_date']})": r["record_id"] for _, r in all_recs.iterrows()}
        chosen_r_lbl = st.selectbox("Select Record", list(r_opts.keys()), key="edit_rec_sel")
        chosen_r_id = r_opts[chosen_r_lbl]
        target_rec = all_recs[all_recs["record_id"] == chosen_r_id].iloc[0]

        with st.form("edit_marks_form"):
            e1, e2 = st.columns(2)
            with e1:
                e_subj = st.text_input("Subject *", value=target_rec["subject"])
                try:
                    p_dt = date.fromisoformat(target_rec["exam_date"][:10])
                except Exception:
                    p_dt = date.today()
                e_dt = st.date_input("Exam Date *", value=p_dt)
            with e2:
                e_int = st.number_input("Internal Marks", min_value=0.0, max_value=float(MAX_INTERNAL_MARKS), value=float(target_rec["internal_marks"]), step=0.5)
                e_asgn = st.number_input("Assignment Marks", min_value=0.0, max_value=float(MAX_ASSIGNMENT_MARKS), value=float(target_rec["assignment_marks"]), step=0.5)
                e_exam = st.number_input("Exam Marks", min_value=0.0, max_value=float(MAX_EXAM_MARKS), value=float(target_rec["exam_marks"]), step=0.5)
                e_att = st.number_input("Attendance %", min_value=0.0, max_value=100.0, value=float(target_rec["attendance_percentage"]), step=0.5)

            edit_reason = st.text_input("Mandatory Reason for Score Update / Correction *", placeholder="e.g. Re-evaluation verified by department head, transcription error corrected")
            submit_upd = st.form_submit_button("Update Record", type="primary")

            if submit_upd:
                if permissions.prevent_demo_mutation():
                    pass
                elif not edit_reason.strip():
                    st.error("A documented reason is mandatory when correcting student examination scores.")
                else:
                    v_ok, v_msg, c_int, c_asgn, c_exam, c_tot = validators.validate_marks(e_int, e_asgn, e_exam)
                    if not v_ok:
                        st.error(v_msg)
                    else:
                        curr_u = permissions.get_current_user()
                        database.correct_academic_record(
                            record_id=chosen_r_id,
                            internal_marks=c_int,
                            assignment_marks=c_asgn,
                            exam_marks=c_exam,
                            maximum_marks=100.0,
                            reason=edit_reason,
                            actor_user=curr_u,
                        )
                        st.success("Record updated and recalculated successfully. Modification logged to audit trail.")
                        st.rerun()

# ============================================================================
# Tab 4: Delete Record
# ============================================================================
with tab_del:
    st.subheader("Delete Academic Record")
    if all_recs.empty:
        st.info("No records to delete.")
    else:
        del_r_lbl = st.selectbox("Select Record to Delete", list(r_opts.keys()), key="del_rec_sel")
        del_r_id = r_opts[del_r_lbl]
        confirm_del_rec = st.checkbox(f"Confirm permanent removal of evaluation record #{del_r_id}", key="chk_del_rec")
        if st.button("Permanently Remove Record", disabled=not confirm_del_rec, key="btn_del_rec"):
            if permissions.prevent_demo_mutation():
                pass
            else:
                database.delete_academic_record(del_r_id)
                st.success("Record deleted successfully.")
                st.rerun()

# ============================================================================
# Tab 5: Result Approval Workflow
# ============================================================================
with tab_approve:
    st.subheader("Official Result Verification & Approval Workflow")
    st.caption("Coordinators can formally review and release examination evaluation batches.")

    pending_df = database.get_academic_records_detailed()
    if not pending_df.empty:
        # Check approval column if present
        if "is_approved" not in pending_df.columns:
            pending_df["is_approved"] = 1

        unapproved = pending_df[pending_df["is_approved"] == 0]
        if unapproved.empty:
            st.success("✅ All academic evaluations in the database are verified and approved.")
            st.write("##### Recently Approved Evaluations")
            st.dataframe(
                pending_df[["record_id", "student_id", "full_name", "subject", "total_marks", "grade", "exam_date"]].head(10).rename(columns={
                    "record_id": "Ref #",
                    "student_id": "Roll No",
                    "full_name": "Student",
                    "subject": "Subject",
                    "total_marks": "Total",
                    "grade": "Grade",
                    "exam_date": "Exam Date",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning(f"Found **{len(unapproved)}** evaluation(s) awaiting formal verification:")
            st.dataframe(
                unapproved[["record_id", "student_id", "full_name", "subject", "total_marks", "grade", "exam_date"]],
                use_container_width=True,
                hide_index=True,
            )
            if st.button(f"Approve All {len(unapproved)} Evaluation(s)", type="primary"):
                curr_u = permissions.get_current_user()
                cnt = database.approve_academic_records(unapproved["record_id"].tolist(), actor_user=curr_u)
                st.success(f"Successfully verified and approved {cnt} academic evaluation records.")
                st.rerun()
    else:
        st.info("No evaluations on record.")
