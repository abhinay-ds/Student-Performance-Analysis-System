"""
Tests for Report Generation, CSV Sanitization, and Excel Workbook Generation.
"""

import pytest
import pandas as pd
from openpyxl import load_workbook
from io import BytesIO
import report_generator
import database


def test_csv_export_sanitizes_sensitive_columns():
    """Ensure CSV export removes internal IDs and password hashes."""
    df = pd.DataFrame([
        {
            "student_id": "STU1",
            "full_name": "Test",
            "password_hash": "secret_hash",
            "internal_student_id": 999,
            "department": "CSE",
        }
    ])

    csv_bytes = report_generator.export_dataframe_to_csv(df)
    csv_text = csv_bytes.decode("utf-8")

    assert "password_hash" not in csv_text
    assert "secret_hash" not in csv_text
    assert "internal_student_id" not in csv_text
    assert "student_id" in csv_text


def test_excel_academic_report_generation(populated_db):
    """Verify generated Excel file has expected worksheets and styles."""
    students = database.get_all_students(db_path=populated_db)
    records = database.get_academic_records_detailed(db_path=populated_db)

    excel_bytes = report_generator.generate_excel_academic_report(
        records, students, report_title="Test Academic Report"
    )

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0

    wb = load_workbook(BytesIO(excel_bytes))
    sheet_names = wb.sheetnames

    assert "Executive Summary" in sheet_names
    assert "Subject Breakdown" in sheet_names
    assert "Grade Distribution" in sheet_names
    assert "Academic Records" in sheet_names


def test_student_transcript_generation(populated_db):
    """Verify individual student transcript text format."""
    student = database.get_student_by_student_id("TEST101", db_path=populated_db)
    records = database.get_academic_records_detailed(student_id_str="TEST101", db_path=populated_db)

    transcript = report_generator.generate_student_transcript_text(student, records)

    assert "OFFICIAL STUDENT PERFORMANCE TRANSCRIPT REPORT" in transcript
    assert "TEST101" in transcript
    assert "Alice Smith" in transcript
    assert "Mathematics" in transcript
    assert "Summary Statistics" in transcript
