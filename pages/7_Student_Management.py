"""
Page 7: Student Management (Professor / Administrator Portal).
Enroll students, search directory, filter cohorts, update details,
and perform safe deletions with foreign-key cascade confirmation.
"""

from datetime import date
import streamlit as st
import database
import auth
import permissions
import validators
import ui_theme
from config import DEPARTMENTS, COURSES, SEMESTERS

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

# Enforce role restriction
permissions.require_role(["professor", "admin"])

ui_theme.render_header(
    title="Student Directory & Enrollment",
    subtitle="Enroll students, filter academic cohorts, update profiles, and manage directory records",
    badge_text="Student Records",
    badge_variant="primary",
)

tab_dir, tab_add, tab_edit, tab_del = st.tabs(
    ["Student Directory", "Enroll Student", "Update Details", "Remove Student"]
)

# ============================================================================
# Tab 1: Search & Filter Directory
# ============================================================================
with tab_dir:
    st.subheader("Student Cohort Directory")

    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        s_query = st.text_input("🔍 Search by Student ID, Name, or Email", placeholder="e.g. STU101 or Sharma")
    with c2:
        f_dept = st.selectbox("Department", ["All"] + DEPARTMENTS, key="mgt_dept")
    with c3:
        f_course = st.selectbox("Course", ["All"] + COURSES, key="mgt_course")
    with c4:
        f_sem = st.selectbox("Semester", ["All"] + [str(s) for s in SEMESTERS], key="mgt_sem")

    sem_val = int(f_sem) if f_sem != "All" else None
    dept_val = f_dept if f_dept != "All" else None
    course_val = f_course if f_course != "All" else None

    students_df = database.get_all_students(
        search=s_query, department=dept_val, course=course_val, semester=sem_val
    )

    st.write(f"Showing **{len(students_df)}** student record(s)")

    if students_df.empty:
        st.info("No matching students found.")
    else:
        st.dataframe(
            students_df[
                ["student_id", "full_name", "email", "department", "course", "semester", "enrollment_date"]
            ].rename(
                columns={
                    "student_id": "Student ID",
                    "full_name": "Full Name",
                    "email": "Email",
                    "department": "Department",
                    "course": "Course",
                    "semester": "Sem",
                    "enrollment_date": "Enrolled Date",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

# ============================================================================
# Tab 2: Add New Student
# ============================================================================
with tab_add:
    st.subheader("Enroll New Student")
    with st.form("add_student_form"):
        c1, c2 = st.columns(2)
        with c1:
            s_id = st.text_input("Student ID *", placeholder="e.g. STU111").strip().upper()
            s_name = st.text_input("Full Name *", placeholder="e.g. Aarav Sharma").strip()
            s_email = st.text_input("Email Address *", placeholder="e.g. student@college.edu").strip()
            s_dept = st.selectbox("Department *", DEPARTMENTS, key="add_dept")
        with c2:
            s_course = st.selectbox("Course *", COURSES, key="add_course")
            s_semester = st.selectbox("Semester *", SEMESTERS, key="add_sem")
            s_date = st.date_input("Enrollment Date *", value=date.today())

        submit_add = st.form_submit_button("Enroll Student", type="primary", use_container_width=True)

        if submit_add:
            if permissions.prevent_demo_mutation():
                pass
            else:
                ok_id, msg_id = validators.validate_student_id(s_id)
                ok_name, msg_name = validators.validate_student_name(s_name)
                ok_email, msg_email = validators.validate_email(s_email)

                if not ok_id:
                    st.error(f"Student ID Error: {msg_id}")
                elif not ok_name:
                    st.error(f"Name Error: {msg_name}")
                elif not ok_email:
                    st.error(f"Email Error: {msg_email}")
                elif database.get_student_by_student_id(s_id):
                    st.error(f"A student with ID '{s_id}' already exists.")
                else:
                    payload = {
                        "student_id": s_id,
                        "full_name": s_name,
                        "email": s_email,
                        "department": s_dept,
                        "course": s_course,
                        "semester": s_semester,
                        "enrollment_date": str(s_date),
                    }
                    database.add_student(payload)
                    st.success(f"Student '{s_name}' ({s_id}) enrolled successfully!")
                    st.rerun()

# ============================================================================
# Tab 3: Edit Student Details
# ============================================================================
with tab_edit:
    st.subheader("Update Student Information")
    all_stus = database.get_all_students()

    if all_stus.empty:
        st.info("No enrolled students.")
    else:
        student_opts = {f"{r['student_id']} - {r['full_name']}": r["id"] for _, r in all_stus.iterrows()}
        chosen_lbl = st.selectbox("Select Student to Edit", list(student_opts.keys()), key="edit_stu_sel")
        chosen_id = student_opts[chosen_lbl]
        s_row = database.get_student_by_id(chosen_id)

        if s_row:
            with st.form("edit_stu_form"):
                e1, e2 = st.columns(2)
                with e1:
                    e_id = st.text_input("Student ID *", value=s_row["student_id"]).strip().upper()
                    e_name = st.text_input("Full Name *", value=s_row["full_name"]).strip()
                    e_email = st.text_input("Email *", value=s_row["email"]).strip()
                    d_idx = DEPARTMENTS.index(s_row["department"]) if s_row["department"] in DEPARTMENTS else 0
                    e_dept = st.selectbox("Department *", DEPARTMENTS, index=d_idx)
                with e2:
                    c_idx = COURSES.index(s_row["course"]) if s_row["course"] in COURSES else 0
                    e_course = st.selectbox("Course *", COURSES, index=c_idx)
                    sem_idx = SEMESTERS.index(s_row["semester"]) if s_row["semester"] in SEMESTERS else 0
                    e_sem = st.selectbox("Semester *", SEMESTERS, index=sem_idx)
                    try:
                        dt_parsed = date.fromisoformat(s_row["enrollment_date"][:10])
                    except Exception:
                        dt_parsed = date.today()
                    e_dt = st.date_input("Enrollment Date *", value=dt_parsed)

                submit_edit = st.form_submit_button("Save Changes", type="primary", use_container_width=True)

                if submit_edit:
                    if permissions.prevent_demo_mutation():
                        pass
                    else:
                        ok_id, msg_id = validators.validate_student_id(e_id)
                        ok_name, msg_name = validators.validate_student_name(e_name)
                        ok_email, msg_email = validators.validate_email(e_email)

                        existing_by_id = database.get_student_by_student_id(e_id)
                        if existing_by_id and existing_by_id["id"] != chosen_id:
                            st.error(f"Cannot update: Student ID '{e_id}' is taken by another student.")
                        elif not ok_id or not ok_name or not ok_email:
                            st.error(msg_id or msg_name or msg_email)
                        else:
                            database.update_student(chosen_id, {
                                "student_id": e_id,
                                "full_name": e_name,
                                "email": e_email,
                                "department": e_dept,
                                "course": e_course,
                                "semester": e_sem,
                                "enrollment_date": str(e_dt),
                            })
                            st.success(f"Student '{e_id}' profile updated successfully.")
                            st.rerun()

        # Coordinator Account Governance for this student
        if permissions.is_coordinator() and s_row.get("user_id"):
            u_id = int(s_row["user_id"])
            st.divider()
            st.write("##### 🛡️ Coordinator Account Governance")
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                u_row = database.get_user_by_id(u_id)
                u_active = bool(u_row.get("is_active", 1)) if u_row else True
                st.write(f"Login Account: `{u_row['username'] if u_row else 'None'}` | Status: **{'Active' if u_active else 'Deactivated'}**")
                toggle_act = st.radio("Account Access", ["Active", "Deactivated"], index=0 if u_active else 1, key=f"stu_act_{u_id}")
                if st.button("Update Login Access", key=f"btn_stu_act_{u_id}"):
                    curr_u = permissions.get_current_user()
                    database.set_user_active_status(u_id, 1 if toggle_act == "Active" else 0, actor_user=curr_u, reason="Student account status modified by coordinator")
                    st.success("Account status updated.")
                    st.rerun()
            with c_g2:
                new_stu_pwd = st.text_input("Reset Student Password", type="password", key=f"stu_pwd_{u_id}")
                if st.button("Reset Password", key=f"btn_stu_pwd_{u_id}"):
                    curr_u = permissions.get_current_user()
                    ok_p, msg_p = database.admin_reset_password(u_id, new_stu_pwd, actor_user=curr_u)
                    if ok_p:
                        st.success(msg_p)
                    else:
                        st.error(msg_p)

# ============================================================================
# Tab 4: Delete Student
# ============================================================================
with tab_del:
    st.subheader("Remove Student Record")
    if all_stus.empty:
        st.info("No students enrolled.")
    else:
        del_opts = {f"{r['student_id']} - {r['full_name']}": r["id"] for _, r in all_stus.iterrows()}
        del_lbl = st.selectbox("Select Student to Delete", list(del_opts.keys()), key="del_stu_sel")
        del_internal_id = del_opts[del_lbl]

        recs_count = database.count_student_academic_records(del_internal_id)
        if recs_count > 0:
            st.warning(f"This student has **{recs_count}** associated academic performance records.")
            confirm_del = st.checkbox(f"Confirm permanent deletion of student and all {recs_count} associated records.")
        else:
            confirm_del = st.checkbox("Confirm permanent deletion of this student profile.")

        if st.button("Permanently Delete Student", disabled=not confirm_del):
            if permissions.prevent_demo_mutation():
                pass
            else:
                ok, msg = database.delete_student(del_internal_id, cascade=confirm_del)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
