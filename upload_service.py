"""
Dataset Upload & Ingestion Service for Campus Performance Portal.
Coordinates CSV/Excel validation, transaction rollback, rejection reporting,
and sample template generation for students, marks, and attendance.
"""

from io import BytesIO
from typing import Dict, Any, List, Tuple
import pandas as pd
import database
import validators
from config import SAMPLE_DATA_DIR


REQUIRED_ATTENDANCE_COLUMNS = ["student_id", "subject_code", "session_date", "session_label", "status"]


def validate_attendance_dataframe(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Validate an uploaded attendance DataFrame."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_ATTENDANCE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Uploaded attendance file is missing required columns: {', '.join(missing)}")

    valid_records = []
    rejected_records = []

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        row_num = idx + 2
        reasons = []

        s_id = str(row_dict.get("student_id", "")).strip().upper()
        ok, msg = validators.validate_student_id(s_id)
        if not ok:
            reasons.append(msg)

        sub_code = str(row_dict.get("subject_code", "")).strip().upper()
        if not sub_code:
            reasons.append("Subject code cannot be blank.")

        s_date = str(row_dict.get("session_date", "")).strip()
        ok, msg = validators.validate_date(s_date)
        if not ok:
            reasons.append(msg)

        status = str(row_dict.get("status", "")).strip().capitalize()
        if status not in ["Present", "Absent", "Late"]:
            reasons.append("Status must be 'Present', 'Absent', or 'Late'.")

        if reasons:
            row_dict["row_number"] = row_num
            row_dict["rejection_reason"] = " | ".join(reasons)
            rejected_records.append(row_dict)
        else:
            valid_records.append({
                "student_id": s_id,
                "subject_code": sub_code,
                "session_date": s_date[:10],
                "session_label": str(row_dict.get("session_label", "Regular Lecture")).strip(),
                "status": status,
            })

    return valid_records, rejected_records


def generate_attendance_template_csv() -> bytes:
    """Generate empty sample CSV for attendance batch upload."""
    sample_df = pd.DataFrame([
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
            "status": "Absent",
        },
    ])
    return sample_df.to_csv(index=False).encode("utf-8")
