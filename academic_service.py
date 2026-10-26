"""
Academic Management Service for Campus Performance Portal.
Coordinates coursework assignments, student submissions, educational study materials,
campus announcements, and student academic performance calculations.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import shutil
import pandas as pd
import database
from validators import calculate_grade
from config import MATERIALS_DIR, ASSIGNMENTS_DIR, SUBMISSIONS_DIR


# ============================================================================
# Student Academic Calculations
# ============================================================================

def get_student_academic_summary(student_id: int, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute comprehensive academic metrics for a single student:
    Enrolled Subjects Count, Average Marks, Highest Score, Lowest Score,
    Cleared Subjects, Failed Subjects, Pending Assignments, New Announcements.
    """
    records = database.get_academic_records_detailed(student_internal_id=student_id, db_path=db_path)
    student = database.get_student_by_id(student_id, db_path=db_path)

    if records.empty:
        # Check enrolled subjects count
        sub_count = 0
        if student:
            subs = database.get_all_subjects(course=student["course"], semester=student["semester"], db_path=db_path)
            sub_count = len(subs)

        return {
            "enrolled_subjects": sub_count,
            "recorded_assessments": 0,
            "average_marks": 0.0,
            "highest_marks": 0.0,
            "lowest_marks": 0.0,
            "cleared_subjects": 0,
            "failed_subjects": 0,
            "pending_assignments": 0,
            "new_announcements": 0,
        }

    total_marks = records["total_marks"]
    avg_marks = round(float(total_marks.mean()), 1)
    highest_marks = round(float(total_marks.max()), 1)
    lowest_marks = round(float(total_marks.min()), 1)
    cleared = int((total_marks >= 40.0).sum())
    failed = len(records) - cleared

    # Count pending assignments
    pending_assignments = 0
    new_announcements = 0
    if student:
        assignments_df = database.get_assignments(
            course=student["course"], semester=student["semester"], db_path=db_path
        )
        for _, assign in assignments_df.iterrows():
            sub = database.get_student_assignment_status(assign["id"], student_id, db_path=db_path)
            if not sub or sub.get("submission_status") == "Pending":
                pending_assignments += 1

        announcements_df = database.get_announcements_for_student(
            student["department"], student["course"], student["semester"], db_path=db_path
        )
        new_announcements = len(announcements_df)

    return {
        "enrolled_subjects": len(records),
        "recorded_assessments": len(records),
        "average_marks": avg_marks,
        "highest_marks": highest_marks,
        "lowest_marks": lowest_marks,
        "cleared_subjects": cleared,
        "failed_subjects": failed,
        "pending_assignments": pending_assignments,
        "new_announcements": new_announcements,
    }


# ============================================================================
# Assignments & Submissions
# ============================================================================

def publish_assignment(
    title: str,
    subject_name: str,
    course: str,
    semester: int,
    due_date: str,
    description: str = "",
    max_marks: float = 10.0,
    uploaded_file=None,
    created_by: Optional[int] = None,
    db_path: Optional[str] = None,
) -> int:
    """Save assignment file and store assignment record in database."""
    attachment_path = None
    if uploaded_file is not None:
        safe_filename = f"assign_{course}_{semester}_{uploaded_file.name}".replace(" ", "_")
        dest_path = ASSIGNMENTS_DIR / safe_filename
        with open(dest_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        attachment_path = str(dest_path)

    return database.create_assignment(
        title=title,
        subject_name=subject_name,
        course=course,
        semester=semester,
        due_date=due_date,
        description=description,
        max_marks=max_marks,
        attachment_path=attachment_path,
        created_by=created_by,
        db_path=db_path,
    )


def record_student_submission(
    assignment_id: int,
    student_id: int,
    submission_text: str = "",
    uploaded_file=None,
    db_path: Optional[str] = None,
) -> int:
    """Store student coursework submission file and record in database."""
    submission_path = None
    if uploaded_file is not None:
        safe_filename = f"sub_{assignment_id}_{student_id}_{uploaded_file.name}".replace(" ", "_")
        dest_path = SUBMISSIONS_DIR / safe_filename
        with open(dest_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        submission_path = str(dest_path)

    return database.submit_assignment(
        assignment_id=assignment_id,
        student_id=student_id,
        submission_text=submission_text,
        submission_path=submission_path,
        db_path=db_path,
    )


# ============================================================================
# Study Materials
# ============================================================================

def upload_study_resource(
    title: str,
    subject_name: str,
    course: str,
    semester: int,
    uploaded_file,
    description: str = "",
    uploaded_by: Optional[int] = None,
    db_path: Optional[str] = None,
) -> int:
    """Safely store an educational resource file on disk and record in database."""
    safe_filename = f"mat_{course}_{semester}_{uploaded_file.name}".replace(" ", "_")
    dest_path = MATERIALS_DIR / safe_filename
    with open(dest_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return database.add_study_material(
        title=title,
        subject_name=subject_name,
        course=course,
        semester=semester,
        file_path=str(dest_path),
        description=description,
        uploaded_by=uploaded_by,
        db_path=db_path,
    )
