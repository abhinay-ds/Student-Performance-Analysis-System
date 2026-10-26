"""
Professor & Faculty Management Module (Coordinator / Admin Only).
Allows viewing faculty profiles, creating new professor accounts, assigning subjects,
deactivating/reactivating accounts, and securely resetting passwords.
"""

import streamlit as st
import database
import auth
import permissions
import ui_theme
from config import ROLE_COORDINATOR, ROLE_ADMIN, DEPARTMENTS

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

# Server-side authorization check
permissions.require_role([ROLE_COORDINATOR, ROLE_ADMIN, "demo_coordinator"])

ui_theme.render_header(
    title="Faculty Directory & Governance",
    subtitle="Manage faculty accounts, institutional course allocations, account status, and credentials",
    badge_text="Faculty Governance",
    badge_variant="primary",
)

tab_list, tab_add, tab_assign, tab_reset = st.tabs([
    "Faculty Directory",
    "Register Faculty",
    "Subject Allocation",
    "Password & Status Management"
])

current_user = permissions.get_current_user()

# ============================================================================
# TAB 1: Faculty Directory
# ============================================================================
with tab_list:
    st.subheader("Institutional Faculty Roster")
    profs_df = database.get_all_professors_detailed()
    if not profs_df.empty:
        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            search_prof = st.text_input("🔍 Search Faculty (Name, Username, Department)", placeholder="e.g. Neha, dr_kapoor, Computer Science")
        with col_f2:
            status_filter = st.selectbox("Status Filter", ["All", "Active", "Inactive"])

        filtered_df = profs_df.copy()
        if search_prof:
            s = search_prof.strip().lower()
            filtered_df = filtered_df[
                filtered_df["full_name"].str.lower().str.contains(s) |
                filtered_df["username"].str.lower().str.contains(s) |
                filtered_df["department"].str.lower().str.contains(s) |
                filtered_df["assigned_subjects"].str.lower().str.contains(s)
            ]

        if status_filter == "Active":
            filtered_df = filtered_df[filtered_df["is_active"] == 1]
        elif status_filter == "Inactive":
            filtered_df = filtered_df[filtered_df["is_active"] == 0]

        # Display Dataframe
        display_cols = ["user_id", "username", "full_name", "email", "department", "assigned_subjects", "is_active", "created_at"]
        st.dataframe(
            filtered_df[display_cols].rename(columns={
                "user_id": "User ID",
                "username": "Username",
                "full_name": "Full Name",
                "email": "Email Address",
                "department": "Department",
                "assigned_subjects": "Assigned Subjects",
                "is_active": "Active Status",
                "created_at": "Created Date",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No professor accounts recorded.")

# ============================================================================
# TAB 2: Register New Faculty
# ============================================================================
with tab_add:
    st.subheader("Create New Faculty Account")
    st.caption("Create an authenticated faculty account and link it to their institutional academic profile.")
    with st.form("add_prof_form"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            new_u = st.text_input("Username *", placeholder="e.g. prof_sharma").strip()
            new_p = st.text_input("Temporary Password * (min 6 chars)", type="password")
            new_name = st.text_input("Faculty Full Name *", placeholder="e.g. Dr. Rajesh Sharma").strip()
        with col_p2:
            new_email = st.text_input("Official Email *", placeholder="e.g. r.sharma@example.com").strip()
            new_dept = st.selectbox("Department *", DEPARTMENTS)
            st.caption("Initial role will be set to 'professor'.")

        btn_add_prof = st.form_submit_button("Register Faculty Member", type="primary", use_container_width=True)
        if btn_add_prof:
            if not new_u or not new_p or not new_name or not new_email:
                st.error("Please fill in all required fields.")
            else:
                ok, msg = auth.register_user(new_u, new_p, role="professor")
                if ok:
                    u_rec = database.get_user_by_username(new_u)
                    if u_rec:
                        database.create_professor_profile(u_rec["id"], new_name, new_email, new_dept)
                        database.log_audit_action(
                            username=current_user.get("username", "coordinator") if current_user else "coordinator",
                            role="coordinator",
                            action="CREATE_FACULTY",
                            entity_type="FACULTY",
                            entity_id=str(u_rec["id"]),
                            new_values=f"username: {new_u}, name: {new_name}, dept: {new_dept}",
                            reason="New faculty onboarded by coordinator",
                        )
                    st.success(f"Faculty account '{new_u}' successfully registered.")
                    st.rerun()
                else:
                    st.error(msg)

# ============================================================================
# TAB 3: Subject Allocation
# ============================================================================
with tab_assign:
    st.subheader("Assign Faculty to Academic Subjects")
    st.caption("Authorize professors to manage student attendance, mark submissions, and coursework.")

    profs = database.get_all_professors_detailed()
    subjects_df = database.get_all_subjects()

    if not profs.empty and not subjects_df.empty:
        prof_options = {row["user_id"]: f"{row['full_name']} ({row['username']}) - {row['department']}" for _, row in profs.iterrows()}
        subj_options = {row["id"]: f"{row['subject_code']} - {row['subject_name']} ({row['course']} Sem {row['semester']})" for _, row in subjects_df.iterrows()}

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.write("##### ➕ Assign Subject")
            sel_prof_id = st.selectbox("Select Faculty", list(prof_options.keys()), format_func=lambda k: prof_options[k], key="assign_prof_sel")
            sel_subj_id = st.selectbox("Select Subject", list(subj_options.keys()), format_func=lambda k: subj_options[k], key="assign_subj_sel")
            acad_year = st.text_input("Academic Year", value="2024-2025")

            if st.button("Assign Subject to Faculty", type="primary", use_container_width=True):
                database.assign_professor_to_subject(sel_prof_id, sel_subj_id, academic_year=acad_year)
                database.log_audit_action(
                    username=current_user.get("username", "coordinator") if current_user else "coordinator",
                    role="coordinator",
                    action="ASSIGN_PROFESSOR_SUBJECT",
                    entity_type="PROFESSOR_SUBJECT",
                    entity_id=f"user:{sel_prof_id}_subject:{sel_subj_id}",
                    new_values=f"Assigned subject {subj_options[sel_subj_id]} to {prof_options[sel_prof_id]}",
                    reason="Subject allocated by coordinator",
                )
                st.success("Subject successfully assigned.")
                st.rerun()

        with col_a2:
            st.write("##### 🗑️ Current Assignments & Removal")
            cur_subjs = database.get_professor_assigned_subjects(sel_prof_id)
            if cur_subjs:
                st.write(f"**Currently Assigned Subjects for {prof_options[sel_prof_id]}:**")
                for s_name in cur_subjs:
                    s_match = subjects_df[subjects_df["subject_name"] == s_name]
                    if not s_match.empty:
                        sub_id_del = int(s_match.iloc[0]["id"])
                        c_del1, c_del2 = st.columns([3, 1])
                        c_del1.write(f"• **{s_name}**")
                        if c_del2.button("Remove", key=f"del_subj_{sel_prof_id}_{sub_id_del}", type="secondary"):
                            database.remove_professor_from_subject(sel_prof_id, sub_id_del, academic_year=acad_year)
                            database.log_audit_action(
                                username=current_user.get("username", "coordinator") if current_user else "coordinator",
                                role="coordinator",
                                action="REMOVE_PROFESSOR_SUBJECT",
                                entity_type="PROFESSOR_SUBJECT",
                                entity_id=f"user:{sel_prof_id}_subject:{sub_id_del}",
                                old_values=f"Removed subject {s_name} from {prof_options[sel_prof_id]}",
                                reason="Subject unassigned by coordinator",
                            )
                            st.rerun()
            else:
                st.info("No subjects currently assigned to this faculty member.")

# ============================================================================
# TAB 4: Password & Status Management
# ============================================================================
with tab_reset:
    st.subheader("Account Governance & Credential Reset")
    st.caption("Reactivate/deactivate faculty accounts and reset temporary passwords.")

    if not profs.empty:
        target_prof_id = st.selectbox(
            "Select Faculty Account",
            list(prof_options.keys()),
            format_func=lambda k: prof_options[k],
            key="status_prof_sel",
        )
        target_row = profs[profs["user_id"] == target_prof_id].iloc[0]

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.write("##### 🔄 Account Status")
            is_currently_active = bool(target_row["is_active"])
            status_text = "🟢 Active" if is_currently_active else "🔴 Deactivated"
            st.write(f"Current Status: **{status_text}**")
            new_status_toggle = st.radio("Modify Account Access", ["Active", "Deactivated"], index=0 if is_currently_active else 1)
            reason_status = st.text_input("Reason for Status Change", placeholder="e.g. Sabbatical leave, retired, new appointment")
            if st.button("Apply Status Change", type="primary"):
                target_act = 1 if new_status_toggle == "Active" else 0
                database.set_user_active_status(target_prof_id, target_act, actor_user=current_user, reason=reason_status)
                st.success(f"Account status updated to {new_status_toggle}.")
                st.rerun()

        with col_s2:
            st.write("##### 🔑 Secure Password Reset")
            new_pwd = st.text_input("New Temporary Password (min 6 chars)", type="password", key="reset_prof_pwd")
            confirm_new_pwd = st.text_input("Confirm New Password", type="password", key="reset_prof_confirm_pwd")
            if st.button("Reset Faculty Password", type="secondary"):
                if new_pwd != confirm_new_pwd:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = database.admin_reset_password(target_prof_id, new_pwd, actor_user=current_user)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
