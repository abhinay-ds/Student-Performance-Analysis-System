"""
Configuration and constants for Student Performance Analysis System.
Provides centralized grading thresholds, assessment limits, role definitions,
and file storage paths for the Campus Performance Portal.
"""

from pathlib import Path
import os

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
UPLOADS_DIR = BASE_DIR / "uploads"
MATERIALS_DIR = UPLOADS_DIR / "materials"
ASSIGNMENTS_DIR = UPLOADS_DIR / "assignments"
SUBMISSIONS_DIR = UPLOADS_DIR / "submissions"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
MATERIALS_DIR.mkdir(parents=True, exist_ok=True)
ASSIGNMENTS_DIR.mkdir(parents=True, exist_ok=True)
SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Database path (can be overridden via environment variable)
DATABASE_PATH = os.environ.get("STUDENT_DB_PATH", str(DATA_DIR / "student_performance.db"))

# Application Metadata
APP_NAME = "Campus Performance Portal"
APP_SUBTITLE = "Your academic journey, organized."

# Role Definitions
ROLE_STUDENT = "student"
ROLE_PROFESSOR = "professor"
ROLE_COORDINATOR = "coordinator"
ROLE_ADMIN = "admin"
ROLE_DEMO = "demo"

# Default System Settings Key-Value Store
DEFAULT_SYSTEM_SETTINGS = {
    "institution_name": ("Campus Performance Portal", "string", "Official institutional display name"),
    "minimum_attendance_threshold": ("75.0", "float", "Minimum required attendance percentage before warning"),
    "pass_mark_threshold": ("40.0", "float", "Minimum total percentage required to pass a subject"),
    "support_needed_threshold": ("50.0", "float", "Score threshold below which student requires academic support"),
    "current_academic_year": ("2024-2025", "string", "Current active academic session year"),
    "max_upload_size_mb": ("20", "int", "Maximum file upload limit in megabytes"),
    "grading_policy_name": ("University 10-Point Credit Scale", "string", "Active academic grading scheme"),
}

# Assessment Maximum Limits
MAX_INTERNAL_MARKS = 20.0
MAX_ASSIGNMENT_MARKS = 10.0
MAX_EXAM_MARKS = 70.0
MAX_TOTAL_MARKS = 100.0

# Academic Thresholds
PASS_MARK_THRESHOLD = 40.0
ATTENDANCE_SUPPORT_THRESHOLD = 75.0
SUPPORT_NEEDED_SCORE_THRESHOLD = 50.0

# File Upload Rules
ALLOWED_MATERIAL_EXTENSIONS = [".pdf", ".docx", ".pptx", ".txt", ".png", ".jpg", ".jpeg"]
ALLOWED_DATASET_EXTENSIONS = [".csv", ".xlsx"]
MAX_UPLOAD_FILE_SIZE_MB = 20

# Configurable Grade Scale
# Format: (grade_letter, minimum_score, grade_point, description)
GRADE_RULES = [
    ("O", 90.0, 10.0, "Outstanding"),
    ("A+", 80.0, 9.0, "Excellent"),
    ("A", 70.0, 8.0, "Very Good"),
    ("B+", 60.0, 7.0, "Good"),
    ("B", 50.0, 6.0, "Above Average"),
    ("C", 40.0, 5.0, "Pass"),
    ("F", 0.0, 0.0, "Fail"),
]

# Standard Academic Dropdowns
DEPARTMENTS = [
    "Computer Science and Engineering",
    "Information Technology",
    "Electronics and Communication",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "Artificial Intelligence and Data Science",
]

COURSES = [
    "B.Tech",
    "B.E.",
    "B.Sc",
    "BCA",
    "M.Tech",
    "MCA",
]

SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8]

# Password Security Configuration
PASSWORD_SALT_BYTES = 16
PBKDF2_ITERATIONS = 100_000
