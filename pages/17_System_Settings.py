"""
System Settings & Academic Policy Configuration Module (Coordinator / Admin Only).
Allows configuring minimum attendance thresholds, passing standards, institution name,
academic term year, file upload limits, and grading policy previews.
"""

import streamlit as st
import database
import auth
import permissions
import ui_theme
from config import (
    ROLE_COORDINATOR, ROLE_ADMIN, DEFAULT_SYSTEM_SETTINGS,
    ATTENDANCE_SUPPORT_THRESHOLD, PASS_MARK_THRESHOLD, SUPPORT_NEEDED_SCORE_THRESHOLD,
    MAX_UPLOAD_FILE_SIZE_MB, GRADE_RULES, APP_NAME
)

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

permissions.require_role([ROLE_COORDINATOR, ROLE_ADMIN, "demo_coordinator"])

ui_theme.render_header(
    title="System Settings & Policy Configuration",
    subtitle="Configure academic evaluation standards, attendance alert thresholds, grading criteria, and parameters",
    badge_text="System Administration",
    badge_variant="primary",
)

current_user = permissions.get_current_user()

tab_general, tab_thresholds, tab_grading, tab_uploads = st.tabs([
    "Institution & Term",
    "Academic Thresholds",
    "Grading Policy",
    "Uploads & Storage"
])

# ============================================================================
# TAB 1: Institution & Term
# ============================================================================
with tab_general:
    st.subheader("Institutional Branding & Academic Year")
    cur_name = database.get_system_setting("institution_name", default=APP_NAME)
    cur_year = database.get_system_setting("current_academic_year", default="2024-2025")

    with st.form("general_settings_form"):
        new_inst_name = st.text_input("Institution Display Name", value=str(cur_name))
        new_acad_year = st.text_input("Active Academic Session Year", value=str(cur_year))
        btn_save_general = st.form_submit_button("Save Institutional Information", type="primary")

        if btn_save_general:
            database.set_system_setting("institution_name", new_inst_name, data_type="string", updated_by=current_user.get("id") if current_user else None)
            database.set_system_setting("current_academic_year", new_acad_year, data_type="string", updated_by=current_user.get("id") if current_user else None)
            database.log_audit_action(
                username=current_user.get("username", "coordinator") if current_user else "coordinator",
                role="coordinator",
                action="UPDATE_SYSTEM_SETTINGS",
                entity_type="SETTINGS",
                new_values=f"institution_name: {new_inst_name}, academic_year: {new_acad_year}",
                reason="Institution information updated by coordinator",
            )
            st.success("Institutional settings updated.")
            st.rerun()

# ============================================================================
# TAB 2: Academic Thresholds
# ============================================================================
with tab_thresholds:
    st.subheader("Attendance & Academic Support Alerts")
    st.caption("Adjusting thresholds dynamically recalculates risk indicators on student, professor, and coordinator dashboards without altering historical session data.")

    cur_att = database.get_system_setting("minimum_attendance_threshold", default=ATTENDANCE_SUPPORT_THRESHOLD)
    cur_pass = database.get_system_setting("pass_mark_threshold", default=PASS_MARK_THRESHOLD)
    cur_support = database.get_system_setting("support_needed_threshold", default=SUPPORT_NEEDED_SCORE_THRESHOLD)

    with st.form("thresholds_form"):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            new_att = st.slider("Minimum Required Attendance (%)", min_value=50.0, max_value=95.0, value=float(cur_att), step=1.0)
            st.caption("Students with overall attendance below this value will receive low-attendance warnings and advisory notices.")

            new_pass = st.number_input("Minimum Passing Percentage (%)", min_value=30.0, max_value=60.0, value=float(cur_pass), step=1.0)
            st.caption("Marks below this total percentage constitute an academic failure (Grade F).")

        with col_t2:
            new_supp = st.number_input("Support-Needed Score Threshold (%)", min_value=35.0, max_value=75.0, value=float(cur_support), step=1.0)
            st.caption("Students scoring below this threshold are flagged in the analytics support quadrant for faculty intervention.")

            thresh_reason = st.text_input("Mandatory Reason for Threshold Change *", placeholder="e.g. Academic Council revision")

        btn_save_thresh = st.form_submit_button("Save Policy Thresholds", type="primary")

        if btn_save_thresh:
            if not thresh_reason:
                st.error("Documented reason required when updating academic thresholds.")
            else:
                database.set_system_setting("minimum_attendance_threshold", str(new_att), data_type="float", updated_by=current_user.get("id") if current_user else None)
                database.set_system_setting("pass_mark_threshold", str(new_pass), data_type="float", updated_by=current_user.get("id") if current_user else None)
                database.set_system_setting("support_needed_threshold", str(new_supp), data_type="float", updated_by=current_user.get("id") if current_user else None)
                database.log_audit_action(
                    username=current_user.get("username", "coordinator") if current_user else "coordinator",
                    role="coordinator",
                    action="UPDATE_THRESHOLDS",
                    entity_type="SETTINGS",
                    old_values=f"att: {cur_att}, pass: {cur_pass}, support: {cur_support}",
                    new_values=f"att: {new_att}, pass: {new_pass}, support: {new_supp}",
                    reason=thresh_reason,
                )
                st.success("Policy thresholds updated successfully.")
                st.rerun()

# ============================================================================
# TAB 3: Grading Policy Preview
# ============================================================================
with tab_grading:
    st.subheader("Institutional Grade Scale Standards")
    st.caption("Standard 10-point UGC/AICTE letter grade cutoffs configured in the portal.")

    import pandas as pd
    grades_df = pd.DataFrame(GRADE_RULES, columns=["Grade Letter", "Minimum Score %", "Grade Point", "Performance Descriptor"])
    st.dataframe(grades_df, use_container_width=True, hide_index=True)

    st.info("💡 **Grading Integrity Safeguard:** Letter grades are automatically derived upon result entry according to configured grade boundaries. Changes to boundaries require academic council validation and preview.")

# ============================================================================
# TAB 4: Uploads & Storage
# ============================================================================
with tab_uploads:
    st.subheader("File Upload Policies")
    cur_mb = database.get_system_setting("max_upload_size_mb", default=MAX_UPLOAD_FILE_SIZE_MB)

    with st.form("upload_settings_form"):
        new_mb = st.number_input("Max File Upload Size (MB)", min_value=5, max_value=100, value=int(cur_mb))
        st.write("**Supported File Types:**")
        st.code("Datasets: .csv, .xlsx\nStudy Materials: .pdf, .docx, .pptx, .txt, .png, .jpg, .jpeg")
        btn_save_up = st.form_submit_button("Save Upload Settings", type="primary")

        if btn_save_up:
            database.set_system_setting("max_upload_size_mb", str(new_mb), data_type="int", updated_by=current_user.get("id") if current_user else None)
            st.success("File upload policies updated.")
            st.rerun()
