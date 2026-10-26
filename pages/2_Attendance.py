"""
Page 2: Student Attendance Portal.
Provides overall cumulative attendance percentage, subject-by-subject attendance
breakdowns, classes attended vs total sessions, and date-by-date attendance logs.
"""

import streamlit as st
import auth
import permissions
import attendance_service
import ui_theme
from config import ATTENDANCE_SUPPORT_THRESHOLD

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

if not permissions.is_authenticated():
    st.warning("Access restricted. Please sign in to the portal.")
    st.stop()

student = permissions.get_current_student_profile()
if not student:
    st.info("No student profile is linked to this session.")
    st.stop()

stu_id = student["id"]

# Calculate Overall Attendance
att_summary = attendance_service.get_student_overall_attendance(stu_id)

badge_variant = "warning" if att_summary["is_low_attendance"] else "success"
badge_text = "Action Required" if att_summary["is_low_attendance"] else "Good Standing"

ui_theme.render_header(
    title="My Attendance Record",
    subtitle=f"Official tracking for {student['full_name']} ({student['student_id']}) — Minimum threshold: {ATTENDANCE_SUPPORT_THRESHOLD}%",
    badge_text=badge_text,
    badge_variant=badge_variant,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cumulative Attendance", f"{att_summary['percentage']}%",
          "- Below Threshold" if att_summary["is_low_attendance"] else "+ Satisfactory",
          delta_color="inverse" if att_summary["is_low_attendance"] else "normal")
c2.metric("Total Classes Conducted", att_summary["total_classes"])
c3.metric("Classes Attended", att_summary["attended_classes"])
missed = max(0, att_summary["total_classes"] - att_summary["attended_classes"])
c4.metric("Classes Missed", missed)

# Threshold Warning Alert
if att_summary["is_low_attendance"]:
    st.error(
        f"Attendance Advisory: Your cumulative attendance is {att_summary['percentage']}%, "
        f"which is below the required minimum threshold of {ATTENDANCE_SUPPORT_THRESHOLD}%. "
        "Students with attendance below 75% risk debarment from end-semester examinations."
    )
else:
    st.success(f"Your attendance meets the university minimum requirement (≥ {ATTENDANCE_SUPPORT_THRESHOLD}%).")

st.write("")

# Subject-Wise Breakdown Table
st.subheader("Subject-Wise Attendance Breakdown")
sub_df = attendance_service.get_student_subject_breakdown(stu_id)

if not sub_df.empty:
    st.dataframe(
        sub_df[
            [
                "subject_code",
                "subject_name",
                "total_sessions",
                "attended_sessions",
                "late_sessions",
                "absent_sessions",
                "attendance_percentage",
            ]
        ].rename(
            columns={
                "subject_code": "Code",
                "subject_name": "Subject Name",
                "total_sessions": "Total Sessions",
                "attended_sessions": "Attended",
                "late_sessions": "Late",
                "absent_sessions": "Absent",
                "attendance_percentage": "Attendance %",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No subject-wise attendance recorded yet.")

st.write("")

# Chronological Attendance History Log
st.subheader("Attendance Session History")
hist_df = attendance_service.database.get_student_attendance_history(stu_id)

if not hist_df.empty:
    st.dataframe(
        hist_df[
            ["session_date", "subject_code", "subject_name", "session_label", "status"]
        ].rename(
            columns={
                "session_date": "Date",
                "subject_code": "Code",
                "subject_name": "Subject",
                "session_label": "Session Type",
                "status": "Attendance Status",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No individual session attendance logs found for your profile.")
