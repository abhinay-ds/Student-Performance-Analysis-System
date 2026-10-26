"""
Attendance Management Service for Campus Performance Portal.
Handles class session scheduling, roll call logging, attendance percentage
computations, threshold breach alerts, and class attendance matrices.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import database
from config import ATTENDANCE_SUPPORT_THRESHOLD


def create_lecture_session(
    subject_id: int,
    session_date: str,
    session_label: str = "Regular Lecture",
    created_by: Optional[int] = None,
    db_path: Optional[str] = None,
) -> int:
    """Schedule or record a class attendance session."""
    return database.create_attendance_session(
        subject_id=subject_id,
        session_date=session_date,
        session_label=session_label,
        created_by=created_by,
        db_path=db_path,
    )


def save_session_attendance(
    session_id: int,
    attendance_map: Dict[int, str],
    db_path: Optional[str] = None,
) -> None:
    """
    Save or update attendance for all enrolled students in a session.
    attendance_map: {student_internal_id: 'Present' | 'Absent' | 'Late'}
    """
    database.bulk_record_session_attendance(session_id, attendance_map, db_path=db_path)


def get_student_overall_attendance(student_id: int, db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute cumulative overall attendance for a single student across all subjects.
    Returns: {total_classes, attended_classes, percentage, is_low_attendance}
    """
    summary_df = database.get_student_attendance_summary(student_id, db_path=db_path)
    if summary_df.empty:
        # Fallback to academic_records if attendance sessions haven't been logged yet
        records_df = database.get_academic_records_detailed(student_internal_id=student_id, db_path=db_path)
        if not records_df.empty and "attendance_percentage" in records_df.columns:
            avg_att = round(float(records_df["attendance_percentage"].mean()), 1)
            return {
                "total_classes": len(records_df) * 30,  # Estimated classes
                "attended_classes": int(round((avg_att / 100.0) * (len(records_df) * 30))),
                "percentage": avg_att,
                "is_low_attendance": avg_att < ATTENDANCE_SUPPORT_THRESHOLD,
            }
        return {
            "total_classes": 0,
            "attended_classes": 0,
            "percentage": 0.0,
            "is_low_attendance": False,
        }

    total_classes = int(summary_df["total_sessions"].sum())
    attended_classes = int(summary_df["attended_sessions"].sum()) + int(summary_df["late_sessions"].sum())
    # Weighted: Present=1.0, Late=0.5
    weighted_present = float(summary_df["attended_sessions"].sum()) + (0.5 * float(summary_df["late_sessions"].sum()))
    percentage = round((weighted_present / max(1, total_classes)) * 100.0, 1)

    return {
        "total_classes": total_classes,
        "attended_classes": attended_classes,
        "percentage": percentage,
        "is_low_attendance": percentage < ATTENDANCE_SUPPORT_THRESHOLD and total_classes > 0,
    }


def get_student_subject_breakdown(student_id: int, db_path: Optional[str] = None) -> pd.DataFrame:
    """Retrieve detailed subject-by-subject attendance stats for a student."""
    df = database.get_student_attendance_summary(student_id, db_path=db_path)
    if df.empty:
        # Fallback to academic_records table if no granular sessions exist yet
        records = database.get_academic_records_detailed(student_internal_id=student_id, db_path=db_path)
        if not records.empty:
            fallback_rows = []
            for _, r in records.iterrows():
                att = float(r["attendance_percentage"])
                tot = 30
                att_count = int(round((att / 100.0) * tot))
                fallback_rows.append({
                    "subject_id": r.get("record_id"),
                    "subject_code": r["subject"][:6].upper(),
                    "subject_name": r["subject"],
                    "total_sessions": tot,
                    "attended_sessions": att_count,
                    "late_sessions": 0,
                    "absent_sessions": tot - att_count,
                    "attendance_percentage": att,
                })
            return pd.DataFrame(fallback_rows)
    return df


def get_class_attendance_matrix(subject_id: int, db_path: Optional[str] = None) -> pd.DataFrame:
    """
    Pivot table of student attendance across all sessions for a given subject.
    Columns: Student ID, Full Name, Session Dates (Present/Absent/Late), Total %, Status.
    """
    query = """
        SELECT
            s.student_id,
            s.full_name,
            ses.session_date,
            ar.status
        FROM attendance_records ar
        JOIN attendance_sessions ses ON ar.attendance_session_id = ses.id
        JOIN students s ON ar.student_id = s.id
        WHERE ses.subject_id = ?
        ORDER BY s.student_id, ses.session_date
    """
    conn = database.get_connection(db_path)
    try:
        raw_df = pd.read_sql_query(query, conn, params=[subject_id])
    finally:
        conn.close()

    if raw_df.empty:
        return pd.DataFrame()

    matrix = raw_df.pivot_table(
        index=["student_id", "full_name"],
        columns="session_date",
        values="status",
        aggfunc="first",
    ).reset_index()

    return matrix
