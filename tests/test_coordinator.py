"""
Tests for Coordinator Administration, Subject Integrity, Attendance/Marks Corrections,
System Settings, and Audit Trail Logging.
"""

import pytest
import database
import permissions
import auth
from config import ROLE_COORDINATOR, ROLE_ADMIN, ROLE_STUDENT


def test_coordinator_role_permissions(test_db_path, monkeypatch):
    """Verify coordinator role checks and universal subject scope."""
    # Authenticate as coordinator
    monkeypatch.setattr(permissions, "is_authenticated", lambda: True)
    monkeypatch.setattr(permissions, "get_current_role", lambda: ROLE_COORDINATOR)

    assert permissions.is_coordinator() is True
    assert permissions.is_professor() is True
    assert permissions.is_student() is False

    # Universal subject access for coordinator
    auth_subjs = permissions.get_professor_authorized_subjects()
    assert len(auth_subjs) > 0


def test_subject_management_and_cascading_rename(test_db_path):
    """
    Verify creating, renaming, and archiving subjects.
    Renaming a subject must cascade to historical academic records without data loss.
    """
    # 1. Create a subject
    sid = database.create_subject(
        subject_code="TEST101",
        subject_name="Original Computing",
        department="Computer Science and Engineering",
        course="B.Tech",
        semester=3,
        credits=4,
        description="Initial test syllabus",
        db_path=test_db_path,
    )
    assert sid > 0

    # 2. Add student and academic record linked to this subject
    stu_id = database.add_student({
        "student_id": "STU9901",
        "full_name": "Test Student",
        "email": "test@example.com",
        "department": "Computer Science and Engineering",
        "course": "B.Tech",
        "semester": 3,
        "enrollment_date": "2024-08-01",
    }, db_path=test_db_path)

    rec_id = database.add_academic_record({
        "student_id": stu_id,
        "subject": "Original Computing",
        "subject_id": sid,
        "internal_marks": 15.0,
        "assignment_marks": 8.0,
        "exam_marks": 50.0,
        "exam_date": "2025-01-20",
    }, db_path=test_db_path)

    # 3. Rename subject to "Advanced Computing Systems"
    actor = {"id": 1, "username": "coordinator", "role": "coordinator"}
    ok = database.update_subject(
        subject_id=sid,
        subject_code="TEST101",
        subject_name="Advanced Computing Systems",
        department="Computer Science and Engineering",
        course="B.Tech",
        semester=3,
        credits=4,
        description="Updated syllabus",
        is_active=1,
        updated_by_user=actor,
        reason="Curriculum revision approved by board",
        db_path=test_db_path,
    )
    assert ok is True

    # 4. Verify subject name updated in subjects table
    s_row = database.get_subject_by_id(sid, db_path=test_db_path)
    assert s_row["subject_name"] == "Advanced Computing Systems"

    # 5. Verify academic record cascaded to new name and preserved historical marks
    recs = database.get_academic_records_detailed(subject="Advanced Computing Systems", db_path=test_db_path)
    assert len(recs) == 1
    assert recs.iloc[0]["record_id"] == rec_id
    assert recs.iloc[0]["internal_marks"] == 15.0

    # 6. Verify audit trail entry was recorded
    audits = database.get_audit_logs(limit=10, action_filter="UPDATE_SUBJECT", db_path=test_db_path)
    assert len(audits) >= 1
    assert "Advanced Computing Systems" in audits.iloc[0]["new_values"]


def test_attendance_correction_with_audit_trail(test_db_path):
    """Verify correcting attendance requires a reason and creates an audit entry."""
    # Add student & session
    stu_id = database.add_student({
        "student_id": "STU9902",
        "full_name": "Roll Call Test",
        "email": "roll@example.com",
        "department": "Computer Science and Engineering",
        "course": "B.Tech",
        "semester": 3,
        "enrollment_date": "2024-08-01",
    }, db_path=test_db_path)

    sub_id = database.add_subject("ATT101", "Attendance Subject", "CSE", "B.Tech", 3, db_path=test_db_path)
    sess_id = database.create_attendance_session(sub_id, "2025-02-01", "Lecture 1", db_path=test_db_path)

    # Initial attendance: Absent
    database.record_student_attendance(sess_id, stu_id, status="Absent", db_path=test_db_path)

    # Empty reason must raise ValueError
    with pytest.raises(ValueError):
        database.correct_student_attendance(sess_id, stu_id, new_status="Present", reason="", db_path=test_db_path)

    # Valid correction
    actor = {"id": 1, "username": "coordinator", "role": "coordinator"}
    ok = database.correct_student_attendance(
        session_id=sess_id,
        student_id=stu_id,
        new_status="Present",
        reason="Medical slip provided for authorized absence",
        actor_user=actor,
        db_path=test_db_path,
    )
    assert ok is True

    # Verify updated status
    with database.get_db(test_db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT status FROM attendance_records WHERE attendance_session_id = ? AND student_id = ?", (sess_id, stu_id))
        row = c.fetchone()
        assert row["status"] == "Present"

    # Verify audit log
    logs = database.get_audit_logs(limit=5, action_filter="CORRECT_ATTENDANCE", db_path=test_db_path)
    assert len(logs) == 1
    assert logs.iloc[0]["old_values"] == "status: Absent"
    assert logs.iloc[0]["new_values"] == "status: Present"
    assert "Medical slip" in logs.iloc[0]["reason"]


def test_marks_correction_and_recalculation(test_db_path):
    """Verify marks correction recalculates grade and writes to audit log."""
    stu_id = database.add_student({
        "student_id": "STU9903",
        "full_name": "Marks Test",
        "email": "marks@example.com",
        "department": "Computer Science and Engineering",
        "course": "B.Tech",
        "semester": 3,
        "enrollment_date": "2024-08-01",
    }, db_path=test_db_path)

    rec_id = database.add_academic_record({
        "student_id": stu_id,
        "subject": "Mathematics",
        "internal_marks": 10.0,
        "assignment_marks": 5.0,
        "exam_marks": 20.0,
        "exam_date": "2025-03-01",
    }, db_path=test_db_path)

    actor = {"id": 1, "username": "coordinator", "role": "coordinator"}
    ok = database.correct_academic_record(
        record_id=rec_id,
        internal_marks=18.0,
        assignment_marks=9.0,
        exam_marks=60.0,
        maximum_marks=100.0,
        reason="Re-evaluation score confirmed by department head",
        actor_user=actor,
        db_path=test_db_path,
    )
    assert ok is True

    # Verify recalculation
    recs = database.get_academic_records_detailed(db_path=test_db_path)
    target = recs[recs["record_id"] == rec_id].iloc[0]
    assert target["internal_marks"] == 18.0
    assert target["total_marks"] == 87.0
    assert target["grade"] == "A+"  # 87% is A+ on 10-point scale

    # Verify audit trail
    audits = database.get_audit_logs(limit=5, action_filter="CORRECT_MARKS", db_path=test_db_path)
    assert len(audits) >= 1
    assert "Re-evaluation score" in audits.iloc[0]["reason"]


def test_system_settings_persistence(test_db_path):
    """Verify system settings key-value persistence and type conversion."""
    database.set_system_setting("minimum_attendance_threshold", 80.0, data_type="float", db_path=test_db_path)
    database.set_system_setting("institution_name", "Global Institute of Tech", data_type="string", db_path=test_db_path)

    val_float = database.get_system_setting("minimum_attendance_threshold", db_path=test_db_path)
    assert val_float == 80.0
    assert isinstance(val_float, float)

    val_str = database.get_system_setting("institution_name", db_path=test_db_path)
    assert val_str == "Global Institute of Tech"


def test_professor_subject_allocation(test_db_path):
    """Verify assigning and unassigning faculty to subjects."""
    pwd = auth.hash_password("Prof123!")
    uid = database.create_user("prof_test", pwd, role="professor", db_path=test_db_path)
    sid = database.add_subject("TEST201", "Automata Theory", "CSE", "B.Tech", 4, db_path=test_db_path)

    # Assign
    database.assign_professor_to_subject(uid, sid, academic_year="2024-2025", db_path=test_db_path)
    subjs = database.get_professor_assigned_subjects(uid, db_path=test_db_path)
    assert "Automata Theory" in subjs

    # Remove
    database.remove_professor_from_subject(uid, sid, academic_year="2024-2025", db_path=test_db_path)
    subjs_after = database.get_professor_assigned_subjects(uid, db_path=test_db_path)
    assert "Automata Theory" not in subjs_after
