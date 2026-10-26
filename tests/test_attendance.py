"""
Tests for Attendance Management, Calculations, and Threshold Alerts.
"""

import pytest
import sqlite3
import database
import attendance_service


def test_attendance_session_creation_and_roll_call(test_db_path):
    """Test creating sessions and recording attendance."""
    # 1. Add Subject
    sub_id = database.add_subject(
        "CS401", "Database Systems", "Computer Science and Engineering", "B.Tech", 4, db_path=test_db_path
    )

    # 2. Add Student
    stu_id = database.add_student(
        {
            "student_id": "ATT001",
            "full_name": "Attendance Tester",
            "email": "att@college.edu",
            "department": "Computer Science and Engineering",
            "course": "B.Tech",
            "semester": 4,
            "enrollment_date": "2024-08-01",
        },
        db_path=test_db_path,
    )

    # 3. Create 4 Sessions: 3 Present, 1 Absent (75% attendance)
    s1 = attendance_service.create_lecture_session(sub_id, "2025-05-01", "Lecture 1", db_path=test_db_path)
    s2 = attendance_service.create_lecture_session(sub_id, "2025-05-02", "Lecture 2", db_path=test_db_path)
    s3 = attendance_service.create_lecture_session(sub_id, "2025-05-03", "Lecture 3", db_path=test_db_path)
    s4 = attendance_service.create_lecture_session(sub_id, "2025-05-04", "Lecture 4", db_path=test_db_path)

    attendance_service.save_session_attendance(s1, {stu_id: "Present"}, db_path=test_db_path)
    attendance_service.save_session_attendance(s2, {stu_id: "Present"}, db_path=test_db_path)
    attendance_service.save_session_attendance(s3, {stu_id: "Present"}, db_path=test_db_path)
    attendance_service.save_session_attendance(s4, {stu_id: "Absent"}, db_path=test_db_path)

    # 4. Compute Student Overall Attendance
    summary = attendance_service.get_student_overall_attendance(stu_id, db_path=test_db_path)
    assert summary["total_classes"] == 4
    assert summary["attended_classes"] == 3
    assert summary["percentage"] == 75.0
    assert summary["is_low_attendance"] is False


def test_attendance_threshold_breach_flag(test_db_path):
    """Verify warning alert is flagged when attendance falls below 75%."""
    sub_id = database.add_subject("CS402", "Operating Systems", "CSE", "B.Tech", 4, db_path=test_db_path)
    stu_id = database.add_student(
        {
            "student_id": "LOW001",
            "full_name": "Low Attender",
            "email": "low@college.edu",
            "department": "CSE",
            "course": "B.Tech",
            "semester": 4,
            "enrollment_date": "2024-08-01",
        },
        db_path=test_db_path,
    )

    # 1 Present, 2 Absent = 33.3% -> Low
    s1 = attendance_service.create_lecture_session(sub_id, "2025-05-10", "Lecture 1", db_path=test_db_path)
    s2 = attendance_service.create_lecture_session(sub_id, "2025-05-11", "Lecture 2", db_path=test_db_path)
    s3 = attendance_service.create_lecture_session(sub_id, "2025-05-12", "Lecture 3", db_path=test_db_path)

    attendance_service.save_session_attendance(s1, {stu_id: "Present"}, db_path=test_db_path)
    attendance_service.save_session_attendance(s2, {stu_id: "Absent"}, db_path=test_db_path)
    attendance_service.save_session_attendance(s3, {stu_id: "Absent"}, db_path=test_db_path)

    summary = attendance_service.get_student_overall_attendance(stu_id, db_path=test_db_path)
    assert summary["percentage"] < 75.0
    assert summary["is_low_attendance"] is True


def test_duplicate_session_prevention(test_db_path):
    """Ensure duplicate session for same subject, date, and label is rejected."""
    sub_id = database.add_subject("CS403", "Networks", "CSE", "B.Tech", 4, db_path=test_db_path)
    attendance_service.create_lecture_session(sub_id, "2025-05-15", "Lecture 1", db_path=test_db_path)

    with pytest.raises(sqlite3.IntegrityError):
        attendance_service.create_lecture_session(sub_id, "2025-05-15", "Lecture 1", db_path=test_db_path)
