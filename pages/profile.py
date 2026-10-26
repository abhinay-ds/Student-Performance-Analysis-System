"""
Profile Page: Displays official academic identification and contact credentials.
For students, official academic records (ID, department, semester) are strictly read-only.
"""

import streamlit as st
import database
import auth
import permissions
import ui_theme

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

if not permissions.is_authenticated():
    st.warning("Access restricted. Please sign in to the portal.")
    st.stop()

if permissions.is_student():
    student = permissions.get_current_student_profile()
    if not student:
        st.info("No student profile linked.")
        st.stop()

    ui_theme.render_header(
        title="Student Academic Profile",
        subtitle=f"Official enrollment identification and records for {student['full_name']} ({student['student_id']})",
        badge_text="Verified Student",
        badge_variant="success",
    )

    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Institutional Roll No / Student ID", value=student["student_id"], disabled=True)
            st.text_input("Full Legal Name", value=student["full_name"], disabled=True)
            st.text_input("Institutional Email", value=student["email"], disabled=True)
        with c2:
            st.text_input("Academic Department", value=student["department"], disabled=True)
            st.text_input("Degree Program / Course", value=student["course"], disabled=True)
            st.text_input("Current Semester", value=str(student["semester"]), disabled=True)

    st.caption("Official academic records are governed by the registrar and cannot be modified directly.")

else:
    active_prof_user = permissions.get_active_professor_username()
    prof_user_row = database.get_user_by_username(active_prof_user)
    prof = database.get_professor_by_user_id(prof_user_row["id"]) if prof_user_row else None

    name_val = prof["full_name"] if prof else ("Dr. Neha Kapoor" if active_prof_user == "dr_kapoor" else "Prof. Arjun Malhotra")
    email_val = prof["email"] if prof else f"{active_prof_user}@example.com"
    dept_val = prof["department"] if prof else "Computer Science and Engineering"

    role_lbl = "Coordinator Profile" if permissions.is_coordinator() else "Faculty Profile"

    ui_theme.render_header(
        title=role_lbl,
        subtitle="Institutional credentials, affiliation, and access permissions",
        badge_text="Active Staff",
        badge_variant="primary",
    )

    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Username", value=active_prof_user, disabled=True)
        st.text_input("Full Name", value=name_val, disabled=True)
    with c2:
        st.text_input("Institutional Email", value=email_val, disabled=True)
        st.text_input("Department", value=dept_val, disabled=True)
