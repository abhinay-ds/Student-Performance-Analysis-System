"""
Tests for Academic Services, Assignments, Study Materials, and Announcements.
"""

import pytest
import database
import academic_service


def test_assignment_lifecycle(test_db_path):
    """Test full workflow: create assignment, submit coursework, and grade submission."""
    # 1. Add Student
    s_id = database.add_student(
        {
            "student_id": "ASG001",
            "full_name": "Assign Student",
            "email": "asg@test.edu",
            "department": "CSE",
            "course": "B.Tech",
            "semester": 4,
            "enrollment_date": "2024-08-01",
        },
        db_path=test_db_path,
    )

    # 2. Create Assignment
    a_id = database.create_assignment(
        title="Assignment 1: SQL Joins",
        subject_name="Database Systems",
        course="B.Tech",
        semester=4,
        due_date="2025-06-15",
        description="Write SQL queries for complex multi-table joins.",
        max_marks=10.0,
        db_path=test_db_path,
    )
    assert a_id > 0

    # 3. Retrieve Assignments for Cohort
    assigns = database.get_assignments(course="B.Tech", semester=4, db_path=test_db_path)
    assert len(assigns) == 1
    assert assigns.iloc[0]["title"] == "Assignment 1: SQL Joins"

    # 4. Student Submits Assignment
    sub_id = database.submit_assignment(
        assignment_id=a_id,
        student_id=s_id,
        submission_text="SELECT * FROM students s JOIN marks m ON s.id = m.student_id;",
        db_path=test_db_path,
    )
    assert sub_id > 0

    sub_status = database.get_student_assignment_status(a_id, s_id, db_path=test_db_path)
    assert sub_status is not None
    assert sub_status["submission_status"] == "Submitted"

    # 5. Professor Grades Submission
    graded = database.grade_assignment_submission(
        submission_id=sub_status["id"],
        marks_awarded=9.5,
        feedback="Excellent query formulation.",
        db_path=test_db_path,
    )
    assert graded is True

    updated_sub = database.get_student_assignment_status(a_id, s_id, db_path=test_db_path)
    assert updated_sub["submission_status"] == "Graded"
    assert updated_sub["marks_awarded"] == 9.5
    assert updated_sub["feedback"] == "Excellent query formulation."


def test_study_materials_and_announcements(test_db_path):
    """Test study material upload and targeted announcement distribution."""
    # 1. Add Study Material
    mat_id = database.add_study_material(
        title="Unit 1 Lecture Notes",
        subject_name="Operating Systems",
        course="B.Tech",
        semester=4,
        file_path="uploads/materials/sample_note.pdf",
        description="Paging & Virtual Memory lecture slides.",
        db_path=test_db_path,
    )
    assert mat_id > 0

    mats = database.get_study_materials(course="B.Tech", semester=4, db_path=test_db_path)
    assert len(mats) == 1
    assert mats.iloc[0]["title"] == "Unit 1 Lecture Notes"

    # 2. Add Announcement
    ann_id = database.add_announcement(
        title="Midterm Exams Schedule",
        message="Exams commence on May 15.",
        department="Computer Science and Engineering",
        course="B.Tech",
        semester=4,
        db_path=test_db_path,
    )
    assert ann_id > 0

    # Student from CSE Sem 4 receives the announcement
    ann_student = database.get_announcements_for_student(
        department="Computer Science and Engineering",
        course="B.Tech",
        semester=4,
        db_path=test_db_path,
    )
    assert len(ann_student) == 1
    assert ann_student.iloc[0]["title"] == "Midterm Exams Schedule"

    # Student from Civil Sem 2 should not receive it
    ann_civil = database.get_announcements_for_student(
        department="Civil Engineering",
        course="B.Tech",
        semester=2,
        db_path=test_db_path,
    )
    assert len(ann_civil) == 0
