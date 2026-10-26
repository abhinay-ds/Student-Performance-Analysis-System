"""
Campus Performance Portal - Student Performance Analysis System.
Main Application Entry Point with Role-Based Navigation Routing.
Supports Student Login, Professor Login, Coordinator Login, and Safe Interactive Demo Sessions.
"""

import streamlit as st
import database
import auth
import permissions
import demo_seeder
import ui_theme
from config import APP_NAME, APP_SUBTITLE, ROLE_STUDENT, ROLE_PROFESSOR, ROLE_COORDINATOR, ROLE_ADMIN

st.set_page_config(
    page_title="Campus Performance Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize schema and seed demo data
database.init_db()
demo_seeder.seed_demo_data()
auth.init_session_state()
ui_theme.inject_global_theme()


def render_login_view():
    """Render the central Campus Performance Portal Login Screen."""
    st.markdown(
        """
        <div style="text-align: center; margin-top: 16px; margin-bottom: 28px;">
            <span class="badge badge-primary" style="margin-bottom: 10px; font-size: 11px;">ACADEMIC MANAGEMENT PLATFORM</span>
            <h1 style="color: #142B4A; font-size: 28px; font-weight: 800; letter-spacing: -0.5px; margin: 8px 0 6px 0;">
                Campus Performance Portal
            </h1>
            <p style="color: #64748B; font-size: 14px; max-width: 580px; margin: 0 auto;">
                Institutional analytics, student records management, and academic governance
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        tabs = st.tabs([
            "Student Access",
            "Faculty Access",
            "Coordinator Administration",
            "Interactive Demo",
            "Register",
        ])

        # --------------------------------------------------------------------
        # Tab 1: Student Login
        # --------------------------------------------------------------------
        with tabs[0]:
            st.markdown("#### Student Portal Sign-In")
            st.caption("Access personal performance, attendance tracking, coursework, and notices.")
            with st.form("student_login_form"):
                stu_ident = st.text_input("Username or Student ID", placeholder="e.g. aarav or STU1001").strip()
                stu_pwd = st.text_input("Password", type="password")
                btn_stu = st.form_submit_button("Sign In as Student", type="primary", use_container_width=True)

                if btn_stu:
                    with st.spinner("Authenticating credentials..."):
                        user = auth.authenticate_credentials(stu_ident, stu_pwd)
                    if user and user["role"] in [ROLE_STUDENT, ROLE_ADMIN]:
                        auth.login_user(user)
                        st.success(f"Welcome back, {user['username']}!")
                        st.rerun()
                    else:
                        st.error("Invalid student credentials. Please verify your username or Student ID (e.g. STU1001) and password.")

            with st.expander("Sample Student Demo Credentials", expanded=False):
                st.markdown(
                    """
                    All demo student accounts use password: `Student123!`
                    - `STU1001` (username: `aarav`) — High marks, 95% attendance
                    - `STU1002` (username: `priya`) — Good marks, weaker in Mathematics
                    - `STU1003` (username: `rohan`) — Low attendance (<75%), needs academic support
                    - `STU1004` (username: `ananya`) — Moderate marks, improving trend
                    """
                )

        # --------------------------------------------------------------------
        # Tab 2: Professor Login
        # --------------------------------------------------------------------
        with tabs[1]:
            st.markdown("#### Faculty Sign-In")
            st.caption("Manage student rosters, record daily attendance, enter marks, and publish materials.")
            with st.form("prof_login_form"):
                prof_user = st.text_input("Faculty Username", placeholder="e.g. dr_kapoor or prof_malhotra").strip()
                prof_pwd = st.text_input("Password", type="password")
                btn_prof = st.form_submit_button("Sign In as Faculty", type="primary", use_container_width=True)

                if btn_prof:
                    with st.spinner("Verifying faculty authorization..."):
                        user = auth.authenticate_credentials(prof_user, prof_pwd, expected_role=ROLE_PROFESSOR)
                    if user:
                        auth.login_user(user)
                        st.success(f"Welcome, Professor {user['username']}!")
                        st.rerun()
                    else:
                        st.error("Invalid faculty credentials. Please check your username and password.")

            with st.expander("Sample Faculty Demo Credentials", expanded=False):
                st.markdown(
                    """
                    All demo faculty accounts use password: `Professor123!`
                    - `dr_kapoor` — Dr. Neha Kapoor (Python Programming & DBMS)
                    - `prof_malhotra` — Prof. Arjun Malhotra (Mathematics, Computer Networks, Data Structures)
                    """
                )

        # --------------------------------------------------------------------
        # Tab 3: Coordinator Login
        # --------------------------------------------------------------------
        with tabs[2]:
            st.markdown("#### Coordinator Administration")
            st.caption("Curricular governance: manage courses, faculty assignments, attendance corrections, and results.")
            with st.form("coord_login_form"):
                coord_user = st.text_input("Administrator Username", placeholder="e.g. coordinator").strip()
                coord_pwd = st.text_input("Password", type="password")
                btn_coord = st.form_submit_button("Sign In as Coordinator", type="primary", use_container_width=True)

                if btn_coord:
                    with st.spinner("Authenticating administrator credentials..."):
                        user = auth.authenticate_credentials(coord_user, coord_pwd, expected_role=ROLE_COORDINATOR)
                    if user:
                        auth.login_user(user)
                        st.success(f"Welcome, Coordinator {user['username']}!")
                        st.rerun()
                    else:
                        st.error("Invalid coordinator credentials. Access restricted to authorized administrative personnel.")

            st.caption("Coordinator credentials can also be generated via `python init_coordinator.py`.")

        # --------------------------------------------------------------------
        # Tab 4: Demo Login
        # --------------------------------------------------------------------
        with tabs[3]:
            st.markdown("#### Interactive Multi-Role Demo Mode")
            st.caption(
                "Explore the portal using a synchronized synthetic academic dataset. "
                "Changes made by faculty or coordinators reflect in student records immediately."
            )

            st.write("")
            d1, d2, d3 = st.columns(3)
            with d1:
                if st.button("Student Demo\n(4 Personas)", use_container_width=True, type="primary"):
                    auth.start_demo_session(demo_role="demo_student")
                    st.rerun()
            with d2:
                if st.button("Faculty Demo\n(2 Instructors)", use_container_width=True, type="secondary"):
                    auth.start_demo_session(demo_role="demo_professor")
                    st.rerun()
            with d3:
                if st.button("Coordinator Tour\n(Full Admin)", use_container_width=True, type="secondary"):
                    auth.start_demo_session(demo_role="demo_coordinator")
                    st.rerun()

            st.markdown(
                """
                ---
                <div style="font-size: 13px; color: #475569; line-height: 1.6;">
                    <b>Synthetic Dataset Highlights:</b><br/>
                    • 4 students with distinct performance and attendance patterns<br/>
                    • 2 faculty members across 5 core university subjects<br/>
                    • 50 attendance sessions, 200 roll-call records, and 40 exam scores<br/>
                    • Coursework assignments, study materials, and audit history
                </div>
                """,
                unsafe_allow_html=True,
            )

        # --------------------------------------------------------------------
        # Tab 5: Register New User
        # --------------------------------------------------------------------
        with tabs[4]:
            st.markdown("#### New Account Registration")
            st.caption("Create a new institutional user profile.")
            with st.form("reg_form"):
                reg_u = st.text_input("Choose Username").strip()
                reg_p = st.text_input("Choose Password (min 6 characters)", type="password")
                reg_cp = st.text_input("Confirm Password", type="password")
                reg_r = st.selectbox("Role", ["student", "professor"])
                btn_reg = st.form_submit_button("Create Account", use_container_width=True, type="primary")

                if btn_reg:
                    if reg_p != reg_cp:
                        st.error("Passwords do not match.")
                    else:
                        ok, msg = auth.register_user(reg_u, reg_p, role=reg_r)
                        if ok:
                            st.success(f"{msg} You can now sign in.")
                        else:
                            st.error(msg)


# ============================================================================
# Role-Based Page Routing with st.navigation
# ============================================================================

if not permissions.is_authenticated():
    # Only render the Login Page in the navigation tree
    pg = st.navigation([st.Page(render_login_view, title="Sign In", icon="🔐", default=True)])
    pg.run()
else:
    # Build permitted page list strictly based on role
    if permissions.is_coordinator():
        coordinator_sections = {
            "Academic Operations": [
                st.Page("pages/1_Home.py", title="Overview Dashboard", icon="📊", default=True),
                st.Page("pages/7_Student_Management.py", title="Student Directory", icon="👥"),
                st.Page("pages/13_Professor_Management.py", title="Faculty Directory", icon="🎓"),
                st.Page("pages/14_Subject_Management.py", title="Curriculum & Subjects", icon="📘"),
                st.Page("pages/15_Course_Department_Management.py", title="Courses & Departments", icon="🏛️"),
                st.Page("pages/16_Enrollment_Management.py", title="Enrollments & Allocations", icon="📋"),
            ],
            "Evaluation & Records": [
                st.Page("pages/8_Attendance_Management.py", title="Attendance Management", icon="📅"),
                st.Page("pages/9_Marks_Management.py", title="Marks & Grade Entry", icon="📝"),
                st.Page("pages/10_Dataset_Upload.py", title="Batch Dataset Upload", icon="📤"),
            ],
            "Coursework & Notices": [
                st.Page("pages/4_Assignments.py", title="Assignments", icon="📁"),
                st.Page("pages/5_Study_Materials.py", title="Study Materials", icon="📚"),
                st.Page("pages/6_Announcements.py", title="Announcements", icon="📢"),
            ],
            "Governance & Insights": [
                st.Page("pages/11_Academic_Analytics.py", title="Academic Analytics", icon="📈"),
                st.Page("pages/12_Reports.py", title="Reports & Export", icon="📑"),
                st.Page("pages/17_System_Settings.py", title="System Settings", icon="⚙️"),
                st.Page("pages/18_Audit_Logs.py", title="Audit Trail", icon="🛡️"),
                st.Page("pages/19_Demo_Management.py", title="Demo Management", icon="🔄"),
                st.Page("pages/profile.py", title="My Profile", icon="👤"),
            ],
        }
        pg = st.navigation(coordinator_sections)

    elif permissions.is_student():
        student_sections = {
            "Academic Progress": [
                st.Page("pages/1_Home.py", title="Student Dashboard", icon="📊", default=True),
                st.Page("pages/2_Attendance.py", title="My Attendance", icon="📅"),
                st.Page("pages/3_Academic_Performance.py", title="Academic Performance", icon="📈"),
                st.Page("pages/12_Reports.py", title="Academic Transcript", icon="📑"),
            ],
            "Coursework & Resources": [
                st.Page("pages/4_Assignments.py", title="Assignments", icon="📁"),
                st.Page("pages/5_Study_Materials.py", title="Study Materials", icon="📚"),
                st.Page("pages/6_Announcements.py", title="Announcements", icon="📢"),
                st.Page("pages/profile.py", title="Student Profile", icon="👤"),
            ],
        }
        pg = st.navigation(student_sections)

    else:
        professor_sections = {
            "Teaching Operations": [
                st.Page("pages/1_Home.py", title="Faculty Dashboard", icon="📊", default=True),
                st.Page("pages/7_Student_Management.py", title="Student Roster", icon="👥"),
                st.Page("pages/8_Attendance_Management.py", title="Attendance Management", icon="📅"),
                st.Page("pages/9_Marks_Management.py", title="Marks & Grade Entry", icon="📝"),
            ],
            "Coursework & Content": [
                st.Page("pages/4_Assignments.py", title="Course Assignments", icon="📁"),
                st.Page("pages/5_Study_Materials.py", title="Study Materials", icon="📚"),
                st.Page("pages/6_Announcements.py", title="Announcements", icon="📢"),
            ],
            "Analytics & Records": [
                st.Page("pages/10_Dataset_Upload.py", title="Dataset Upload", icon="📤"),
                st.Page("pages/11_Academic_Analytics.py", title="Academic Analytics", icon="📈"),
                st.Page("pages/12_Reports.py", title="Reports & Export", icon="📑"),
                st.Page("pages/profile.py", title="Faculty Profile", icon="👤"),
            ],
        }
        pg = st.navigation(professor_sections)

    pg.run()
