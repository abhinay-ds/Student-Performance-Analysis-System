"""
Page 10: Dataset Upload and Batch Data Ingestion (Professor / Administrator Portal).
Supports bulk CSV and Excel imports for Students, Academic Marks, and Attendance.
Performs pre-validation, atomic transactional ingestion, and rejection reporting.
"""

from io import BytesIO
import streamlit as st
import pandas as pd
import database
import auth
import permissions
import validators
import upload_service
import ui_theme
from config import SAMPLE_DATA_DIR

auth.init_session_state()
ui_theme.inject_global_theme()
permissions.render_demo_banner()
auth.render_sidebar_user_info()

permissions.require_role(["professor", "admin"])

ui_theme.render_header(
    title="Dataset Upload & Batch Ingestion",
    subtitle="Import bulk student demographics, academic evaluations, or attendance logs from CSV or Excel files",
    badge_text="Batch Operations",
    badge_variant="primary",
)

# Template Downloads
with st.expander("Download Sample CSV Templates & Schemas", expanded=False):
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("**Student Directory Template**")
        st.caption("Schema: `student_id, full_name, email, department, course, semester, enrollment_date`")
        try:
            with open(SAMPLE_DATA_DIR / "students_template.csv", "rb") as f:
                st.download_button("Download Student CSV Template", data=f.read(), file_name="student_template.csv", mime="text/csv")
        except Exception:
            pass

    with t2:
        st.markdown("**Academic Marks Template**")
        st.caption("Schema: `student_id, subject, internal_marks, assignment_marks, exam_marks, attendance_percentage, exam_date`")
        try:
            with open(SAMPLE_DATA_DIR / "academic_records_template.csv", "rb") as f:
                st.download_button("Download Marks CSV Template", data=f.read(), file_name="marks_template.csv", mime="text/csv")
        except Exception:
            pass

    with t3:
        st.markdown("**Attendance Records Template**")
        st.caption("Schema: `student_id, subject_code, session_date, session_label, status`")
        att_bytes = upload_service.generate_attendance_template_csv()
        st.download_button("Download Attendance CSV Template", data=att_bytes, file_name="attendance_template.csv", mime="text/csv")

st.write("")

import_target = st.radio(
    "Select Target Ingestion Dataset:",
    ["Student Demographics Dataset", "Academic Marks Dataset", "Attendance Sessions Dataset"],
    horizontal=True,
)

uploaded_file = st.file_uploader(f"Upload {import_target} (.csv or .xlsx)", type=["csv", "xlsx"])

if uploaded_file is not None:
    fbytes = uploaded_file.getvalue()
    fname = uploaded_file.name.lower()

    try:
        if fname.endswith(".xlsx"):
            raw_df = pd.read_excel(BytesIO(fbytes), engine="openpyxl")
        else:
            raw_df = pd.read_csv(BytesIO(fbytes))
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        st.stop()

    st.subheader("Upload File Diagnostics")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Total Rows", len(raw_df))
    d2.metric("Total Columns", len(raw_df.columns))
    d3.metric("Missing Values", int(raw_df.isna().sum().sum()))
    d4.metric("Duplicate Rows", int(raw_df.duplicated().sum()))

    # Validation Phase
    st.subheader("Pre-Import Validation")
    try:
        if import_target == "Student Demographics Dataset":
            valid_rows, rejected_rows = validators.validate_students_dataframe(raw_df)
        elif import_target == "Academic Marks Dataset":
            valid_rows, rejected_rows = validators.validate_academic_dataframe(raw_df)
        else:
            valid_rows, rejected_rows = upload_service.validate_attendance_dataframe(raw_df)
    except ValueError as ve:
        st.error(f"Schema Error: {ve}")
        st.stop()

    v1, v2 = st.columns(2)
    v1.success(f"Valid Records: **{len(valid_rows)}**")
    if rejected_rows:
        v2.error(f"Rejected Records: **{len(rejected_rows)}**")
        st.warning("The following records contain formatting errors and will NOT be imported:")
        rej_df = pd.DataFrame(rejected_rows)
        st.dataframe(rej_df, use_container_width=True, hide_index=True)
        rej_csv = rej_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Rejected Rows Report (CSV)", data=rej_csv, file_name="rejected_records_report.csv", mime="text/csv")
    else:
        v2.info("Clean dataset: All rows passed validation.")

    if valid_rows:
        with st.expander(f"Preview Valid Records ({len(valid_rows)})", expanded=True):
            st.dataframe(pd.DataFrame(valid_rows), use_container_width=True, hide_index=True)

        if st.button("Confirm & Ingest Records into Database", type="primary"):
            if permissions.prevent_demo_mutation():
                pass
            else:
                with st.spinner("Processing transactional database insertion..."):
                    if import_target == "Student Demographics Dataset":
                        s_count, db_rej = database.bulk_insert_students(valid_rows)
                    elif import_target == "Academic Marks Dataset":
                        s_count, db_rej = database.bulk_insert_academic_records(valid_rows)
                    else:
                        s_count, db_rej = database.bulk_insert_attendance_records(valid_rows)

                if db_rej:
                    st.warning(f"Imported **{s_count}** records. **{len(db_rej)}** rows rejected due to database constraints.")
                    st.dataframe(pd.DataFrame(db_rej), use_container_width=True)
                else:
                    st.success(f"Successfully imported all {s_count} records into the database.")
