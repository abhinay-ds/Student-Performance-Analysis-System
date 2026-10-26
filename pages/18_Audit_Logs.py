"""
Administrative Audit Trail & Governance Log Viewer (Coordinator / Admin Only).
Allows inspecting, searching, filtering, and exporting records of administrative actions
including attendance corrections, marks updates, subject modifications, and password resets.
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
    title="Administrative Audit Trail",
    subtitle="Immutable log of administrative corrections, policy revisions, account status changes, and evaluations",
    badge_text="Compliance & Governance",
    badge_variant="primary",
)

col_a, col_e, col_s = st.columns([1, 1, 2])
with col_a:
    action_filter = st.selectbox(
        "Action Filter",
        ["All", "CORRECT_ATTENDANCE", "CORRECT_MARKS", "APPROVE_RESULTS", "UPDATE_SUBJECT", "CREATE_SUBJECT", "ASSIGN_PROFESSOR_SUBJECT", "ACTIVATE_USER", "DEACTIVATE_USER", "RESET_PASSWORD", "UPDATE_THRESHOLDS", "RESET_DEMO_DATA"]
    )
with col_e:
    entity_filter = st.selectbox(
        "Entity Filter",
        ["All", "ATTENDANCE_RECORD", "ACADEMIC_RECORD", "ACADEMIC_RECORDS", "SUBJECT", "USER", "FACULTY", "SETTINGS", "SYSTEM"]
    )
with col_s:
    search_query = st.text_input("Search Logs", placeholder="Search by username, reason, or entity ID...")

limit_sel = st.selectbox("Entries to Display", [50, 100, 200, 500], index=1)

logs_df = database.get_audit_logs(
    limit=limit_sel,
    action_filter=action_filter if action_filter != "All" else None,
    entity_filter=entity_filter if entity_filter != "All" else None,
    search=search_query if search_query else None,
)

if not logs_df.empty:
    st.write(f"Showing **{len(logs_df)}** audit log entries:")

    # Summary Table
    display_df = logs_df[["id", "created_at", "username", "role", "action", "entity_type", "entity_id", "reason"]].copy()
    st.dataframe(
        display_df.rename(columns={
            "id": "Log ID",
            "created_at": "Timestamp",
            "username": "Actor",
            "role": "Role",
            "action": "Action",
            "entity_type": "Entity",
            "entity_id": "Target ID",
            "reason": "Justification Reason",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.write("")
    st.write("##### Detailed Log State (Before / After Modifications)")
    for _, log in logs_df.head(10).iterrows():
        with st.expander(f"Log #{log['id']} — {log['action']} by {log['username']} ({log['created_at']})"):
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Entity:** `{log['entity_type']}` (ID: `{log['entity_id']}`)")
                st.write(f"**Actor:** `{log['username']}` (Role: `{log['role']}`)")
                st.write(f"**Justification Reason:** *{log['reason'] or 'None provided'}*")
            with c2:
                if log["old_values"]:
                    st.markdown("**Previous State (Old):**")
                    st.code(log["old_values"], language="text")
                if log["new_values"]:
                    st.markdown("**Updated State (New):**")
                    st.code(log["new_values"], language="text")

    st.divider()
    # CSV Export
    csv_bytes = logs_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Audit Log to CSV",
        data=csv_bytes,
        file_name="campus_portal_audit_logs.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("No audit logs matching the criteria.")
