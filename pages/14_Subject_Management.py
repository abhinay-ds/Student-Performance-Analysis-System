"""
Subject Management Module (Coordinator / Admin Only).
Allows adding subjects, renaming subjects (with automated cascading display name updates
and full historical data preservation), managing credits, archiving/reactivating,
and inspecting enrolled students and authorized faculty.
"""

import streamlit as st
import database
import auth
import permissions
import ui_theme
from config import ROLE_COORDINATOR, ROLE_ADMIN, DEPARTMENTS, COURSES, SEMESTERS

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

permissions.require_role([ROLE_COORDINATOR, ROLE_ADMIN, "demo_coordinator"])

ui_theme.render_header(
    title="Curriculum & Subject Management",
    subtitle="Configure institutional subjects, credits, cascading renames, and faculty allocations",
    badge_text="Curriculum Management",
    badge_variant="primary",
)

current_user = permissions.get_current_user()

tab_browse, tab_add, tab_edit, tab_details = st.tabs([
    "Subject Catalog",
    "Create Subject",
    "Edit & Rename Subject",
    "Enrolled Students & Faculty"
])

# ============================================================================
# TAB 1: Subject Catalog
# ============================================================================
with tab_browse:
    st.subheader("Institutional Subjects Directory")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        f_dept = st.selectbox("Department Filter", ["All"] + DEPARTMENTS)
    with c2:
        f_course = st.selectbox("Course Filter", ["All"] + COURSES)
    with c3:
        f_sem = st.selectbox("Semester Filter", ["All"] + SEMESTERS)
    with c4:
        f_status = st.selectbox("Status", ["All", "Active", "Archived"])

    all_subjects = database.get_all_subjects(department=f_dept, course=f_course, semester=f_sem)

    if not all_subjects.empty:
        if f_status == "Active":
            all_subjects = all_subjects[all_subjects["is_active"] == 1]
        elif f_status == "Archived":
            all_subjects = all_subjects[all_subjects["is_active"] == 0]

        st.dataframe(
            all_subjects.rename(columns={
                "id": "Subject ID",
                "subject_code": "Code",
                "subject_name": "Subject Name",
                "department": "Department",
                "course": "Course",
                "semester": "Semester",
                "credits": "Credits",
                "is_active": "Active Status",
                "created_at": "Created Date",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No subjects found matching the selected filter criteria.")

# ============================================================================
# TAB 2: Create Subject
# ============================================================================
with tab_add:
    st.subheader("Add New Academic Subject")
    st.caption("Create a subject with unique code, assigned department, credits, and course.")
    with st.form("create_subject_form"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            code_in = st.text_input("Subject Code *", placeholder="e.g. CS501").strip().upper()
            name_in = st.text_input("Subject Name *", placeholder="e.g. Distributed Cloud Computing").strip()
            dept_in = st.selectbox("Department *", DEPARTMENTS, index=0)
            course_in = st.selectbox("Course / Program *", COURSES, index=0)
        with col_s2:
            sem_in = st.selectbox("Semester *", SEMESTERS, index=2)
            credits_in = st.number_input("Credits *", min_value=1, max_value=8, value=3)
            desc_in = st.text_area("Course Overview & Description", placeholder="Outline core syllabus objectives and learning outcomes...")

        btn_create = st.form_submit_button("Register New Subject", type="primary", use_container_width=True)
        if btn_create:
            if not code_in or not name_in:
                st.error("Subject code and name are required.")
            else:
                try:
                    s_id = database.create_subject(
                        subject_code=code_in,
                        subject_name=name_in,
                        department=dept_in,
                        course=course_in,
                        semester=sem_in,
                        credits=credits_in,
                        description=desc_in,
                    )
                    database.log_audit_action(
                        username=current_user.get("username", "coordinator") if current_user else "coordinator",
                        role="coordinator",
                        action="CREATE_SUBJECT",
                        entity_type="SUBJECT",
                        entity_id=str(s_id),
                        new_values=f"code: {code_in}, name: {name_in}, credits: {credits_in}",
                        reason="New subject curriculum registered by coordinator",
                    )
                    st.success(f"Subject '{name_in}' ({code_in}) created successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to create subject: {str(e)}")

# ============================================================================
# TAB 3: Edit & Rename Subject
# ============================================================================
with tab_edit:
    st.subheader("Edit & Rename Subject Details")
    st.caption("Renaming a subject maintains all historical marks, student attendance records, and assignments without data loss.")

    subjs_df = database.get_all_subjects()
    if not subjs_df.empty:
        subj_choice = st.selectbox(
            "Select Subject to Edit",
            subjs_df["id"].tolist(),
            format_func=lambda sid: f"{subjs_df[subjs_df['id'] == sid].iloc[0]['subject_code']} - {subjs_df[subjs_df['id'] == sid].iloc[0]['subject_name']}",
            key="edit_subj_selector"
        )
        selected_subj = subjs_df[subjs_df["id"] == subj_choice].iloc[0]

        with st.form("edit_subject_form"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                e_code = st.text_input("Subject Code *", value=str(selected_subj["subject_code"])).strip().upper()
                e_name = st.text_input("Subject Name *", value=str(selected_subj["subject_name"])).strip()
                dept_idx = DEPARTMENTS.index(selected_subj["department"]) if selected_subj["department"] in DEPARTMENTS else 0
                e_dept = st.selectbox("Department *", DEPARTMENTS, index=dept_idx)
                course_idx = COURSES.index(selected_subj["course"]) if selected_subj["course"] in COURSES else 0
                e_course = st.selectbox("Course *", COURSES, index=course_idx)
            with col_e2:
                sem_idx = SEMESTERS.index(selected_subj["semester"]) if selected_subj["semester"] in SEMESTERS else 0
                e_sem = st.selectbox("Semester *", SEMESTERS, index=sem_idx)
                e_cred = st.number_input("Credits", min_value=1, max_value=8, value=int(selected_subj.get("credits", 3)))
                e_desc = st.text_area("Description", value=str(selected_subj.get("description", "")))
                e_active = st.checkbox("Active Subject (Visible to Faculty & Students)", value=bool(selected_subj["is_active"]))

            e_reason = st.text_input("Reason for Change (Required for Audit Log) *", placeholder="e.g. Curriculum modernization, code update")
            btn_save_edit = st.form_submit_button("Update Subject Details", type="primary", use_container_width=True)

            if btn_save_edit:
                if not e_reason:
                    st.error("A documented reason is mandatory when modifying institutional academic subjects.")
                else:
                    success = database.update_subject(
                        subject_id=subj_choice,
                        subject_code=e_code,
                        subject_name=e_name,
                        department=e_dept,
                        course=e_course,
                        semester=e_sem,
                        credits=e_cred,
                        description=e_desc,
                        is_active=1 if e_active else 0,
                        updated_by_user=current_user,
                        reason=e_reason,
                    )
                    if success:
                        st.success(f"Subject '{e_name}' successfully updated and synchronized across all records.")
                        st.rerun()
                    else:
                        st.error("Failed to update subject.")

        st.divider()
        st.write("##### ⚠️ Archive or Delete Subject")
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            st.info("💡 **Archival Policy:** Archiving retains all historical exam marks, transcripts, and attendance sessions while hiding the subject from new roll-calls.")
            arch_label = "Archive Subject" if selected_subj["is_active"] else "Reactivate Subject"
            if st.button(arch_label, key="toggle_arch_btn"):
                new_state = 0 if selected_subj["is_active"] else 1
                database.toggle_subject_status(subj_choice, new_state, updated_by_user=current_user, reason=f"Subject status changed to {new_state}")
                st.success(f"Subject status changed successfully.")
                st.rerun()

        with col_del2:
            st.warning("Permanent Deletion: Permitted only if no attendance, marks, or coursework records exist.")
            confirm_subj_del = st.checkbox("Confirm permanent deletion of this subject", key="chk_del_subj")
            if st.button("Permanently Delete Subject", disabled=not confirm_subj_del, key="del_subj_btn"):
                ok, d_msg = database.delete_subject(subj_choice)
                if ok:
                    st.success(d_msg)
                    st.rerun()
                else:
                    st.error(d_msg)
    else:
        st.info("No subjects found.")

# ============================================================================
# TAB 4: Enrolled Students & Faculty
# ============================================================================
with tab_details:
    st.subheader("Subject Enrollment & Faculty Roster")
    if not subjs_df.empty:
        detail_sid = st.selectbox(
            "Select Subject to Inspect",
            subjs_df["id"].tolist(),
            format_func=lambda sid: f"{subjs_df[subjs_df['id'] == sid].iloc[0]['subject_code']} - {subjs_df[subjs_df['id'] == sid].iloc[0]['subject_name']}",
            key="detail_subj_sel"
        )
        c_prof, c_stu = st.columns(2)
        with c_prof:
            st.write("##### 👨‍🏫 Authorized Faculty")
            assigned_profs = database.get_subject_assigned_professors(detail_sid)
            if assigned_profs:
                for p in assigned_profs:
                    st.markdown(f"• **{p['full_name']}** (`{p['username']}`) — *{p['email']}*")
            else:
                st.caption("No professors specifically assigned to this subject.")

        with c_stu:
            st.write("##### 🎓 Enrolled Students")
            enrolled_stus = database.get_subject_enrolled_students(detail_sid)
            if not enrolled_stus.empty:
                st.dataframe(
                    enrolled_stus[["student_id", "full_name", "department", "course", "semester"]].rename(columns={
                        "student_id": "Roll No",
                        "full_name": "Full Name",
                        "department": "Department",
                        "course": "Course",
                        "semester": "Semester",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption("No students explicitly enrolled in this subject.")
