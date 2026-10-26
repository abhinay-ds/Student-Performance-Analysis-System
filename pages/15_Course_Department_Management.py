"""
Course & Department Management Module (Coordinator / Admin Only).
Allows defining academic departments, degree programs, semester tracks,
and managing operational activation status.
"""

import streamlit as st
import database
import auth
import permissions
import ui_theme
from config import ROLE_COORDINATOR, ROLE_ADMIN

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

permissions.require_role([ROLE_COORDINATOR, ROLE_ADMIN, "demo_coordinator"])

ui_theme.render_header(
    title="Courses & Academic Departments",
    subtitle="Manage institutional academic divisions, degree curricula, program duration, and tracks",
    badge_text="Academic Structure",
    badge_variant="primary",
)

current_user = permissions.get_current_user()

tab_dept, tab_course = st.tabs(["Departments", "Degree Courses & Programs"])

# ============================================================================
# TAB 1: Departments
# ============================================================================
with tab_dept:
    st.subheader("Academic Departments Directory")
    depts_df = database.get_all_departments()

    col_d1, col_d2 = st.columns([3, 2])
    with col_d1:
        if not depts_df.empty:
            st.dataframe(
                depts_df.rename(columns={
                    "id": "ID",
                    "department_code": "Code",
                    "department_name": "Department Name",
                    "description": "Description",
                    "is_active": "Active",
                    "created_at": "Created Date",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No departments registered.")

    with col_d2:
        st.write("##### ➕ Add New Department")
        with st.form("new_dept_form"):
            d_code = st.text_input("Department Code *", placeholder="e.g. MECH").strip().upper()
            d_name = st.text_input("Department Name *", placeholder="e.g. Mechanical Engineering").strip()
            d_desc = st.text_area("Description", placeholder="Discipline focus...")
            btn_add_dept = st.form_submit_button("Register Department", type="primary", use_container_width=True)

            if btn_add_dept:
                if not d_code or not d_name:
                    st.error("Department code and name are required.")
                else:
                    try:
                        dept_id = database.add_department(d_code, d_name, d_desc)
                        database.log_audit_action(
                            username=current_user.get("username", "coordinator") if current_user else "coordinator",
                            role="coordinator",
                            action="CREATE_DEPARTMENT",
                            entity_type="DEPARTMENT",
                            entity_id=str(dept_id),
                            new_values=f"code: {d_code}, name: {d_name}",
                            reason="Department established by coordinator",
                        )
                        st.success(f"Department '{d_name}' registered successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating department: {str(e)}")

        if not depts_df.empty:
            st.write("##### ✏️ Edit Department")
            edit_dept_id = st.selectbox(
                "Select Department",
                depts_df["id"].tolist(),
                format_func=lambda did: f"{depts_df[depts_df['id'] == did].iloc[0]['department_code']} - {depts_df[depts_df['id'] == did].iloc[0]['department_name']}"
            )
            d_row = depts_df[depts_df["id"] == edit_dept_id].iloc[0]
            with st.form("edit_dept_form"):
                ed_code = st.text_input("Code", value=d_row["department_code"]).strip().upper()
                ed_name = st.text_input("Name", value=d_row["department_name"]).strip()
                ed_desc = st.text_area("Description", value=d_row.get("description", ""))
                ed_act = st.checkbox("Active Status", value=bool(d_row["is_active"]))
                btn_up_dept = st.form_submit_button("Save Department Changes", type="secondary", use_container_width=True)
                if btn_up_dept:
                    database.update_department(edit_dept_id, ed_code, ed_name, ed_desc, 1 if ed_act else 0)
                    st.success("Department updated successfully.")
                    st.rerun()

# ============================================================================
# TAB 2: Courses & Programs
# ============================================================================
with tab_course:
    st.subheader("Academic Programs & Degree Tracks")
    courses_df = database.get_all_courses()

    col_c1, col_c2 = st.columns([3, 2])
    with col_c1:
        if not courses_df.empty:
            st.dataframe(
                courses_df.rename(columns={
                    "id": "ID",
                    "course_code": "Code",
                    "course_name": "Course Name",
                    "department_name": "Department",
                    "duration_years": "Duration (Years)",
                    "total_semesters": "Total Semesters",
                    "is_active": "Active",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No courses registered.")

    with col_c2:
        st.write("##### ➕ Register New Course")
        dept_names = depts_df["department_name"].tolist() if not depts_df.empty else ["Computer Science and Engineering"]
        with st.form("new_course_form"):
            c_code = st.text_input("Course Code *", placeholder="e.g. BTECH_DS").strip().upper()
            c_name = st.text_input("Course Name *", placeholder="e.g. B.Tech Data Science").strip()
            c_dept = st.selectbox("Affiliated Department *", dept_names)
            c_dur = st.number_input("Duration (Years)", min_value=1, max_value=6, value=4)
            c_sem = st.number_input("Total Semesters", min_value=1, max_value=12, value=8)
            btn_add_c = st.form_submit_button("Register Course", type="primary", use_container_width=True)

            if btn_add_c:
                if not c_code or not c_name:
                    st.error("Course code and name are required.")
                else:
                    try:
                        cid = database.add_course(c_code, c_name, c_dept, c_dur, c_sem)
                        database.log_audit_action(
                            username=current_user.get("username", "coordinator") if current_user else "coordinator",
                            role="coordinator",
                            action="CREATE_COURSE",
                            entity_type="COURSE",
                            entity_id=str(cid),
                            new_values=f"code: {c_code}, name: {c_name}, dept: {c_dept}",
                            reason="Course curriculum established by coordinator",
                        )
                        st.success(f"Course '{c_name}' created successfully.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating course: {str(e)}")
