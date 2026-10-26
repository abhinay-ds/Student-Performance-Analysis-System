"""
Tests for Dataset Uploads, Bulk File Ingestion, and Schema Validations.
"""

import pytest
import pandas as pd
import database
import upload_service
import validators


def test_attendance_csv_validation():
    """Verify validation of uploaded attendance DataFrame."""
    df_valid = pd.DataFrame([
        {
            "student_id": "STU101",
            "subject_code": "CS401",
            "session_date": "2025-05-15",
            "session_label": "Lecture 1",
            "status": "Present",
        },
        {
            "student_id": "STU102",
            "subject_code": "CS401",
            "session_date": "2025-05-15",
            "session_label": "Lecture 1",
            "status": "InvalidStatus",  # Rejected
        },
    ])

    valid_rows, rejected_rows = upload_service.validate_attendance_dataframe(df_valid)
    assert len(valid_rows) == 1
    assert len(rejected_rows) == 1
    assert "status" in rejected_rows[0]["rejection_reason"].lower()


def test_attendance_missing_columns_raises_error():
    """Verify missing required columns raise ValueError."""
    bad_df = pd.DataFrame([{"student_id": "STU101"}])
    with pytest.raises(ValueError) as exc:
        upload_service.validate_attendance_dataframe(bad_df)
    assert "missing required columns" in str(exc.value).lower()


def test_bulk_attendance_database_import(test_db_path):
    """Test inserting validated attendance records into SQLite."""
    # Setup student and subject
    database.add_subject("CS401", "DBMS", "CSE", "B.Tech", 4, db_path=test_db_path)
    database.add_student(
        {
            "student_id": "STU101",
            "full_name": "Test Student",
            "email": "test@test.edu",
            "department": "CSE",
            "course": "B.Tech",
            "semester": 4,
            "enrollment_date": "2024-08-01",
        },
        db_path=test_db_path,
    )

    records = [
        {
            "student_id": "STU101",
            "subject_code": "CS401",
            "session_date": "2025-05-01",
            "session_label": "Lecture 1",
            "status": "Present",
        },
        {
            "student_id": "NON_EXISTENT",
            "subject_code": "CS401",
            "session_date": "2025-05-01",
            "session_label": "Lecture 1",
            "status": "Present",
        },
    ]

    success_n, rejected = database.bulk_insert_attendance_records(records, db_path=test_db_path)
    assert success_n == 1
    assert len(rejected) == 1
    assert "not found" in rejected[0]["rejection_reason"].lower()
