"""
Page 6: Campus Announcements Board.
Students view department and cohort notifications published by faculty.
Professors publish targeted announcements by department, course, and semester.
"""

import streamlit as st
import database
import auth
import permissions
import ui_theme
from config import DEPARTMENTS, COURSES, SEMESTERS

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

if not permissions.is_authenticated():
    st.warning("Access restricted. Please sign in to the portal.")
    st.stop()

# ============================================================================
# STUDENT ANNOUNCEMENTS VIEW
# ============================================================================
if permissions.is_student():
    student = permissions.get_current_student_profile()
    if not student:
        st.info("No student profile linked.")
        st.stop()

    ann_df = database.get_announcements_for_student(
        student["department"], student["course"], student["semester"]
    )

    ui_theme.render_header(
        title="Campus Announcements",
        subtitle=f"Official departmental notices and examination bulletins for {student['department']}",
        badge_text=f"{len(ann_df)} Active Notices" if not ann_df.empty else "No Notices",
        badge_variant="info",
    )

    if ann_df.empty:
        st.info("No announcements published for your department or cohort at this time.")
    else:
        for _, ann in ann_df.iterrows():
            st.markdown(
                f"""
                <div class="saas-card">
                    <div class="saas-card-header">
                        <span class="saas-card-title">{ann['title']}</span>
                        {ui_theme.render_badge(ann['created_at'][:10], 'neutral')}
                    </div>
                    <p style="color: #334155; font-size: 14px; line-height: 1.6; margin: 0 0 10px 0;">{ann['message']}</p>
                    <small style="color: #94A3B8;">Target: {ann['department']} &bull; {ann['course']}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ============================================================================
# PROFESSOR ANNOUNCEMENTS MANAGEMENT VIEW
# ============================================================================
else:
    ui_theme.render_header(
        title="Announcements Management",
        subtitle="Publish notices and bulletins to academic departments and student cohorts",
        badge_text="Communications",
        badge_variant="primary",
    )

    tab_post, tab_history = st.tabs(["Broadcast Announcement", "Published Notices History"])

    with tab_post:
        st.subheader("Compose Campus Announcement")
        with st.form("broadcast_ann_form"):
            an_title = st.text_input("Announcement Headline *", placeholder="e.g. Schedule for Mid-Term Examination")

            c1, c2, c3 = st.columns(3)
            with c1:
                an_dept = st.selectbox("Target Department *", ["All"] + DEPARTMENTS)
            with c2:
                an_course = st.selectbox("Target Course *", ["All"] + COURSES)
            with c3:
                an_sem = st.selectbox("Target Semester (0 = All) *", [0] + SEMESTERS)

            an_msg = st.text_area("Detailed Message *", placeholder="Type notification body here...", height=150)
            submit_an = st.form_submit_button("Broadcast Notice", type="primary", use_container_width=True)

            if submit_an:
                if permissions.prevent_demo_mutation():
                    pass
                elif not an_title or not an_msg:
                    st.error("Headline and message are required.")
                else:
                    curr_user = permissions.get_current_user() or {}
                    database.add_announcement(
                        title=an_title,
                        message=an_msg,
                        department=an_dept,
                        course=an_course,
                        semester=an_sem,
                        created_by=curr_user.get("id"),
                    )
                    st.success(f"Announcement '{an_title}' broadcasted successfully!")
                    st.rerun()

    with tab_history:
        st.subheader("Active Announcements Archive")
        all_anns = database.get_all_announcements()
        if all_anns.empty:
            st.info("No announcements recorded.")
        else:
            st.dataframe(
                all_anns[["id", "title", "department", "course", "semester", "created_at"]].rename(
                    columns={
                        "id": "ID",
                        "title": "Headline",
                        "department": "Department",
                        "course": "Course",
                        "semester": "Sem",
                        "created_at": "Broadcast Date",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

