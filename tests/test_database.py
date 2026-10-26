"""
Tests for SQLite Database Initialization, Foreign Keys, CRUD, and Transactions.
"""

import sqlite3
import pytest
import database


def test_database_initialization_and_persistence(test_db_path):
    """Verify tables exist and persist across new connections."""
    conn = database.get_connection(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    assert "users" in tables
    assert "students" in tables
    assert "academic_records" in tables


def test_student_crud_operations(test_db_path):
    """Test inserting, retrieving, updating, and searching students."""
    # Insert
    s_id = database.add_student(
        {
            "student_id": "STU001",
            "full_name": "John Doe",
            "email": "john@college.edu",
            "department": "Computer Science and Engineering",
            "course": "B.Tech",
            "semester": 2,
            "enrollment_date": "2024-08-01",
        },
        db_path=test_db_path,
    )
    assert s_id > 0

    # Retrieve by ID
    student = database.get_student_by_id(s_id, db_path=test_db_path)
    assert student is not None
    assert student["student_id"] == "STU001"
    assert student["full_name"] == "John Doe"

    # Retrieve by student_id
    student_by_code = database.get_student_by_student_id("STU001", db_path=test_db_path)
    assert student_by_code is not None
    assert student_by_code["id"] == s_id

    # Update
    updated = database.update_student(
        s_id,
        {
            "student_id": "STU001",
            "full_name": "John Updated",
            "email": "john.updated@college.edu",
            "department": "Computer Science and Engineering",
            "course": "B.Tech",
            "semester": 3,
            "enrollment_date": "2024-08-01",
        },
        db_path=test_db_path,
    )
    assert updated is True

    check_student = database.get_student_by_id(s_id, db_path=test_db_path)
    assert check_student["full_name"] == "John Updated"
    assert check_student["semester"] == 3


def test_duplicate_student_id_prevention(test_db_path):
    """Ensure duplicate student IDs raise an integrity error."""
    payload = {
        "student_id": "DUP001",
        "full_name": "Student A",
        "email": "a@college.edu",
        "department": "Mechanical Engineering",
        "course": "B.Tech",
        "semester": 1,
        "enrollment_date": "2024-08-01",
    }
    database.add_student(payload, db_path=test_db_path)

    with pytest.raises(sqlite3.IntegrityError):
        database.add_student(payload, db_path=test_db_path)


def test_student_deletion_policy(test_db_path):
    """Test deletion with foreign key safety check and cascade handling."""
    s_id = database.add_student(
        {
            "student_id": "DEL001",
            "full_name": "Delete Target",
            "email": "del@college.edu",
            "department": "Civil Engineering",
            "course": "B.Tech",
            "semester": 1,
            "enrollment_date": "2024-08-01",
        },
        db_path=test_db_path,
    )

    database.add_academic_record(
        {
            "student_id": s_id,
            "subject": "Surveying",
            "internal_marks": 15.0,
            "assignment_marks": 8.0,
            "exam_marks": 50.0,
            "attendance_percentage": 80.0,
            "exam_date": "2025-05-10",
        },
        db_path=test_db_path,
    )

    # Attempt delete without cascade should fail
    success, msg = database.delete_student(s_id, cascade=False, db_path=test_db_path)
    assert success is False
    assert "associated" in msg.lower() or "exist" in msg.lower()

    # Attempt delete with cascade should succeed and remove both student and academic record
    success_cascade, msg_cascade = database.delete_student(s_id, cascade=True, db_path=test_db_path)
    assert success_cascade is True
    assert database.get_student_by_id(s_id, db_path=test_db_path) is None
    assert database.count_student_academic_records(s_id, db_path=test_db_path) == 0


def test_duplicate_academic_record_prevention(test_db_path):
    """Prevent duplicate evaluation record for same student, subject, and exam_date."""
    s_id = database.add_student(
        {
            "student_id": "ACAD001",
            "full_name": "Acad Student",
            "email": "acad@college.edu",
            "department": "Electrical Engineering",
            "course": "B.Tech",
            "semester": 2,
            "enrollment_date": "2024-08-01",
        },
        db_path=test_db_path,
    )

    record_data = {
        "student_id": s_id,
        "subject": "Circuit Theory",
        "internal_marks": 17.0,
        "assignment_marks": 8.5,
        "exam_marks": 55.0,
        "attendance_percentage": 88.0,
        "exam_date": "2025-05-20",
    }
    database.add_academic_record(record_data, db_path=test_db_path)

    # Attempt inserting identical subject and exam_date for same student
    with pytest.raises(sqlite3.IntegrityError):
        database.add_academic_record(record_data, db_path=test_db_path)


def test_bulk_insert_students_and_rollback(test_db_path):
    """Test bulk student insert handles duplicates safely."""
    students = [
        {
            "student_id": "BULK1",
            "full_name": "Student Bulk 1",
            "email": "b1@college.edu",
            "department": "IT",
            "course": "B.Tech",
            "semester": 1,
            "enrollment_date": "2024-08-01",
        },
        {
            "student_id": "BULK1",  # duplicate ID
            "full_name": "Student Bulk Duplicate",
            "email": "bdup@college.edu",
            "department": "IT",
            "course": "B.Tech",
            "semester": 1,
            "enrollment_date": "2024-08-01",
        },
    ]

    success_n, rejected = database.bulk_insert_students(students, db_path=test_db_path)
    assert success_n == 1
    assert len(rejected) == 1
    assert "already exists" in rejected[0]["rejection_reason"]
