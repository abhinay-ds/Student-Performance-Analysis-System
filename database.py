"""
Database Management Module for Student Performance Analysis System.
Handles SQLite schema creation, foreign-key enforcement, migrations,
parameterized queries, and transactions across users, students, professors,
subjects, attendance, marks, assignments, materials, and announcements.
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
import numpy as np

# Register adapters so numpy scalar types from pandas DataFrames seamlessly bind to SQLite
sqlite3.register_adapter(np.int64, int)
sqlite3.register_adapter(np.int32, int)
sqlite3.register_adapter(np.int16, int)
sqlite3.register_adapter(np.int8, int)
sqlite3.register_adapter(np.float64, float)
sqlite3.register_adapter(np.float32, float)

from config import DATABASE_PATH

logger = logging.getLogger(__name__)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Establish and return an SQLite connection with foreign keys enabled
    and dictionary-style row factory.
    """
    path = db_path or DATABASE_PATH
    conn = sqlite3.connect(path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db(db_path: Optional[str] = None):
    """
    Context manager providing a safe transactional database session.
    Commits on clean exit, rolls back on exception.
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction rolled back: {e}")
        raise
    finally:
        conn.close()


def _safe_add_column(cursor: sqlite3.Cursor, table: str, col_def: str) -> None:
    """Safely add a column to an existing table if it does not exist."""
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def};")
    except sqlite3.OperationalError:
        pass  # Column already exists


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initialize full database schema. Creates tables, constraints, indexes,
    and applies non-destructive migrations. Preserves existing data across restarts.
    """
    with get_db(db_path) as conn:
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        _safe_add_column(cursor, "users", "is_active INTEGER NOT NULL DEFAULT 1")

        # 2. Students Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                student_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                department TEXT NOT NULL,
                course TEXT NOT NULL,
                semester INTEGER NOT NULL,
                enrollment_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """
        )
        _safe_add_column(cursor, "students", "user_id INTEGER REFERENCES users(id) ON DELETE SET NULL")

        # 3. Professor Profiles Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS professor_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                department TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )

        # 4. Subjects Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_code TEXT UNIQUE NOT NULL,
                subject_name TEXT NOT NULL,
                department TEXT NOT NULL,
                course TEXT NOT NULL,
                semester INTEGER NOT NULL,
                credits INTEGER NOT NULL DEFAULT 3,
                description TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        _safe_add_column(cursor, "subjects", "credits INTEGER NOT NULL DEFAULT 3")
        _safe_add_column(cursor, "subjects", "description TEXT")
        _safe_add_column(cursor, "subjects", "is_active INTEGER NOT NULL DEFAULT 1")

        # 4a. Departments Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_code TEXT UNIQUE NOT NULL,
                department_name TEXT NOT NULL,
                description TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 4b. Courses Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT UNIQUE NOT NULL,
                course_name TEXT NOT NULL,
                department_name TEXT NOT NULL,
                duration_years INTEGER NOT NULL DEFAULT 4,
                total_semesters INTEGER NOT NULL DEFAULT 8,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 4c. Professor-Subject Assignment Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS professor_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                academic_year TEXT NOT NULL DEFAULT '2024-2025',
                is_assigned INTEGER NOT NULL DEFAULT 1,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                UNIQUE(user_id, subject_id, academic_year)
            );
            """
        )

        # 4d. System Settings Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                data_type TEXT NOT NULL DEFAULT 'string',
                description TEXT,
                updated_by INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
            );
            """
        )

        # 4e. Audit Logs Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT,
                old_values TEXT,
                new_values TEXT,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """
        )

        # 5. Student-Subject Enrollment Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS student_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                academic_year TEXT NOT NULL DEFAULT '2024-2025',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                UNIQUE(student_id, subject_id, academic_year)
            );
            """
        )

        # 6. Attendance Sessions Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                session_date TEXT NOT NULL,
                session_label TEXT NOT NULL DEFAULT 'Regular Lecture',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
                UNIQUE(subject_id, session_date, session_label)
            );
            """
        )

        # 7. Attendance Records Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attendance_session_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Present',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (attendance_session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE(attendance_session_id, student_id)
            );
            """
        )

        # 8. Academic Records Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS academic_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                subject_id INTEGER,
                examination_type TEXT NOT NULL DEFAULT 'End Semester',
                internal_marks REAL NOT NULL DEFAULT 0.0,
                assignment_marks REAL NOT NULL DEFAULT 0.0,
                exam_marks REAL NOT NULL DEFAULT 0.0,
                maximum_marks REAL NOT NULL DEFAULT 100.0,
                attendance_percentage REAL NOT NULL DEFAULT 0.0,
                grade TEXT,
                exam_date TEXT NOT NULL,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE RESTRICT,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
                CONSTRAINT uq_student_subject_date UNIQUE (student_id, subject, exam_date)
            );
            """
        )
        _safe_add_column(cursor, "academic_records", "subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL")
        _safe_add_column(cursor, "academic_records", "examination_type TEXT NOT NULL DEFAULT 'End Semester'")
        _safe_add_column(cursor, "academic_records", "maximum_marks REAL NOT NULL DEFAULT 100.0")
        _safe_add_column(cursor, "academic_records", "grade TEXT")
        _safe_add_column(cursor, "academic_records", "created_by INTEGER REFERENCES users(id) ON DELETE SET NULL")
        _safe_add_column(cursor, "academic_records", "is_approved INTEGER NOT NULL DEFAULT 1")
        _safe_add_column(cursor, "academic_records", "approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL")
        _safe_add_column(cursor, "academic_records", "approval_date TEXT")

        # 9. Assignments Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                subject_id INTEGER,
                subject_name TEXT NOT NULL,
                course TEXT NOT NULL,
                semester INTEGER NOT NULL,
                due_date TEXT NOT NULL,
                max_marks REAL NOT NULL DEFAULT 10.0,
                attachment_path TEXT,
                created_by INTEGER,
                is_published INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            );
            """
        )

        # 10. Assignment Submissions Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS assignment_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                submission_path TEXT,
                submission_text TEXT,
                submission_status TEXT NOT NULL DEFAULT 'Submitted',
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                marks_awarded REAL,
                feedback TEXT,
                FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE(assignment_id, student_id)
            );
            """
        )

        # 11. Study Materials Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS study_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                subject_id INTEGER,
                subject_name TEXT NOT NULL,
                course TEXT NOT NULL,
                semester INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                uploaded_by INTEGER,
                is_published INTEGER NOT NULL DEFAULT 1,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,
                FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
            );
            """
        )

        # 12. Announcements Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                department TEXT NOT NULL DEFAULT 'All',
                course TEXT NOT NULL DEFAULT 'All',
                semester INTEGER NOT NULL DEFAULT 0,
                created_by INTEGER,
                is_published INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            );
            """
        )

        # Performance Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_student_id ON students(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_academic_student_id ON academic_records(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_academic_subject ON academic_records(subject);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_session ON attendance_records(attendance_session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance_records(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assignments_course_sem ON assignments(course, semester);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_course_sem ON study_materials(course, semester);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prof_sub_user ON professor_subjects(user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prof_sub_subject ON professor_subjects(subject_id);")

        # Initialize Default System Settings if empty
        try:
            from config import DEFAULT_SYSTEM_SETTINGS
            for k, (v, dt, desc) in DEFAULT_SYSTEM_SETTINGS.items():
                cursor.execute(
                    """
                    INSERT INTO system_settings (key, value, data_type, description)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(key) DO NOTHING
                    """,
                    (k, v, dt, desc),
                )
        except Exception:
            pass


# ============================================================================
# User Operations
# ============================================================================

def create_user(
    username: str,
    password_hash: str,
    role: str = "student",
    is_active: int = 1,
    db_path: Optional[str] = None,
) -> int:
    """Create a user with hashed password and role."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, is_active) VALUES (?, ?, ?, ?)",
            (username.strip(), password_hash, role.strip(), is_active),
        )
        return cursor.lastrowid


def get_user_by_username(username: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary by username."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, role, is_active, created_at FROM users WHERE username = ?",
            (username.strip(),),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary by primary key."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, is_active, created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def count_users(role: Optional[str] = None, db_path: Optional[str] = None) -> int:
    """Count registered users in database, optionally filtered by role."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        if role:
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = ?", (role,))
        else:
            cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]


# ============================================================================
# Student Operations
# ============================================================================

def add_student(student_data: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """Add a new student profile."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO students (
                user_id, student_id, full_name, email, department, course, semester, enrollment_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_data.get("user_id"),
                str(student_data["student_id"]).strip().upper(),
                student_data["full_name"].strip(),
                student_data["email"].strip().lower(),
                student_data["department"].strip(),
                student_data["course"].strip(),
                int(student_data["semester"]),
                str(student_data["enrollment_date"]).strip(),
            ),
        )
        return cursor.lastrowid


def update_student(internal_id: int, student_data: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """Update existing student details."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE students
            SET student_id = ?,
                full_name = ?,
                email = ?,
                department = ?,
                course = ?,
                semester = ?,
                enrollment_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                str(student_data["student_id"]).strip().upper(),
                student_data["full_name"].strip(),
                student_data["email"].strip().lower(),
                student_data["department"].strip(),
                student_data["course"].strip(),
                int(student_data["semester"]),
                str(student_data["enrollment_date"]).strip(),
                internal_id,
            ),
        )
        return cursor.rowcount > 0


def get_student_by_id(internal_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve single student by primary key."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (internal_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_student_by_student_id(student_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve single student by institutional student_id."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id.strip().upper(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_student_by_user_id(user_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve student linked to a user account ID."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_students(
    search: Optional[str] = None,
    department: Optional[str] = None,
    course: Optional[str] = None,
    semester: Optional[int] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Search and filter students table into a pandas DataFrame."""
    query = "SELECT * FROM students WHERE 1=1"
    params: List[Any] = []

    if search:
        p = f"%{search.strip()}%"
        query += " AND (student_id LIKE ? OR full_name LIKE ? OR email LIKE ?)"
        params.extend([p, p, p])

    if department and department != "All":
        query += " AND department = ?"
        params.append(department.strip())

    if course and course != "All":
        query += " AND course = ?"
        params.append(course.strip())

    if semester and semester != "All":
        query += " AND semester = ?"
        params.append(int(semester))

    query += " ORDER BY full_name ASC"

    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def count_student_academic_records(student_internal_id: int, db_path: Optional[str] = None) -> int:
    """Count academic records for given student."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM academic_records WHERE student_id = ?", (student_internal_id,))
        return cursor.fetchone()[0]


def delete_student(internal_id: int, cascade: bool = False, db_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Safely delete a student. If cascade is False and academic records exist,
    returns an informative error. If cascade is True, cleans up associated data atomically.
    """
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        records_count = count_student_academic_records(internal_id, db_path=db_path)

        if records_count > 0 and not cascade:
            return (
                False,
                f"Cannot delete student because {records_count} academic record(s) exist. Confirm cascade to proceed.",
            )

        if cascade:
            cursor.execute("DELETE FROM academic_records WHERE student_id = ?", (internal_id,))
            cursor.execute("DELETE FROM attendance_records WHERE student_id = ?", (internal_id,))
            cursor.execute("DELETE FROM assignment_submissions WHERE student_id = ?", (internal_id,))
            cursor.execute("DELETE FROM student_subjects WHERE student_id = ?", (internal_id,))

        cursor.execute("DELETE FROM students WHERE id = ?", (internal_id,))
        if cursor.rowcount > 0:
            return True, "Student deleted successfully."
        return False, "Student not found."


# ============================================================================
# Professor Profile Operations
# ============================================================================

def create_professor_profile(
    user_id: int,
    full_name: str,
    email: str,
    department: str,
    db_path: Optional[str] = None,
) -> int:
    """Create professor profile linked to user_id."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO professor_profiles (user_id, full_name, email, department)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, full_name.strip(), email.strip().lower(), department.strip()),
        )
        return cursor.lastrowid


def get_professor_by_user_id(user_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve professor profile linked to user_id."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM professor_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# ============================================================================
# Subject Operations
# ============================================================================

def add_subject(
    subject_code: str,
    subject_name: str,
    department: str,
    course: str,
    semester: int,
    db_path: Optional[str] = None,
) -> int:
    """Register a new academic subject."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO subjects (subject_code, subject_name, department, course, semester)
            VALUES (?, ?, ?, ?, ?)
            """,
            (subject_code.strip().upper(), subject_name.strip(), department.strip(), course.strip(), int(semester)),
        )
        return cursor.lastrowid


def get_all_subjects(
    department: Optional[str] = None,
    course: Optional[str] = None,
    semester: Optional[int] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch subjects DataFrame matching criteria."""
    query = "SELECT * FROM subjects WHERE 1=1"
    params: List[Any] = []

    if department and department != "All":
        query += " AND department = ?"
        params.append(department.strip())

    if course and course != "All":
        query += " AND course = ?"
        params.append(course.strip())

    if semester and semester != "All":
        query += " AND semester = ?"
        params.append(int(semester))

    query += " ORDER BY semester ASC, subject_name ASC"

    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def get_subject_by_id(subject_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch subject row by ID."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# ============================================================================
# Attendance Session & Records Operations
# ============================================================================

def create_attendance_session(
    subject_id: int,
    session_date: str,
    session_label: str = "Lecture",
    created_by: Optional[int] = None,
    db_path: Optional[str] = None,
) -> int:
    """Create an attendance session for a subject and date."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO attendance_sessions (subject_id, session_date, session_label, created_by)
            VALUES (?, ?, ?, ?)
            """,
            (
                int(subject_id),
                str(session_date)[:10],
                session_label.strip(),
                int(created_by) if created_by is not None else None,
            ),
        )
        return cursor.lastrowid


def get_attendance_sessions(
    subject_id: Optional[int] = None,
    date_str: Optional[str] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch attendance sessions joined with subject info."""
    query = """
        SELECT
            s.id AS session_id,
            s.subject_id,
            sub.subject_code,
            sub.subject_name,
            sub.department,
            sub.course,
            sub.semester,
            s.session_date,
            s.session_label,
            s.created_at
        FROM attendance_sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        WHERE 1=1
    """
    params: List[Any] = []
    if subject_id:
        query += " AND s.subject_id = ?"
        params.append(subject_id)
    if date_str and date_str != "All":
        query += " AND s.session_date = ?"
        params.append(date_str)

    query += " ORDER BY s.session_date DESC, sub.subject_name ASC"

    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def record_student_attendance(
    session_id: int,
    student_id: int,
    status: str = "Present",
    db_path: Optional[str] = None,
) -> None:
    """Record or update attendance status for a student in a session."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO attendance_records (attendance_session_id, student_id, status, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(attendance_session_id, student_id)
            DO UPDATE SET status = excluded.status, updated_at = CURRENT_TIMESTAMP
            """,
            (int(session_id), int(student_id), status),
        )


def bulk_record_session_attendance(
    session_id: int,
    attendance_map: Dict[int, str],
    db_path: Optional[str] = None,
) -> None:
    """Bulk save attendance for all students in a session."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        for student_internal_id, status in attendance_map.items():
            cursor.execute(
                """
                INSERT INTO attendance_records (attendance_session_id, student_id, status, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(attendance_session_id, student_id)
                DO UPDATE SET status = excluded.status, updated_at = CURRENT_TIMESTAMP
                """,
                (int(session_id), int(student_internal_id), status),
            )


def get_student_attendance_summary(
    student_id: int,
    subject_id: Optional[int] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Compute attendance summary for a student grouped by subject:
    Total Sessions, Attended Sessions, Attendance Percentage.
    """
    query = """
        SELECT
            sub.id AS subject_id,
            sub.subject_code,
            sub.subject_name,
            COUNT(ar.id) AS total_sessions,
            SUM(CASE WHEN ar.status = 'Present' THEN 1 ELSE 0 END) AS attended_sessions,
            SUM(CASE WHEN ar.status = 'Late' THEN 1 ELSE 0 END) AS late_sessions,
            SUM(CASE WHEN ar.status = 'Absent' THEN 1 ELSE 0 END) AS absent_sessions,
            ROUND(
                (SUM(CASE WHEN ar.status = 'Present' THEN 1.0 WHEN ar.status = 'Late' THEN 0.5 ELSE 0.0 END) /
                MAX(1, COUNT(ar.id))) * 100.0, 1
            ) AS attendance_percentage
        FROM attendance_records ar
        JOIN attendance_sessions ses ON ar.attendance_session_id = ses.id
        JOIN subjects sub ON ses.subject_id = sub.id
        WHERE ar.student_id = ?
    """
    params: List[Any] = [student_id]
    if subject_id:
        query += " AND sub.id = ?"
        params.append(subject_id)

    query += " GROUP BY sub.id, sub.subject_code, sub.subject_name ORDER BY sub.subject_name ASC"

    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def get_student_attendance_history(
    student_id: int,
    subject_id: Optional[int] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch chronological individual attendance logs for a student."""
    query = """
        SELECT
            ses.session_date,
            sub.subject_name,
            sub.subject_code,
            ses.session_label,
            ar.status,
            ar.created_at
        FROM attendance_records ar
        JOIN attendance_sessions ses ON ar.attendance_session_id = ses.id
        JOIN subjects sub ON ses.subject_id = sub.id
        WHERE ar.student_id = ?
    """
    params: List[Any] = [student_id]
    if subject_id:
        query += " AND sub.id = ?"
        params.append(subject_id)

    query += " ORDER BY ses.session_date DESC, sub.subject_name ASC"

    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


# ============================================================================
# Academic Records Operations
# ============================================================================

def add_academic_record(record_data: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """Insert a new academic evaluation record."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO academic_records (
                student_id, subject, subject_id, examination_type, internal_marks,
                assignment_marks, exam_marks, maximum_marks, attendance_percentage,
                grade, exam_date, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(record_data["student_id"]),
                record_data["subject"].strip(),
                record_data.get("subject_id"),
                record_data.get("examination_type", "End Semester"),
                float(record_data["internal_marks"]),
                float(record_data["assignment_marks"]),
                float(record_data["exam_marks"]),
                float(record_data.get("maximum_marks", 100.0)),
                float(record_data.get("attendance_percentage", 0.0)),
                record_data.get("grade"),
                str(record_data["exam_date"]).strip(),
                record_data.get("created_by"),
            ),
        )
        return cursor.lastrowid


def update_academic_record(record_id: int, record_data: Dict[str, Any], db_path: Optional[str] = None) -> bool:
    """Update an academic evaluation record."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE academic_records
            SET student_id = ?,
                subject = ?,
                internal_marks = ?,
                assignment_marks = ?,
                exam_marks = ?,
                attendance_percentage = ?,
                exam_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                int(record_data["student_id"]),
                record_data["subject"].strip(),
                float(record_data["internal_marks"]),
                float(record_data["assignment_marks"]),
                float(record_data["exam_marks"]),
                float(record_data.get("attendance_percentage", 0.0)),
                str(record_data["exam_date"]).strip(),
                record_id,
            ),
        )
        return cursor.rowcount > 0


def delete_academic_record(record_id: int, db_path: Optional[str] = None) -> bool:
    """Delete an academic record by ID."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM academic_records WHERE id = ?", (record_id,))
        return cursor.rowcount > 0


def get_academic_records_detailed(
    student_id_str: Optional[str] = None,
    student_internal_id: Optional[int] = None,
    department: Optional[str] = None,
    semester: Optional[int] = None,
    subject: Optional[str] = None,
    exam_date: Optional[str] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch academic records joined with student information."""
    query = """
        SELECT
            ar.id AS record_id,
            s.id AS internal_student_id,
            s.student_id,
            s.full_name,
            s.email,
            s.department,
            s.course,
            s.semester,
            ar.subject,
            ar.examination_type,
            ar.internal_marks,
            ar.assignment_marks,
            ar.exam_marks,
            (ar.internal_marks + ar.assignment_marks + ar.exam_marks) AS total_marks,
            ar.maximum_marks,
            ar.attendance_percentage,
            ar.grade,
            ar.exam_date,
            ar.created_at AS record_created_at
        FROM academic_records ar
        JOIN students s ON ar.student_id = s.id
        WHERE 1=1
    """
    params: List[Any] = []

    if student_internal_id:
        query += " AND s.id = ?"
        params.append(student_internal_id)

    if student_id_str and student_id_str != "All":
        query += " AND s.student_id = ?"
        params.append(student_id_str.strip().upper())

    if department and department != "All":
        query += " AND s.department = ?"
        params.append(department.strip())

    if semester and semester != "All":
        query += " AND s.semester = ?"
        params.append(int(semester))

    if subject and subject != "All":
        query += " AND ar.subject = ?"
        params.append(subject.strip())

    if exam_date and exam_date != "All":
        query += " AND ar.exam_date = ?"
        params.append(exam_date.strip())

    query += " ORDER BY s.student_id ASC, ar.exam_date DESC, ar.subject ASC"

    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


# ============================================================================
# Assignments & Submissions Operations
# ============================================================================

def create_assignment(
    title: str,
    subject_name: str,
    course: str,
    semester: int,
    due_date: str,
    description: str = "",
    max_marks: float = 10.0,
    attachment_path: Optional[str] = None,
    created_by: Optional[int] = None,
    db_path: Optional[str] = None,
) -> int:
    """Create a new coursework assignment."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assignments (
                title, description, subject_name, course, semester, due_date,
                max_marks, attachment_path, created_by, is_published
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                title.strip(),
                description.strip(),
                subject_name.strip(),
                course.strip(),
                int(semester),
                str(due_date)[:10],
                float(max_marks),
                attachment_path,
                created_by,
            ),
        )
        return cursor.lastrowid


def get_assignments(
    course: Optional[str] = None,
    semester: Optional[int] = None,
    subject_name: Optional[str] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch published assignments."""
    query = "SELECT * FROM assignments WHERE is_published = 1"
    params: List[Any] = []

    if course and course != "All":
        query += " AND course = ?"
        params.append(course.strip())

    if semester and semester != "All":
        query += " AND semester = ?"
        params.append(int(semester))

    if subject_name and subject_name != "All":
        query += " AND subject_name = ?"
        params.append(subject_name.strip())

    query += " ORDER BY due_date ASC, created_at DESC"

    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def submit_assignment(
    assignment_id: int,
    student_id: int,
    submission_text: str = "",
    submission_path: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    """Record or update student submission for an assignment."""
    aid = int(assignment_id)
    sid = int(student_id)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO assignment_submissions (
                assignment_id, student_id, submission_text, submission_path,
                submission_status, submitted_at
            ) VALUES (?, ?, ?, ?, 'Submitted', CURRENT_TIMESTAMP)
            ON CONFLICT(assignment_id, student_id)
            DO UPDATE SET
                submission_text = excluded.submission_text,
                submission_path = coalesce(excluded.submission_path, assignment_submissions.submission_path),
                submission_status = 'Submitted',
                submitted_at = CURRENT_TIMESTAMP
            """,
            (aid, sid, submission_text.strip(), submission_path),
        )
        cursor.execute(
            "SELECT id FROM assignment_submissions WHERE assignment_id = ? AND student_id = ?",
            (aid, sid),
        )
        row = cursor.fetchone()
        return int(row["id"]) if row else cursor.lastrowid


def get_student_assignment_status(
    assignment_id: int,
    student_id: int,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve submission details for a specific student and assignment."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM assignment_submissions WHERE assignment_id = ? AND student_id = ?",
            (assignment_id, student_id),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def grade_assignment_submission(
    submission_id: int,
    marks_awarded: float,
    feedback: str = "",
    db_path: Optional[str] = None,
) -> bool:
    """Professor grade assignment submission."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE assignment_submissions
            SET marks_awarded = ?, feedback = ?, submission_status = 'Graded'
            WHERE id = ?
            """,
            (float(marks_awarded), feedback.strip(), submission_id),
        )
        return cursor.rowcount > 0


def get_submissions_for_assignment(assignment_id: int, db_path: Optional[str] = None) -> pd.DataFrame:
    """Fetch all student submissions for an assignment with student details."""
    query = """
        SELECT
            sub.id AS submission_id,
            sub.assignment_id,
            s.id AS student_internal_id,
            s.student_id,
            s.full_name,
            sub.submission_status,
            sub.submitted_at,
            sub.submission_text,
            sub.submission_path,
            sub.marks_awarded,
            sub.feedback
        FROM assignment_submissions sub
        JOIN students s ON sub.student_id = s.id
        WHERE sub.assignment_id = ?
        ORDER BY sub.submitted_at DESC
    """
    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=[assignment_id])
    finally:
        conn.close()


# ============================================================================
# Study Materials Operations
# ============================================================================

def add_study_material(
    title: str,
    subject_name: str,
    course: str,
    semester: int,
    file_path: str,
    description: str = "",
    uploaded_by: Optional[int] = None,
    db_path: Optional[str] = None,
) -> int:
    """Upload study resource metadata and file path."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO study_materials (
                title, description, subject_name, course, semester, file_path, uploaded_by, is_published
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                title.strip(),
                description.strip(),
                subject_name.strip(),
                course.strip(),
                int(semester),
                file_path.strip(),
                uploaded_by,
            ),
        )
        return cursor.lastrowid


def get_study_materials(
    course: Optional[str] = None,
    semester: Optional[int] = None,
    subject_name: Optional[str] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch published study materials."""
    query = "SELECT * FROM study_materials WHERE is_published = 1"
    params: List[Any] = []

    if course and course != "All":
        query += " AND course = ?"
        params.append(course.strip())

    if semester and semester != "All":
        query += " AND semester = ?"
        params.append(int(semester))

    if subject_name and subject_name != "All":
        query += " AND subject_name = ?"
        params.append(subject_name.strip())

    query += " ORDER BY uploaded_at DESC"

    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


# ============================================================================
# Announcements Operations
# ============================================================================

def add_announcement(
    title: str,
    message: str,
    department: str = "All",
    course: str = "All",
    semester: int = 0,
    created_by: Optional[int] = None,
    db_path: Optional[str] = None,
) -> int:
    """Publish a targeted campus announcement."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO announcements (
                title, message, department, course, semester, created_by, is_published
            ) VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (
                title.strip(),
                message.strip(),
                department.strip(),
                course.strip(),
                int(semester),
                created_by,
            ),
        )
        return cursor.lastrowid


def get_announcements_for_student(
    department: str,
    course: str,
    semester: int,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Retrieve announcements applicable to a student's cohort or all students."""
    query = """
        SELECT * FROM announcements
        WHERE is_published = 1
          AND (department = 'All' OR department = ?)
          AND (course = 'All' OR course = ?)
          AND (semester = 0 OR semester = ?)
        ORDER BY created_at DESC
    """
    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=[department.strip(), course.strip(), int(semester)])
    finally:
        conn.close()


def get_all_announcements(db_path: Optional[str] = None) -> pd.DataFrame:
    """Retrieve all campus announcements for administrators/professors."""
    query = "SELECT * FROM announcements WHERE is_published = 1 ORDER BY created_at DESC"
    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


# ============================================================================
# Bulk Dataset Import Transactions
# ============================================================================

def bulk_insert_students(
    students: List[Dict[str, Any]], db_path: Optional[str] = None
) -> Tuple[int, List[Dict[str, Any]]]:
    """Bulk insert students in a transaction."""
    success_count = 0
    rejected: List[Dict[str, Any]] = []

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        for idx, row in enumerate(students, start=1):
            s_id = str(row.get("student_id", "")).strip().upper()
            name = str(row.get("full_name", "")).strip()
            email = str(row.get("email", "")).strip().lower()
            dept = str(row.get("department", "")).strip()
            course = str(row.get("course", "")).strip()
            sem = row.get("semester")
            enroll_dt = str(row.get("enrollment_date", "")).strip()

            cursor.execute("SELECT id FROM students WHERE student_id = ?", (s_id,))
            if cursor.fetchone():
                rejected.append({**row, "row_number": idx, "rejection_reason": f"Student ID '{s_id}' already exists."})
                continue

            try:
                cursor.execute(
                    """
                    INSERT INTO students (student_id, full_name, email, department, course, semester, enrollment_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (s_id, name, email, dept, course, int(sem), enroll_dt),
                )
                success_count += 1
            except Exception as e:
                rejected.append({**row, "row_number": idx, "rejection_reason": f"DB Error: {str(e)}"})

    return success_count, rejected




def bulk_insert_academic_records(
    records: List[Dict[str, Any]], db_path: Optional[str] = None
) -> Tuple[int, List[Dict[str, Any]]]:
    """Bulk insert academic performance records in a transaction."""
    success_count = 0
    rejected: List[Dict[str, Any]] = []

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, student_id FROM students")
        student_map = {row["student_id"]: row["id"] for row in cursor.fetchall()}

        for idx, row in enumerate(records, start=1):
            s_id_str = str(row.get("student_id", "")).strip().upper()
            internal_s_id = student_map.get(s_id_str)

            if not internal_s_id:
                rejected.append({
                    **row,
                    "row_number": idx,
                    "rejection_reason": f"Student ID '{s_id_str}' does not exist in students table.",
                })
                continue

            subject = str(row.get("subject", "")).strip()
            exam_dt = str(row.get("exam_date", "")).strip()

            cursor.execute(
                "SELECT id FROM academic_records WHERE student_id = ? AND subject = ? AND exam_date = ?",
                (internal_s_id, subject, exam_dt),
            )
            if cursor.fetchone():
                rejected.append({
                    **row,
                    "row_number": idx,
                    "rejection_reason": f"Duplicate record for student '{s_id_str}', subject '{subject}' on '{exam_dt}'.",
                })
                continue

            try:
                cursor.execute(
                    """
                    INSERT INTO academic_records (
                        student_id, subject, internal_marks, assignment_marks,
                        exam_marks, attendance_percentage, exam_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        internal_s_id,
                        subject,
                        float(row["internal_marks"]),
                        float(row["assignment_marks"]),
                        float(row["exam_marks"]),
                        float(row.get("attendance_percentage", 0.0)),
                        exam_dt,
                    ),
                )
                success_count += 1
            except Exception as e:
                rejected.append({**row, "row_number": idx, "rejection_reason": f"DB Error: {str(e)}"})

    return success_count, rejected




def bulk_insert_attendance_records(
    records: List[Dict[str, Any]], db_path: Optional[str] = None
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Bulk import attendance records from CSV.
    Expected row keys: student_id, subject_code, session_date, session_label, status
    """
    success_count = 0
    rejected: List[Dict[str, Any]] = []

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, student_id FROM students")
        student_map = {row["student_id"]: row["id"] for row in cursor.fetchall()}

        cursor.execute("SELECT id, subject_code FROM subjects")
        subject_map = {row["subject_code"].upper(): row["id"] for row in cursor.fetchall()}

        for idx, row in enumerate(records, start=1):
            s_id = str(row.get("student_id", "")).strip().upper()
            sub_code = str(row.get("subject_code", "")).strip().upper()
            s_date = str(row.get("session_date", "")).strip()[:10]
            s_label = str(row.get("session_label", "Lecture")).strip()
            status = str(row.get("status", "Present")).strip().capitalize()

            internal_s_id = student_map.get(s_id)
            if not internal_s_id:
                rejected.append({**row, "row_number": idx, "rejection_reason": f"Student '{s_id}' not found."})
                continue

            sub_id = subject_map.get(sub_code)
            if not sub_id:
                rejected.append({**row, "row_number": idx, "rejection_reason": f"Subject code '{sub_code}' not found."})
                continue

            # Ensure session exists
            cursor.execute(
                "SELECT id FROM attendance_sessions WHERE subject_id = ? AND session_date = ? AND session_label = ?",
                (sub_id, s_date, s_label),
            )
            sess_row = cursor.fetchone()
            if sess_row:
                session_id = sess_row[0]
            else:
                cursor.execute(
                    "INSERT INTO attendance_sessions (subject_id, session_date, session_label) VALUES (?, ?, ?)",
                    (sub_id, s_date, s_label),
                )
                session_id = cursor.lastrowid

            try:
                cursor.execute(
                    """
                    INSERT INTO attendance_records (attendance_session_id, student_id, status)
                    VALUES (?, ?, ?)
                    ON CONFLICT(attendance_session_id, student_id)
                    DO UPDATE SET status = excluded.status, updated_at = CURRENT_TIMESTAMP
                    """,
                    (session_id, internal_s_id, status),
                )
                success_count += 1
            except Exception as e:
                rejected.append({**row, "row_number": idx, "rejection_reason": str(e)})

    return success_count, rejected




# ============================================================================
# AUDIT LOGGING OPERATIONS
# ============================================================================

def log_audit_action(
    username: str,
    role: str,
    action: str,
    entity_type: str,
    user_id: Optional[int] = None,
    entity_id: Optional[str] = None,
    old_values: Optional[str] = None,
    new_values: Optional[str] = None,
    reason: Optional[str] = None,
    db_path: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """Record an administrative action into the audit trail."""
    def _execute_insert(target_conn):
        cursor = target_conn.cursor()
        valid_uid = None
        if user_id is not None:
            try:
                cursor.execute("SELECT 1 FROM users WHERE id = ?", (int(user_id),))
                if cursor.fetchone():
                    valid_uid = int(user_id)
            except Exception:
                valid_uid = None

        sql = """
            INSERT INTO audit_logs (
                user_id, username, role, action, entity_type, entity_id,
                old_values, new_values, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            valid_uid,
            str(username or "system").strip(),
            str(role or "coordinator").strip(),
            str(action).strip(),
            str(entity_type).strip(),
            str(entity_id) if entity_id is not None else None,
            str(old_values) if old_values is not None else None,
            str(new_values) if new_values is not None else None,
            str(reason).strip() if reason else None,
        )
        cursor.execute(sql, params)
        return cursor.lastrowid

    if conn is not None:
        return _execute_insert(conn)

    with get_db(db_path) as c:
        return _execute_insert(c)

    with get_db(db_path) as c:
        cursor = c.cursor()
        cursor.execute(sql, params)
        return cursor.lastrowid


def get_audit_logs(
    limit: int = 200,
    action_filter: Optional[str] = None,
    entity_filter: Optional[str] = None,
    search: Optional[str] = None,
    db_path: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch recent audit log entries matching filters."""
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params: List[Any] = []

    if action_filter and action_filter != "All":
        query += " AND action = ?"
        params.append(action_filter.strip())

    if entity_filter and entity_filter != "All":
        query += " AND entity_type = ?"
        params.append(entity_filter.strip())

    if search:
        s = f"%{search.strip()}%"
        query += " AND (username LIKE ? OR reason LIKE ? OR entity_id LIKE ? OR new_values LIKE ?)"
        params.extend([s, s, s, s])

    query += f" ORDER BY created_at DESC LIMIT {int(limit)}"

    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


# ============================================================================
# SYSTEM SETTINGS OPERATIONS
# ============================================================================

def get_system_setting(key: str, default: Any = None, db_path: Optional[str] = None) -> Any:
    """Retrieve typed value of a system setting."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value, data_type FROM system_settings WHERE key = ?", (str(key).strip(),))
        row = cursor.fetchone()
        if not row:
            return default
        val, dt = row["value"], row["data_type"]
        if dt == "float":
            try:
                return float(val)
            except (ValueError, TypeError):
                return default
        elif dt == "int":
            try:
                return int(val)
            except (ValueError, TypeError):
                return default
        elif dt == "bool":
            return str(val).lower() in ["1", "true", "yes"]
        return str(val)


def set_system_setting(
    key: str,
    value: Any,
    data_type: str = "string",
    description: Optional[str] = None,
    updated_by: Optional[int] = None,
    db_path: Optional[str] = None,
) -> bool:
    """Update or insert a configurable system setting."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO system_settings (key, value, data_type, description, updated_by, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                data_type = excluded.data_type,
                description = coalesce(excluded.description, system_settings.description),
                updated_by = excluded.updated_by,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                str(key).strip(),
                str(value),
                data_type,
                description,
                int(updated_by) if updated_by is not None else None,
            ),
        )
        return cursor.rowcount > 0


def get_all_system_settings(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Fetch dictionary of all key-value system settings."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value, data_type, description, updated_at FROM system_settings")
        settings = {}
        for row in cursor.fetchall():
            k = row["key"]
            v = row["value"]
            dt = row["data_type"]
            if dt == "float":
                try:
                    v = float(v)
                except ValueError:
                    pass
            elif dt == "int":
                try:
                    v = int(v)
                except ValueError:
                    pass
            elif dt == "bool":
                v = str(v).lower() in ["1", "true", "yes"]
            settings[k] = {
                "value": v,
                "data_type": dt,
                "description": row["description"],
                "updated_at": row["updated_at"],
            }
        return settings


# ============================================================================
# DEPARTMENT AND COURSE MANAGEMENT
# ============================================================================

def get_all_departments(active_only: bool = False, db_path: Optional[str] = None) -> pd.DataFrame:
    """Fetch all academic departments."""
    query = "SELECT * FROM departments"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY department_name ASC"

    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


def add_department(code: str, name: str, description: str = "", db_path: Optional[str] = None) -> int:
    """Register a new academic department."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO departments (department_code, department_name, description, is_active)
            VALUES (?, ?, ?, 1)
            """,
            (code.strip().upper(), name.strip(), description.strip()),
        )
        return cursor.lastrowid


def update_department(
    dept_id: int,
    code: str,
    name: str,
    description: str = "",
    is_active: int = 1,
    db_path: Optional[str] = None,
) -> bool:
    """Update department information."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE departments
            SET department_code = ?, department_name = ?, description = ?, is_active = ?
            WHERE id = ?
            """,
            (code.strip().upper(), name.strip(), description.strip(), int(is_active), int(dept_id)),
        )
        return cursor.rowcount > 0


def get_all_courses(active_only: bool = False, db_path: Optional[str] = None) -> pd.DataFrame:
    """Fetch all academic courses."""
    query = "SELECT * FROM courses"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY course_name ASC"

    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


def add_course(
    code: str,
    name: str,
    department_name: str,
    duration_years: int = 4,
    total_semesters: int = 8,
    db_path: Optional[str] = None,
) -> int:
    """Register a new course/degree program."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO courses (course_code, course_name, department_name, duration_years, total_semesters, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (code.strip().upper(), name.strip(), department_name.strip(), int(duration_years), int(total_semesters)),
        )
        return cursor.lastrowid


def update_course(
    course_id: int,
    code: str,
    name: str,
    department_name: str,
    duration_years: int = 4,
    total_semesters: int = 8,
    is_active: int = 1,
    db_path: Optional[str] = None,
) -> bool:
    """Update course information."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE courses
            SET course_code = ?, course_name = ?, department_name = ?, duration_years = ?, total_semesters = ?, is_active = ?
            WHERE id = ?
            """,
            (code.strip().upper(), name.strip(), department_name.strip(), int(duration_years), int(total_semesters), int(is_active), int(course_id)),
        )
        return cursor.rowcount > 0


# ============================================================================
# SUBJECT MANAGEMENT WITH STABLE ID INTEGRITY
# ============================================================================

def create_subject(
    subject_code: str,
    subject_name: str,
    department: str,
    course: str,
    semester: int,
    credits: int = 3,
    description: str = "",
    db_path: Optional[str] = None,
) -> int:
    """Create a subject with credits and description."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO subjects (subject_code, subject_name, department, course, semester, credits, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                subject_code.strip().upper(),
                subject_name.strip(),
                department.strip(),
                course.strip(),
                int(semester),
                int(credits),
                description.strip(),
            ),
        )
        return cursor.lastrowid


def update_subject(
    subject_id: int,
    subject_code: str,
    subject_name: str,
    department: str,
    course: str,
    semester: int,
    credits: int = 3,
    description: str = "",
    is_active: int = 1,
    updated_by_user: Optional[Dict[str, Any]] = None,
    reason: str = "",
    db_path: Optional[str] = None,
) -> bool:
    """
    Update subject details. Renaming updates displayed subject name throughout
    academic records, assignments, and study materials while maintaining historical data.
    """
    sid = int(subject_id)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM subjects WHERE id = ?", (sid,))
        old_subj = cursor.fetchone()
        if not old_subj:
            return False

        old_name = old_subj["subject_name"]
        old_code = old_subj["subject_code"]
        new_name = subject_name.strip()
        new_code = subject_code.strip().upper()

        # Update subjects table
        cursor.execute(
            """
            UPDATE subjects
            SET subject_code = ?, subject_name = ?, department = ?, course = ?, semester = ?,
                credits = ?, description = ?, is_active = ?
            WHERE id = ?
            """,
            (
                new_code,
                new_name,
                department.strip(),
                course.strip(),
                int(semester),
                int(credits),
                description.strip(),
                int(is_active),
                sid,
            ),
        )

        # Propagate subject name rename to linked records
        if old_name != new_name:
            cursor.execute(
                "UPDATE academic_records SET subject = ? WHERE subject_id = ? OR subject = ?",
                (new_name, sid, old_name),
            )
            cursor.execute(
                "UPDATE assignments SET subject_name = ? WHERE subject_id = ? OR subject_name = ?",
                (new_name, sid, old_name),
            )
            cursor.execute(
                "UPDATE study_materials SET subject_name = ? WHERE subject_id = ? OR subject_name = ?",
                (new_name, sid, old_name),
            )

        # Log to audit trail
        if updated_by_user:
            log_audit_action(
                user_id=updated_by_user.get("id"),
                username=updated_by_user.get("username", "coordinator"),
                role=updated_by_user.get("role", "coordinator"),
                action="UPDATE_SUBJECT",
                entity_type="SUBJECT",
                entity_id=str(sid),
                old_values=f"code: {old_code}, name: {old_name}, active: {old_subj['is_active']}",
                new_values=f"code: {new_code}, name: {new_name}, active: {is_active}",
                reason=reason or "Subject information updated by coordinator",
                conn=conn,
            )

        return True


def toggle_subject_status(
    subject_id: int,
    is_active: int,
    updated_by_user: Optional[Dict[str, Any]] = None,
    reason: str = "",
    db_path: Optional[str] = None,
) -> bool:
    """Archive (is_active=0) or reactivate (is_active=1) a subject."""
    sid = int(subject_id)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE subjects SET is_active = ? WHERE id = ?", (int(is_active), sid))
        action_name = "REACTIVATE_SUBJECT" if is_active else "ARCHIVE_SUBJECT"
        if updated_by_user:
            log_audit_action(
                user_id=updated_by_user.get("id"),
                username=updated_by_user.get("username", "coordinator"),
                role=updated_by_user.get("role", "coordinator"),
                action=action_name,
                entity_type="SUBJECT",
                entity_id=str(sid),
                new_values=f"is_active: {is_active}",
                reason=reason or ("Subject archived" if not is_active else "Subject reactivated"),
                conn=conn,
            )
        return cursor.rowcount > 0


def can_delete_subject(subject_id: int, db_path: Optional[str] = None) -> Tuple[bool, str]:
    """Check if subject has historical dependencies before deletion."""
    sid = int(subject_id)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM academic_records WHERE subject_id = ?", (sid,))
        if cursor.fetchone()[0] > 0:
            return False, "Cannot delete: Subject has linked academic records. Archive it instead to preserve academic history."

        cursor.execute("SELECT COUNT(*) FROM attendance_sessions WHERE subject_id = ?", (sid,))
        if cursor.fetchone()[0] > 0:
            return False, "Cannot delete: Subject has linked attendance sessions. Archive it instead to preserve records."

        cursor.execute("SELECT COUNT(*) FROM assignments WHERE subject_id = ?", (sid,))
        if cursor.fetchone()[0] > 0:
            return False, "Cannot delete: Subject has linked coursework assignments. Archive it instead."

        return True, ""


def delete_subject(subject_id: int, db_path: Optional[str] = None) -> Tuple[bool, str]:
    """Delete a subject if it has no foreign key dependencies."""
    can_del, msg = can_delete_subject(subject_id, db_path=db_path)
    if not can_del:
        return False, msg

    sid = int(subject_id)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student_subjects WHERE subject_id = ?", (sid,))
        cursor.execute("DELETE FROM professor_subjects WHERE subject_id = ?", (sid,))
        cursor.execute("DELETE FROM subjects WHERE id = ?", (sid,))
        return True, "Subject deleted successfully."


# ============================================================================
# PROFESSOR-SUBJECT ALLOCATION
# ============================================================================

def assign_professor_to_subject(
    user_id: int,
    subject_id: int,
    academic_year: str = "2024-2025",
    db_path: Optional[str] = None,
) -> bool:
    """Assign a faculty member to teach a subject."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO professor_subjects (user_id, subject_id, academic_year, is_assigned)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(user_id, subject_id, academic_year) DO UPDATE SET is_assigned = 1
            """,
            (int(user_id), int(subject_id), academic_year.strip()),
        )
        return True


def remove_professor_from_subject(
    user_id: int,
    subject_id: int,
    academic_year: str = "2024-2025",
    db_path: Optional[str] = None,
) -> bool:
    """Remove faculty assignment from a subject."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM professor_subjects
            WHERE user_id = ? AND subject_id = ? AND academic_year = ?
            """,
            (int(user_id), int(subject_id), academic_year.strip()),
        )
        return cursor.rowcount > 0


def get_professor_assigned_subjects(user_id_or_username: Any, db_path: Optional[str] = None) -> List[str]:
    """Retrieve list of subject names assigned to a faculty member."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        # Find user_id if username was provided
        if isinstance(user_id_or_username, str) and not user_id_or_username.isdigit():
            cursor.execute("SELECT id FROM users WHERE username = ?", (user_id_or_username.strip(),))
            row = cursor.fetchone()
            uid = row["id"] if row else None
        else:
            uid = int(user_id_or_username) if user_id_or_username is not None else None

        if not uid:
            return []

        cursor.execute(
            """
            SELECT s.subject_name
            FROM professor_subjects ps
            JOIN subjects s ON ps.subject_id = s.id
            WHERE ps.user_id = ? AND ps.is_assigned = 1 AND s.is_active = 1
            ORDER BY s.subject_name ASC
            """,
            (uid,),
        )
        return [r["subject_name"] for r in cursor.fetchall()]


def get_subject_assigned_professors(subject_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all faculty assigned to a specific subject."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.id AS user_id, u.username, p.full_name, p.email, p.department
            FROM professor_subjects ps
            JOIN users u ON ps.user_id = u.id
            LEFT JOIN professor_profiles p ON u.id = p.user_id
            WHERE ps.subject_id = ? AND ps.is_assigned = 1
            """,
            (int(subject_id),),
        )
        return [dict(r) for r in cursor.fetchall()]


# ============================================================================
# STUDENT-SUBJECT ENROLLMENT
# ============================================================================

def enroll_student_in_subject(
    student_id: int,
    subject_id: int,
    academic_year: str = "2024-2025",
    db_path: Optional[str] = None,
) -> bool:
    """Enroll student in an academic subject."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO student_subjects (student_id, subject_id, academic_year)
            VALUES (?, ?, ?)
            ON CONFLICT(student_id, subject_id, academic_year) DO NOTHING
            """,
            (int(student_id), int(subject_id), academic_year.strip()),
        )
        return True


def unenroll_student_from_subject(
    student_id: int,
    subject_id: int,
    academic_year: str = "2024-2025",
    db_path: Optional[str] = None,
) -> bool:
    """Unenroll student from a subject."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM student_subjects WHERE student_id = ? AND subject_id = ? AND academic_year = ?",
            (int(student_id), int(subject_id), academic_year.strip()),
        )
        return cursor.rowcount > 0


def get_student_enrolled_subjects(student_id: int, db_path: Optional[str] = None) -> pd.DataFrame:
    """Retrieve subjects enrolled by a student."""
    query = """
        SELECT s.id AS subject_id, s.subject_code, s.subject_name, s.department, s.course, s.semester, s.credits
        FROM student_subjects ss
        JOIN subjects s ON ss.subject_id = s.id
        WHERE ss.student_id = ? AND s.is_active = 1
        ORDER BY s.subject_name ASC
    """
    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=[int(student_id)])
    finally:
        conn.close()


def get_subject_enrolled_students(subject_id: int, db_path: Optional[str] = None) -> pd.DataFrame:
    """Retrieve all students enrolled in a subject."""
    query = """
        SELECT st.id AS student_internal_id, st.student_id, st.full_name, st.email, st.department, st.course, st.semester
        FROM student_subjects ss
        JOIN students st ON ss.student_id = st.id
        WHERE ss.subject_id = ?
        ORDER BY st.student_id ASC
    """
    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(query, conn, params=[int(subject_id)])
    finally:
        conn.close()


# ============================================================================
# ATTENDANCE CORRECTION WITH AUDIT TRAIL
# ============================================================================

def correct_student_attendance(
    session_id: int,
    student_id: int,
    new_status: str,
    reason: str,
    actor_user: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> bool:
    """
    Coordinator attendance mistake correction with mandatory audit logging.
    Records who corrected it, old value, new value, timestamp, and justification reason.
    """
    sess_id = int(session_id)
    stu_id = int(student_id)
    clean_status = str(new_status).strip().capitalize()
    clean_reason = str(reason).strip()

    if not clean_reason:
        raise ValueError("A documented reason is mandatory when correcting attendance records.")

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        # Find current record
        cursor.execute(
            "SELECT status FROM attendance_records WHERE attendance_session_id = ? AND student_id = ?",
            (sess_id, stu_id),
        )
        row = cursor.fetchone()
        old_status = row["status"] if row else "None"

        # Update or insert
        cursor.execute(
            """
            INSERT INTO attendance_records (attendance_session_id, student_id, status, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(attendance_session_id, student_id)
            DO UPDATE SET status = excluded.status, updated_at = CURRENT_TIMESTAMP
            """,
            (sess_id, stu_id, clean_status),
        )

        # Audit log
        username = actor_user.get("username", "coordinator") if actor_user else "coordinator"
        user_id = actor_user.get("id") if actor_user else None
        role = actor_user.get("role", "coordinator") if actor_user else "coordinator"

        log_audit_action(
            user_id=user_id,
            username=username,
            role=role,
            action="CORRECT_ATTENDANCE",
            entity_type="ATTENDANCE_RECORD",
            entity_id=f"session:{sess_id}_student:{stu_id}",
            old_values=f"status: {old_status}",
            new_values=f"status: {clean_status}",
            reason=clean_reason,
            conn=conn,
        )
        return True


# ============================================================================
# ACADEMIC MARKS CORRECTION & APPROVAL WITH AUDIT TRAIL
# ============================================================================

def correct_academic_record(
    record_id: int,
    internal_marks: float,
    assignment_marks: float,
    exam_marks: float,
    maximum_marks: float = 100.0,
    reason: str = "",
    actor_user: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> bool:
    """
    Coordinator marks correction with recalculation and mandatory audit logging.
    Validates marks against maximums and recalculates grade.
    """
    rid = int(record_id)
    clean_reason = str(reason).strip()
    if not clean_reason:
        raise ValueError("A documented reason is mandatory when correcting academic results.")

    import validators

    total = round(float(internal_marks) + float(assignment_marks) + float(exam_marks), 2)
    percentage = (total / float(maximum_marks)) * 100.0 if float(maximum_marks) > 0 else 0.0
    g_res = validators.calculate_grade(percentage)
    new_grade = g_res[0] if isinstance(g_res, (list, tuple)) else str(g_res)

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM academic_records WHERE id = ?", (rid,))
        old_rec = cursor.fetchone()
        if not old_rec:
            return False

        old_val_str = (
            f"internal: {old_rec['internal_marks']}, asgn: {old_rec['assignment_marks']}, "
            f"exam: {old_rec['exam_marks']}, grade: {old_rec['grade']}"
        )
        new_val_str = (
            f"internal: {internal_marks}, asgn: {assignment_marks}, "
            f"exam: {exam_marks}, total: {total}, grade: {new_grade}"
        )

        cursor.execute(
            """
            UPDATE academic_records
            SET internal_marks = ?, assignment_marks = ?, exam_marks = ?,
                maximum_marks = ?, grade = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (float(internal_marks), float(assignment_marks), float(exam_marks), float(maximum_marks), new_grade, rid),
        )

        username = actor_user.get("username", "coordinator") if actor_user else "coordinator"
        user_id = actor_user.get("id") if actor_user else None
        role = actor_user.get("role", "coordinator") if actor_user else "coordinator"

        log_audit_action(
            user_id=user_id,
            username=username,
            role=role,
            action="CORRECT_MARKS",
            entity_type="ACADEMIC_RECORD",
            entity_id=str(rid),
            old_values=old_val_str,
            new_values=new_val_str,
            reason=clean_reason,
            conn=conn,
        )
        return True


def approve_academic_records(
    record_ids: List[int],
    actor_user: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> int:
    """Coordinator bulk approval of official examination results."""
    if not record_ids:
        return 0

    user_id = actor_user.get("id") if actor_user else None
    username = actor_user.get("username", "coordinator") if actor_user else "coordinator"
    role = actor_user.get("role", "coordinator") if actor_user else "coordinator"

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        approved_count = 0
        for rid in record_ids:
            cursor.execute(
                """
                UPDATE academic_records
                SET is_approved = 1, approved_by = ?, approval_date = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (user_id, int(rid)),
            )
            approved_count += cursor.rowcount

        log_audit_action(
            user_id=user_id,
            username=username,
            role=role,
            action="APPROVE_RESULTS",
            entity_type="ACADEMIC_RECORDS",
            entity_id=f"count:{approved_count}",
            new_values=f"Approved {approved_count} academic records",
            reason="Official results verification and release by coordinator",
            conn=conn,
        )
        return approved_count


# ============================================================================
# FACULTY & ACCOUNT ADMINISTRATION
# ============================================================================

def get_all_professors_detailed(db_path: Optional[str] = None) -> pd.DataFrame:
    """Fetch all professors joined with their account status and profiles."""
    query = """
        SELECT
            u.id AS user_id,
            u.username,
            u.role,
            u.is_active,
            u.created_at,
            coalesce(p.full_name, u.username) AS full_name,
            coalesce(p.email, 'Not set') AS email,
            coalesce(p.department, 'Not Assigned') AS department
        FROM users u
        LEFT JOIN professor_profiles p ON u.id = p.user_id
        WHERE u.role IN ('professor', 'admin', 'coordinator')
        ORDER BY u.created_at ASC
    """
    conn = get_connection(db_path)
    try:
        df = pd.read_sql_query(query, conn)
        # Fetch assigned subjects for each
        assigned_list = []
        for _, row in df.iterrows():
            subjs = get_professor_assigned_subjects(row["user_id"], db_path=db_path)
            assigned_list.append(", ".join(subjs) if subjs else "None")
        df["assigned_subjects"] = assigned_list
        return df
    finally:
        conn.close()


def set_user_active_status(
    user_id: int,
    is_active: int,
    actor_user: Optional[Dict[str, Any]] = None,
    reason: str = "",
    db_path: Optional[str] = None,
) -> bool:
    """Deactivate or reactivate a user account."""
    uid = int(user_id)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (int(is_active), uid))
        action_name = "ACTIVATE_USER" if is_active else "DEACTIVATE_USER"
        if actor_user:
            log_audit_action(
                user_id=actor_user.get("id"),
                username=actor_user.get("username", "coordinator"),
                role=actor_user.get("role", "coordinator"),
                action=action_name,
                entity_type="USER",
                entity_id=str(uid),
                new_values=f"is_active: {is_active}",
                reason=reason or ("Account deactivated" if not is_active else "Account reactivated"),
                db_path=db_path,
            )
        return cursor.rowcount > 0


def admin_reset_password(
    user_id: int,
    new_password: str,
    actor_user: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> Tuple[bool, str]:
    """Secure password reset by administrator / coordinator."""
    if not new_password or len(new_password) < 6:
        return False, "New password must be at least 6 characters."

    import auth
    hashed = auth.hash_password(new_password)
    uid = int(user_id)
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed, uid))
        if cursor.rowcount > 0:
            if actor_user:
                log_audit_action(
                    user_id=actor_user.get("id"),
                    username=actor_user.get("username", "coordinator"),
                    role=actor_user.get("role", "coordinator"),
                    action="RESET_PASSWORD",
                    entity_type="USER",
                    entity_id=str(uid),
                    new_values="Password reset successfully (hash updated)",
                    reason="Administrative password reset",
                    db_path=db_path,
                )
            return True, "Password reset successfully."
        return False, "User not found."
