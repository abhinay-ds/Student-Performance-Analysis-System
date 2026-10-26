"""
Pytest configuration and shared fixtures.
Creates isolated temporary databases for each test run.
"""

import pytest
import sqlite3
import database


@pytest.fixture
def test_db_path(tmp_path):
    """Provide a path to a temporary isolated SQLite database file."""
    db_file = tmp_path / "test_student_performance.db"
    db_str = str(db_file)
    database.init_db(db_str)
    return db_str


@pytest.fixture
def populated_db(test_db_path):
    """Provide a database pre-populated with realistic students and academic records."""
    # Add Students
    s1_id = database.add_student(
        {
            "student_id": "TEST101",
            "full_name": "Alice Smith",
            "email": "alice@test.edu",
            "department": "Computer Science and Engineering",
            "course": "B.Tech",
            "semester": 4,
            "enrollment_date": "2024-08-01",
        },
        db_path=test_db_path,
    )

    s2_id = database.add_student(
        {
            "student_id": "TEST102",
            "full_name": "Bob Jones",
            "email": "bob@test.edu",
            "department": "Information Technology",
            "course": "B.Tech",
            "semester": 4,
            "enrollment_date": "2024-08-01",
        },
        db_path=test_db_path,
    )

    # Add Academic Records
    database.add_academic_record(
        {
            "student_id": s1_id,
            "subject": "Mathematics",
            "internal_marks": 18.0,
            "assignment_marks": 9.0,
            "exam_marks": 60.0,
            "attendance_percentage": 90.0,
            "exam_date": "2025-05-15",
        },
        db_path=test_db_path,
    )

    database.add_academic_record(
        {
            "student_id": s2_id,
            "subject": "Mathematics",
            "internal_marks": 10.0,
            "assignment_marks": 5.0,
            "exam_marks": 20.0,  # Total 35 -> Fail
            "attendance_percentage": 65.0,  # Below 75% -> Needs support
            "exam_date": "2025-05-15",
        },
        db_path=test_db_path,
    )

    return test_db_path
