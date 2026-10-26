"""
Data Validation and Sanitization Module for Student Performance Analysis System.
Validates student demographics, academic scores, CSV/Excel schema, and provides
standardized grading calculations based on configurable rules.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
from config import (
    MAX_INTERNAL_MARKS,
    MAX_ASSIGNMENT_MARKS,
    MAX_EXAM_MARKS,
    MAX_TOTAL_MARKS,
    PASS_MARK_THRESHOLD,
    ATTENDANCE_SUPPORT_THRESHOLD,
    SUPPORT_NEEDED_SCORE_THRESHOLD,
    GRADE_RULES,
)

# Standard regex for email address validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
STUDENT_ID_REGEX = re.compile(r"^[A-Za-z0-9\-_]{2,20}$")

REQUIRED_STUDENT_COLUMNS = [
    "student_id",
    "full_name",
    "email",
    "department",
    "course",
    "semester",
    "enrollment_date",
]

REQUIRED_ACADEMIC_COLUMNS = [
    "student_id",
    "subject",
    "internal_marks",
    "assignment_marks",
    "exam_marks",
    "attendance_percentage",
    "exam_date",
]


# ============================================================================
# Field-Level Validators
# ============================================================================

def validate_student_id(student_id: str) -> Tuple[bool, str]:
    """Validate format and presence of student institutional ID."""
    s_id = (student_id or "").strip()
    if not s_id:
        return False, "Student ID is required."
    if not STUDENT_ID_REGEX.match(s_id):
        return False, "Student ID must be 2-20 alphanumeric characters (hyphens and underscores allowed)."
    return True, ""


def validate_student_name(full_name: str) -> Tuple[bool, str]:
    """Validate student full name."""
    name = (full_name or "").strip()
    if not name:
        return False, "Full Name is required."
    if len(name) < 2:
        return False, "Name must be at least 2 characters long."
    if len(name) > 100:
        return False, "Name cannot exceed 100 characters."
    if not re.match(r"^[a-zA-Z\s\.\'-]+$", name):
        return False, "Name should contain only alphabets, spaces, and standard punctuation (. - ')."
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email address format."""
    email_str = (email or "").strip()
    if not email_str:
        return False, "Email address is required."
    if not EMAIL_REGEX.match(email_str):
        return False, "Please enter a valid email address (e.g., student@college.edu)."
    return True, ""


def validate_date(date_str: str) -> Tuple[bool, str]:
    """Validate date format is YYYY-MM-DD and represents a valid calendar date."""
    d_str = str(date_str or "").strip()
    if not d_str:
        return False, "Date is required."
    try:
        dt = datetime.strptime(d_str[:10], "%Y-%m-%d")
        if dt.year < 1990 or dt.year > 2050:
            return False, "Date year must be between 1990 and 2050."
        return True, ""
    except ValueError:
        return False, "Date must be in YYYY-MM-DD format."


def validate_semester(semester: Any) -> Tuple[bool, str]:
    """Validate semester is an integer between 1 and 12."""
    try:
        sem = int(semester)
        if 1 <= sem <= 12:
            return True, ""
        return False, "Semester must be between 1 and 12."
    except (ValueError, TypeError):
        return False, "Semester must be a valid integer."


def validate_marks(
    internal: Any, assignment: Any, exam: Any
) -> Tuple[bool, str, float, float, float, float]:
    """
    Validate that marks are numeric, non-negative, and within individual maximum limits.
    Returns: (is_valid, error_msg, clean_internal, clean_assignment, clean_exam, total_marks)
    """
    try:
        f_internal = float(internal)
        f_assign = float(assignment)
        f_exam = float(exam)
    except (ValueError, TypeError):
        return False, "Marks must be numeric numbers.", 0.0, 0.0, 0.0, 0.0

    if f_internal < 0 or f_internal > MAX_INTERNAL_MARKS:
        return False, f"Internal marks must be between 0 and {MAX_INTERNAL_MARKS}.", 0.0, 0.0, 0.0, 0.0

    if f_assign < 0 or f_assign > MAX_ASSIGNMENT_MARKS:
        return False, f"Assignment marks must be between 0 and {MAX_ASSIGNMENT_MARKS}.", 0.0, 0.0, 0.0, 0.0

    if f_exam < 0 or f_exam > MAX_EXAM_MARKS:
        return False, f"Exam marks must be between 0 and {MAX_EXAM_MARKS}.", 0.0, 0.0, 0.0, 0.0

    total = round(f_internal + f_assign + f_exam, 2)
    if total > MAX_TOTAL_MARKS:
        return False, f"Total marks ({total}) exceed the maximum permitted ({MAX_TOTAL_MARKS}).", 0.0, 0.0, 0.0, 0.0

    return True, "", f_internal, f_assign, f_exam, total


def validate_attendance(attendance: Any) -> Tuple[bool, str, float]:
    """Validate attendance percentage is between 0.0 and 100.0."""
    try:
        att = float(attendance)
        if 0.0 <= att <= 100.0:
            return True, "", round(att, 2)
        return False, "Attendance percentage must be between 0.0 and 100.0.", 0.0
    except (ValueError, TypeError):
        return False, "Attendance must be a valid numeric percentage.", 0.0


# ============================================================================
# Grading Rules and Academic Status Calculations
# ============================================================================

def calculate_grade(total_marks: float) -> Tuple[str, float, str]:
    """
    Calculate letter grade, grade point, and description using configured rules.
    Returns: (grade_letter, grade_point, description)
    """
    score = float(total_marks)
    for letter, min_score, gpa, desc in GRADE_RULES:
        if score >= min_score:
            return letter, gpa, desc
    return "F", 0.0, "Fail"


def is_passing(total_marks: float) -> bool:
    """Return whether the student passed according to PASS_MARK_THRESHOLD."""
    return float(total_marks) >= PASS_MARK_THRESHOLD


def is_academic_support_needed(total_marks: float, attendance_pct: float) -> bool:
    """
    Student requires academic support if total score < SUPPORT_NEEDED_SCORE_THRESHOLD
    or attendance < ATTENDANCE_SUPPORT_THRESHOLD.
    """
    return (
        float(total_marks) < SUPPORT_NEEDED_SCORE_THRESHOLD
        or float(attendance_pct) < ATTENDANCE_SUPPORT_THRESHOLD
    )


# ============================================================================
# Dataset Bulk Validation
# ============================================================================

def validate_students_dataframe(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate an uploaded students DataFrame.
    Returns: (valid_records, rejected_records_with_reasons)
    """
    # Normalize column names: lowercase, stripped
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing_cols = [c for c in REQUIRED_STUDENT_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Uploaded file is missing required columns: {', '.join(missing_cols)}")

    valid_records: List[Dict[str, Any]] = []
    rejected_records: List[Dict[str, Any]] = []
    seen_ids = set()

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        row_num = idx + 2  # Excel/CSV 1-based header offset
        reasons = []

        # Student ID
        s_id = str(row_dict.get("student_id", "")).strip().upper()
        ok, msg = validate_student_id(s_id)
        if not ok:
            reasons.append(msg)
        elif s_id in seen_ids:
            reasons.append(f"Duplicate student_id '{s_id}' within upload file.")
        else:
            seen_ids.add(s_id)

        # Name
        name = str(row_dict.get("full_name", "")).strip()
        ok, msg = validate_student_name(name)
        if not ok:
            reasons.append(msg)

        # Email
        email = str(row_dict.get("email", "")).strip()
        ok, msg = validate_email(email)
        if not ok:
            reasons.append(msg)

        # Department & Course
        dept = str(row_dict.get("department", "")).strip()
        if not dept:
            reasons.append("Department cannot be blank.")

        course = str(row_dict.get("course", "")).strip()
        if not course:
            reasons.append("Course cannot be blank.")

        # Semester
        ok, msg = validate_semester(row_dict.get("semester"))
        if not ok:
            reasons.append(msg)

        # Enrollment Date
        enroll_dt = str(row_dict.get("enrollment_date", "")).strip()
        ok, msg = validate_date(enroll_dt)
        if not ok:
            reasons.append(msg)

        if reasons:
            row_dict["row_number"] = row_num
            row_dict["rejection_reason"] = " | ".join(reasons)
            rejected_records.append(row_dict)
        else:
            valid_records.append({
                "student_id": s_id,
                "full_name": name,
                "email": email.lower(),
                "department": dept,
                "course": course,
                "semester": int(row_dict.get("semester")),
                "enrollment_date": enroll_dt[:10],
            })

    return valid_records, rejected_records


def validate_academic_dataframe(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validate an uploaded academic records DataFrame.
    Returns: (valid_records, rejected_records_with_reasons)
    """
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing_cols = [c for c in REQUIRED_ACADEMIC_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Uploaded file is missing required columns: {', '.join(missing_cols)}")

    valid_records: List[Dict[str, Any]] = []
    rejected_records: List[Dict[str, Any]] = []
    seen_combos = set()

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        row_num = idx + 2
        reasons = []

        # Student ID
        s_id = str(row_dict.get("student_id", "")).strip().upper()
        ok, msg = validate_student_id(s_id)
        if not ok:
            reasons.append(msg)

        # Subject
        subj = str(row_dict.get("subject", "")).strip()
        if not subj:
            reasons.append("Subject cannot be blank.")

        # Exam Date
        exam_dt = str(row_dict.get("exam_date", "")).strip()
        ok, msg = validate_date(exam_dt)
        if not ok:
            reasons.append(msg)
        else:
            exam_dt = exam_dt[:10]

        # Duplicate check within file
        combo = (s_id, subj.lower(), exam_dt)
        if combo in seen_combos:
            reasons.append(f"Duplicate entry for student '{s_id}', subject '{subj}' on '{exam_dt}' in file.")
        else:
            seen_combos.add(combo)

        # Marks validation
        ok, msg, c_int, c_asgn, c_exam, total = validate_marks(
            row_dict.get("internal_marks"),
            row_dict.get("assignment_marks"),
            row_dict.get("exam_marks"),
        )
        if not ok:
            reasons.append(msg)

        # Attendance validation
        ok, msg, c_att = validate_attendance(row_dict.get("attendance_percentage"))
        if not ok:
            reasons.append(msg)

        if reasons:
            row_dict["row_number"] = row_num
            row_dict["rejection_reason"] = " | ".join(reasons)
            rejected_records.append(row_dict)
        else:
            valid_records.append({
                "student_id": s_id,
                "subject": subj,
                "internal_marks": c_int,
                "assignment_marks": c_asgn,
                "exam_marks": c_exam,
                "attendance_percentage": c_att,
                "exam_date": exam_dt,
            })

    return valid_records, rejected_records
