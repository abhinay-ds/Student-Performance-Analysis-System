"""
Demo Environment Management Module (Coordinator / Admin Only).
Allows safe restoration of the baseline synthetic academic dataset,
inspecting demo records, and verifying test scenarios.
"""

import streamlit as st
import database
import auth
import permissions
import demo_seeder
import ui_theme
from config import ROLE_COORDINATOR, ROLE_ADMIN

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

permissions.require_role([ROLE_COORDINATOR, ROLE_ADMIN, "demo_coordinator"])

ui_theme.render_header(
    title="Demo Environment Management",
    subtitle="Manage synthetic evaluation data, test scenarios, and restore pristine baseline demo states",
    badge_text="Sandbox Controls",
    badge_variant="info",
)

current_user = permissions.get_current_user()

st.markdown(
    """
    <div class="saas-card">
        <div class="saas-card-header">
            <span class="saas-card-title">Demo Mode Architecture & Synchronized Baseline</span>
            <span class="badge badge-info">SYNCHRONIZED PERSISTENCE</span>
        </div>
        <p style="color: #475569; font-size: 14px; line-height: 1.6; margin: 0;">
            The Campus Performance Portal provides 4 fictional student profiles, 2 professors, and 5 academic courses.
            Evaluators can perform live attendance roll-calls, enter marks, submit assignments, and rename subjects.
            Use the control below to restore the evaluation baseline at any time.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_d1, col_d2 = st.columns([2, 1])

with col_d1:
    st.subheader("Pristine Baseline Specification")
    st.markdown(
        """
        Restoring the baseline will reset the academic database to:
        - **4 Fictional Students:**
          - `STU1001` Aarav Sharma (Consistently High Performance, 95% Attendance)
          - `STU1002` Priya Verma (Good Marks, weaker in Mathematics)
          - `STU1003` Rohan Mehta (Attendance <75%, alerts triggered, 2 subjects needing support)
          - `STU1004` Ananya Singh (Moderate marks with clear improvement trend)
        - **2 Faculty Members:**
          - Dr. Neha Kapoor (Python Programming & DBMS)
          - Prof. Arjun Malhotra (Mathematics, Computer Networks, Data Structures)
        - **5 Standard Subjects:** CS301, CS302, MA301, CS303, CS304
        - **50 Class Attendance Sessions & 200 Roll-Call Records**
        - **40 Examination Marks Records across 2 Assessment Periods (Mid-Term & End-Semester)**
        - **5 Coursework Assignments & 5 Downloadable Educational Documents**
        - **4 Official Announcements**
        """
    )

with col_d2:
    st.subheader("Reset Demo Baseline")
    st.caption("Press below to wipe experimental edits and restore the baseline dataset.")
    confirm_check = st.checkbox("I confirm I want to reset the demo database to standard baseline.")
    if st.button("Reset Demo Data to Baseline", type="primary", disabled=not confirm_check, use_container_width=True):
        with st.spinner("Restoring pristine demo baseline..."):
            demo_seeder.reset_demo_data(actor_user=current_user)
        st.success("Demo baseline restored successfully. Standard student rosters, courses, attendance, and evaluation marks are reset.")
        st.rerun()

st.divider()
st.subheader("Current Dataset Verification")
col_c1, col_c2, col_c3, col_c4 = st.columns(4)
col_c1.metric("Students Cataloged", len(database.get_all_students()))
col_c2.metric("Subjects Cataloged", len(database.get_all_subjects()))
col_c3.metric("Faculty Members", len(database.get_all_professors_detailed()))
col_c4.metric("Assignments Active", len(database.get_assignments()))
