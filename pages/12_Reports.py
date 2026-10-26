"""
Page 12: Reports & Dataset Exports.
Students download their official academic transcripts and personal attendance summaries.
Professors export multi-worksheet Excel workbooks via OpenPyXL, attendance matrices,
and filtered CSV datasets.
"""

from datetime import datetime
import streamlit as st
import pandas as pd
import database
import auth
import permissions
import analytics
import report_generator
import attendance_service
import ui_theme
from config import DEPARTMENTS, SEMESTERS

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

if not permissions.is_authenticated():
    st.warning("Access restricted. Please sign in to the portal.")
    st.stop()

# ============================================================================
# STUDENT REPORTS VIEW
# ============================================================================
if permissions.is_student():
    student = permissions.get_current_student_profile()
    if not student:
        st.info("No student profile linked.")
        st.stop()

    stu_id = student["id"]
    stu_code = student["student_id"]

    ui_theme.render_header(
        title="Official Academic Transcripts",
        subtitle=f"Official university evaluation transcripts and attendance statements for {student['full_name']} ({stu_code})",
        badge_text="Verified Record",
        badge_variant="success",
    )

    student_records = database.get_academic_records_detailed(student_internal_id=stu_id)
    transcript_text = report_generator.generate_student_transcript_text(student, student_records)

    st.subheader("Official Performance Transcript")
    st.code(transcript_text, language="text")

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download Official Transcript (.txt)",
            data=transcript_text,
            file_name=f"Transcript_{stu_code}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with c2:
        att_df = attendance_service.get_student_subject_breakdown(stu_id)
        if not att_df.empty:
            att_csv = att_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Attendance Statement (CSV)",
                data=att_csv,
                file_name=f"Attendance_{stu_code}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

# ============================================================================
# PROFESSOR REPORTS & EXPORTS VIEW
# ============================================================================
else:
    ui_theme.render_header(
        title="Reports & Dataset Exports",
        subtitle="Generate official multi-worksheet Excel workbooks, CSV exports, and cohort summaries",
        badge_text="Institutional Reporting",
        badge_variant="primary",
    )

    tab_excel, tab_csv = st.tabs(["Comprehensive Excel Report", "CSV Data Exports"])

    with tab_excel:
        st.subheader("Generate Multi-Worksheet Academic Excel Report")
        st.caption("Includes Executive Summary, Subject Performance, Grade Distribution, and Records sheets.")

        ec1, ec2 = st.columns(2)
        with ec1:
            ex_dept = st.selectbox("Department Filter", ["All"] + DEPARTMENTS, key="rep_ex_dept")
        with ec2:
            ex_sem = st.selectbox("Semester Filter", ["All"] + [str(s) for s in SEMESTERS], key="rep_ex_sem")

        e_dept_val = ex_dept if ex_dept != "All" else None
        e_sem_val = int(ex_sem) if ex_sem != "All" else None

        records_to_export = database.get_academic_records_detailed(department=e_dept_val, semester=e_sem_val)
        students_to_export = database.get_all_students(department=e_dept_val, semester=e_sem_val)

        st.write(f"Cohort includes **{len(records_to_export)}** assessment evaluations across **{len(students_to_export)}** student(s).")

        excel_data = report_generator.generate_excel_academic_report(
            records_to_export,
            students_to_export,
            report_title=f"Campus Performance Report ({ex_dept} - Sem {ex_sem})",
            filter_metadata={"department": ex_dept, "semester": ex_sem},
        )

        st.download_button(
            "Download Formatted Excel Workbook (.xlsx)",
            data=excel_data,
            file_name=f"Academic_Performance_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

    with tab_csv:
        st.subheader("Sanitized CSV Exports")
        st.caption("Export raw relational data tables safely stripped of internal IDs and password hashes.")

        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            raw_stus = database.get_all_students(department=e_dept_val, semester=e_sem_val)
            csv_stu = report_generator.export_dataframe_to_csv(raw_stus)
            st.download_button("Export Enrolled Students (CSV)", data=csv_stu, file_name="students_roster.csv", mime="text/csv", use_container_width=True)

        with c_btn2:
            raw_recs = database.get_academic_records_detailed(department=e_dept_val, semester=e_sem_val)
            csv_rec = report_generator.export_dataframe_to_csv(raw_recs)
            st.download_button("Export Evaluation Records (CSV)", data=csv_rec, file_name="academic_records.csv", mime="text/csv", use_container_width=True)
