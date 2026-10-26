"""
Tests for Form Input Validation, Grading Calculations, and Dataset File Checking.
"""

import pytest
import pandas as pd
import validators
from config import (
    MAX_INTERNAL_MARKS,
    MAX_ASSIGNMENT_MARKS,
    MAX_EXAM_MARKS,
)


def test_student_field_validators():
    """Verify student fields validate correctly."""
    # Student ID
    assert validators.validate_student_id("STU101")[0] is True
    assert validators.validate_student_id("")[0] is False
    assert validators.validate_student_id("A")[0] is False

    # Name
    assert validators.validate_student_name("Alice Smith")[0] is True
    assert validators.validate_student_name("A")[0] is False
    assert validators.validate_student_name("")[0] is False

    # Email
    assert validators.validate_email("test@college.edu")[0] is True
    assert validators.validate_email("not-an-email")[0] is False
    assert validators.validate_email("user@.com")[0] is False

    # Date
    assert validators.validate_date("2025-05-15")[0] is True
    assert validators.validate_date("15-05-2025")[0] is False
    assert validators.validate_date("invalid-date")[0] is False

    # Semester
    assert validators.validate_semester(4)[0] is True
    assert validators.validate_semester(0)[0] is False
    assert validators.validate_semester(15)[0] is False
    assert validators.validate_semester("invalid")[0] is False


def test_marks_and_attendance_validation():
    """Verify marks range limits and attendance bounds."""
    # Valid marks
    ok, msg, c_int, c_asg, c_ex, tot = validators.validate_marks(15.0, 8.0, 50.0)
    assert ok is True
    assert tot == 73.0

    # Negative marks
    assert validators.validate_marks(-1, 5, 50)[0] is False

    # Exceeding internal limit
    assert validators.validate_marks(MAX_INTERNAL_MARKS + 1, 5, 50)[0] is False

    # Exceeding assignment limit
    assert validators.validate_marks(10, MAX_ASSIGNMENT_MARKS + 1, 50)[0] is False

    # Exceeding exam limit
    assert validators.validate_marks(10, 5, MAX_EXAM_MARKS + 1)[0] is False

    # Attendance
    assert validators.validate_attendance(85.5)[0] is True
    assert validators.validate_attendance(100.0)[0] is True
    assert validators.validate_attendance(0.0)[0] is True
    assert validators.validate_attendance(101.0)[0] is False
    assert validators.validate_attendance(-5.0)[0] is False
    assert validators.validate_attendance("abc")[0] is False


def test_grading_calculations():
    """Verify accurate calculation of grades, pass/fail, and academic support."""
    # 95 -> O (Outstanding)
    grade, gpa, desc = validators.calculate_grade(95.0)
    assert grade == "O"
    assert gpa == 10.0

    # 85 -> A+
    grade, gpa, desc = validators.calculate_grade(85.0)
    assert grade == "A+"
    assert gpa == 9.0

    # 75 -> A
    grade, gpa, desc = validators.calculate_grade(75.0)
    assert grade == "A"
    assert gpa == 8.0

    # 45 -> C (Pass)
    grade, gpa, desc = validators.calculate_grade(45.0)
    assert grade == "C"

    # 35 -> F (Fail)
    grade, gpa, desc = validators.calculate_grade(35.0)
    assert grade == "F"

    # Pass / Fail check
    assert validators.is_passing(40.0) is True
    assert validators.is_passing(39.9) is False

    # Academic support needed
    assert validators.is_academic_support_needed(35.0, 90.0) is True  # Low marks
    assert validators.is_academic_support_needed(80.0, 60.0) is True  # Low attendance
    assert validators.is_academic_support_needed(80.0, 85.0) is False  # Good standing


def test_validate_students_dataframe():
    """Test batch DataFrame validation for students import."""
    df_valid = pd.DataFrame([
        {
            "student_id": "STU1",
            "full_name": "Test One",
            "email": "t1@college.edu",
            "department": "CSE",
            "course": "B.Tech",
            "semester": 1,
            "enrollment_date": "2024-08-01",
        },
        {
            "student_id": "STU2",
            "full_name": "Test Two",
            "email": "invalid-email",  # Invalid
            "department": "IT",
            "course": "B.Tech",
            "semester": 1,
            "enrollment_date": "2024-08-01",
        },
    ])

    valid, rejected = validators.validate_students_dataframe(df_valid)
    assert len(valid) == 1
    assert len(rejected) == 1
    assert "email" in rejected[0]["rejection_reason"].lower()


def test_missing_required_columns_raises_error():
    """Test that missing required columns raise descriptive ValueError."""
    bad_df = pd.DataFrame([{"student_id": "STU1"}])
    with pytest.raises(ValueError) as excinfo:
        validators.validate_students_dataframe(bad_df)
    assert "missing required columns" in str(excinfo.value).lower()
