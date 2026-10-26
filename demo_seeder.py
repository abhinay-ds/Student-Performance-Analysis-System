"""
Demo and Initial Data Seeder for Campus Performance Portal.
Populates:
- Exactly 4 fictional students (STU1001 Aarav, STU1002 Priya, STU1003 Rohan, STU1004 Ananya) in Semester 3
- Exactly 2 fictional professors (Dr. Neha Kapoor, Prof. Arjun Malhotra)
- Exactly 5 academic subjects
- 10 class attendance sessions per subject (50 sessions, 200 attendance records)
- Academic records across 2 examination periods (Mid-Term & End-Semester)
- 5 coursework assignments with attachments & student submissions
- 5 downloadable educational study materials with real content
- 4 official campus announcements
"""

from pathlib import Path
from datetime import date, timedelta
import database
import auth
from config import MATERIALS_DIR, ASSIGNMENTS_DIR, SUBMISSIONS_DIR, GRADE_RULES


def seed_demo_data(db_path: None = None, force: bool = False) -> None:
    """Seed the complete pre-populated demo dataset into SQLite."""
    database.init_db(db_path)

    # ========================================================================
    # 0. COORDINATOR & DEPARTMENTS / COURSES
    # ========================================================================
    # Initial Academic Coordinator
    u_coord = database.get_user_by_username("coordinator", db_path=db_path)
    if not u_coord:
        pwd_hash = auth.hash_password("Coordinator123!")
        coord_user_id = database.create_user("coordinator", pwd_hash, role="coordinator", db_path=db_path)
    else:
        coord_user_id = u_coord["id"]

    # Fictional Departments
    depts_seed = [
        ("CSE", "Computer Science and Engineering", "Core computing, artificial intelligence, and software engineering."),
        ("IT", "Information Technology", "Cloud infrastructure, enterprise applications, and networking systems."),
        ("ECE", "Electronics and Communication", "Embedded systems, communication networks, and signal processing."),
        ("MATH", "Mathematics", "Discrete mathematical structures, numerical algorithms, and probability."),
    ]
    all_depts = database.get_all_departments(db_path=db_path)
    existing_dept_codes = set(all_depts["department_code"].tolist()) if not all_depts.empty else set()
    for d_code, d_name, d_desc in depts_seed:
        if d_code not in existing_dept_codes:
            database.add_department(d_code, d_name, d_desc, db_path=db_path)

    # Fictional Courses
    courses_seed = [
        ("BTECH_CSE", "B.Tech Computer Science", "Computer Science and Engineering", 4, 8),
        ("BTECH_IT", "B.Tech Information Technology", "Information Technology", 4, 8),
        ("BCA", "Bachelor of Computer Applications", "Computer Science and Engineering", 3, 6),
        ("MTECH_AI", "M.Tech Artificial Intelligence", "Computer Science and Engineering", 2, 4),
    ]
    all_courses = database.get_all_courses(db_path=db_path)
    existing_course_codes = set(all_courses["course_code"].tolist()) if not all_courses.empty else set()
    for c_code, c_name, c_dept, c_dur, c_sem in courses_seed:
        if c_code not in existing_course_codes:
            database.add_course(c_code, c_name, c_dept, c_dur, c_sem, db_path=db_path)

    # ========================================================================
    # 1. PROFESSORS
    # ========================================================================
    # Professor 1: Dr. Neha Kapoor (Python Programming & DBMS)
    u_kapoor = database.get_user_by_username("dr_kapoor", db_path=db_path)
    if not u_kapoor:
        pwd_hash = auth.hash_password("Professor123!")
        kapoor_user_id = database.create_user("dr_kapoor", pwd_hash, role="professor", db_path=db_path)
        database.create_professor_profile(
            kapoor_user_id,
            "Dr. Neha Kapoor",
            "neha.kapoor@example.com",
            "Computer Science and Engineering",
            db_path=db_path,
        )
    else:
        kapoor_user_id = u_kapoor["id"]

    # Professor 2: Prof. Arjun Malhotra (Mathematics, Computer Networks, Data Structures)
    u_malhotra = database.get_user_by_username("prof_malhotra", db_path=db_path)
    if not u_malhotra:
        pwd_hash = auth.hash_password("Professor123!")
        malhotra_user_id = database.create_user("prof_malhotra", pwd_hash, role="professor", db_path=db_path)
        database.create_professor_profile(
            malhotra_user_id,
            "Prof. Arjun Malhotra",
            "arjun.malhotra@example.com",
            "Computer Science and Engineering",
            db_path=db_path,
        )
    else:
        malhotra_user_id = u_malhotra["id"]

    # Also keep backward-compatible prof_smith if not existing
    if not database.get_user_by_username("prof_smith", db_path=db_path):
        pwd_hash = auth.hash_password("Professor123!")
        u_smith = database.create_user("prof_smith", pwd_hash, role="professor", db_path=db_path)
        database.create_professor_profile(u_smith, "Prof. Robert Smith", "r.smith@example.com", "Computer Science and Engineering", db_path=db_path)

    # ========================================================================
    # 2. SUBJECTS (Exactly 5 subjects)
    # ========================================================================
    subjects_seed = [
        ("CS301", "Python Programming", "Computer Science and Engineering", "B.Tech", 3),
        ("CS302", "Database Management Systems", "Computer Science and Engineering", "B.Tech", 3),
        ("MA301", "Mathematics", "Computer Science and Engineering", "B.Tech", 3),
        ("CS303", "Computer Networks", "Computer Science and Engineering", "B.Tech", 3),
        ("CS304", "Data Structures", "Computer Science and Engineering", "B.Tech", 3),
    ]

    all_subs = database.get_all_subjects(db_path=db_path)
    existing_codes = set(all_subs["subject_code"].tolist()) if not all_subs.empty else set()

    for code, name, dept, course, sem in subjects_seed:
        if code not in existing_codes:
            database.add_subject(code, name, dept, course, sem, db_path=db_path)

    all_subs = database.get_all_subjects(db_path=db_path)
    subj_map = {r["subject_name"]: r["id"] for _, r in all_subs.iterrows()}
    subj_code_map = {r["subject_code"]: r["id"] for _, r in all_subs.iterrows()}

    # Assign Faculty to Subjects
    for c in ["CS301", "CS302"]:
        if c in subj_code_map:
            database.assign_professor_to_subject(kapoor_user_id, subj_code_map[c], db_path=db_path)
    for c in ["MA301", "CS303", "CS304"]:
        if c in subj_code_map:
            database.assign_professor_to_subject(malhotra_user_id, subj_code_map[c], db_path=db_path)

    # ========================================================================
    # 3. STUDENTS (Exactly 4 students)
    # ========================================================================
    students_seed = [
        {
            "student_id": "STU1001",
            "username": "aarav",
            "full_name": "Aarav Sharma",
            "email": "aarav.sharma@example.com",
            "department": "Computer Science and Engineering",
            "course": "B.Tech",
            "semester": 3,
            "enrollment_date": "2024-08-01",
        },
        {
            "student_id": "STU1002",
            "username": "priya",
            "full_name": "Priya Verma",
            "email": "priya.verma@example.com",
            "department": "Computer Science and Engineering",
            "course": "B.Tech",
            "semester": 3,
            "enrollment_date": "2024-08-01",
        },
        {
            "student_id": "STU1003",
            "username": "rohan",
            "full_name": "Rohan Mehta",
            "email": "rohan.mehta@example.com",
            "department": "Computer Science and Engineering",
            "course": "B.Tech",
            "semester": 3,
            "enrollment_date": "2024-08-01",
        },
        {
            "student_id": "STU1004",
            "username": "ananya",
            "full_name": "Ananya Singh",
            "email": "ananya.singh@example.com",
            "department": "Computer Science and Engineering",
            "course": "B.Tech",
            "semester": 3,
            "enrollment_date": "2024-08-01",
        },
    ]

    stu_internal_map = {}
    for s_info in students_seed:
        # Create user account
        u_stu = database.get_user_by_username(s_info["username"], db_path=db_path)
        if not u_stu:
            pwd_hash = auth.hash_password("Student123!")
            u_id = database.create_user(s_info["username"], pwd_hash, role="student", db_path=db_path)
        else:
            u_id = u_stu["id"]

        # Create or fetch student record
        existing_stu = database.get_student_by_student_id(s_info["student_id"], db_path=db_path)
        if not existing_stu:
            payload = {
                "user_id": u_id,
                "student_id": s_info["student_id"],
                "full_name": s_info["full_name"],
                "email": s_info["email"],
                "department": s_info["department"],
                "course": s_info["course"],
                "semester": s_info["semester"],
                "enrollment_date": s_info["enrollment_date"],
            }
            internal_id = database.add_student(payload, db_path=db_path)
        else:
            internal_id = existing_stu["id"]

        stu_internal_map[s_info["student_id"]] = internal_id

    s_aarav = stu_internal_map["STU1001"]
    s_priya = stu_internal_map["STU1002"]
    s_rohan = stu_internal_map["STU1003"]
    s_ananya = stu_internal_map["STU1004"]

    # Seed Student-Subject Enrollments
    for stu_id_int in [s_aarav, s_priya, s_rohan, s_ananya]:
        for sub_id_int in subj_code_map.values():
            database.enroll_student_in_subject(stu_id_int, sub_id_int, db_path=db_path)

    # ========================================================================
    # 4. ATTENDANCE SESSIONS & RECORDS (10 sessions per subject = 50 sessions)
    # ========================================================================
    # Session dates across the academic semester
    session_dates = [
        "2025-01-15", "2025-01-22", "2025-01-29", "2025-02-05", "2025-02-12",
        "2025-02-19", "2025-02-26", "2025-03-05", "2025-03-12", "2025-03-19"
    ]

    # Attendance Profiles:
    # Aarav: consistently high (Present on all or 9/10 sessions = 90-100%)
    # Priya: good attendance (8/10 sessions = 80%)
    # Rohan: low attendance (5-6/10 sessions = 50-60% -> triggers <75% warning!)
    # Ananya: moderate attendance (8/10 sessions = 80%)

    for code, name, dept, course, sem in subjects_seed:
        s_id_db = subj_code_map.get(code)
        if not s_id_db:
            continue

        prof_creator = kapoor_user_id if code in ["CS301", "CS302"] else malhotra_user_id

        for idx, s_dt in enumerate(session_dates, start=1):
            s_lbl = f"Lecture {idx}: {name} Core Topics"
            try:
                sess_id = database.create_attendance_session(
                    subject_id=int(s_id_db),
                    session_date=s_dt,
                    session_label=s_lbl,
                    created_by=int(prof_creator),
                    db_path=db_path,
                )
            except Exception:
                # Session already exists
                existing_sess = database.get_attendance_sessions(subject_id=int(s_id_db), date_str=s_dt, db_path=db_path)
                sess_id = int(existing_sess.iloc[0]["session_id"]) if not existing_sess.empty else None

            if sess_id:
                # Aarav: 100% Present (or 90%)
                status_aarav = "Present" if idx != 7 else "Late"
                database.record_student_attendance(int(sess_id), int(s_aarav), status_aarav, db_path=db_path)

                # Priya: 80% Present (Absent on session 4 & 9)
                status_priya = "Absent" if idx in [4, 9] else "Present"
                database.record_student_attendance(int(sess_id), int(s_priya), status_priya, db_path=db_path)

                # Rohan: 50-60% Present (Absent on 3, 5, 7, 8, 10 -> Low Attendance Warning!)
                status_rohan = "Absent" if idx in [3, 5, 7, 8, 10] else ("Late" if idx == 6 else "Present")
                database.record_student_attendance(int(sess_id), int(s_rohan), status_rohan, db_path=db_path)

                # Ananya: 80% Present (Absent on 2 & 8)
                status_ananya = "Absent" if idx in [2, 8] else "Present"
                database.record_student_attendance(int(sess_id), int(s_ananya), status_ananya, db_path=db_path)

    # ========================================================================
    # 5. ACADEMIC RECORDS (Two examination periods: Mid-Term & End-Semester)
    # ========================================================================
    # Periods:
    # Period 1: Mid-Term Exam (2025-03-15)
    # Period 2: End-Semester Exam (2025-05-20)

    # Marks Pattern:
    # Aarav: Consistently Outstanding / Excellent (88-95%)
    # Priya: Very Good (75-85%), but weaker in Mathematics (~55%)
    # Rohan: Below threshold in 2 subjects (<40% fail in Computer Networks & Data Structures)
    # Ananya: Clear improvement from Mid-Term to End-Semester (52% -> 76%)

    academic_evaluations = [
        # --- AARAV SHARMA (STU1001) - Consistently High ---
        # Mid-Term (2025-03-15)
        {"student_id": s_aarav, "subject": "Python Programming", "internal": 19.0, "asgn": 9.5, "exam": 64.0, "att": 95.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "O"},
        {"student_id": s_aarav, "subject": "Database Management Systems", "internal": 18.5, "asgn": 9.0, "exam": 63.0, "att": 94.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "O"},
        {"student_id": s_aarav, "subject": "Mathematics", "internal": 19.5, "asgn": 10.0, "exam": 65.5, "att": 96.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "O"},
        {"student_id": s_aarav, "subject": "Computer Networks", "internal": 18.0, "asgn": 9.0, "exam": 61.0, "att": 92.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "A+" },
        {"student_id": s_aarav, "subject": "Data Structures", "internal": 19.0, "asgn": 9.5, "exam": 65.0, "att": 95.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "O"},
        # End-Semester (2025-05-20)
        {"student_id": s_aarav, "subject": "Python Programming", "internal": 19.5, "asgn": 10.0, "exam": 66.0, "att": 96.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "O"},
        {"student_id": s_aarav, "subject": "Database Management Systems", "internal": 19.0, "asgn": 9.5, "exam": 64.5, "att": 95.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "O"},
        {"student_id": s_aarav, "subject": "Mathematics", "internal": 20.0, "asgn": 10.0, "exam": 67.0, "att": 97.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "O"},
        {"student_id": s_aarav, "subject": "Computer Networks", "internal": 18.5, "asgn": 9.0, "exam": 63.5, "att": 93.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "O"},
        {"student_id": s_aarav, "subject": "Data Structures", "internal": 19.5, "asgn": 9.5, "exam": 66.5, "att": 96.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "O"},

        # --- PRIYA VERMA (STU1002) - Good Marks, but Weaker in Mathematics ---
        # Mid-Term (2025-03-15)
        {"student_id": s_priya, "subject": "Python Programming", "internal": 17.5, "asgn": 8.5, "exam": 57.0, "att": 85.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "A+"},
        {"student_id": s_priya, "subject": "Database Management Systems", "internal": 18.0, "asgn": 9.0, "exam": 59.0, "att": 86.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "A+"},
        {"student_id": s_priya, "subject": "Mathematics", "internal": 12.0, "asgn": 6.0, "exam": 36.0, "att": 80.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "B"}, # weaker 54%
        {"student_id": s_priya, "subject": "Computer Networks", "internal": 16.5, "asgn": 8.0, "exam": 53.5, "att": 82.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "A"},
        {"student_id": s_priya, "subject": "Data Structures", "internal": 17.0, "asgn": 8.5, "exam": 56.5, "att": 84.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "A+"},
        # End-Semester (2025-05-20)
        {"student_id": s_priya, "subject": "Python Programming", "internal": 18.0, "asgn": 9.0, "exam": 58.5, "att": 86.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "A+"},
        {"student_id": s_priya, "subject": "Database Management Systems", "internal": 18.5, "asgn": 9.0, "exam": 60.5, "att": 87.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "A+"},
        {"student_id": s_priya, "subject": "Mathematics", "internal": 13.0, "asgn": 6.5, "exam": 38.0, "att": 81.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "B"}, # 57.5%
        {"student_id": s_priya, "subject": "Computer Networks", "internal": 17.0, "asgn": 8.5, "exam": 55.5, "att": 83.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "A+"},
        {"student_id": s_priya, "subject": "Data Structures", "internal": 17.5, "asgn": 8.5, "exam": 57.0, "att": 85.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "A+"},

        # --- ROHAN MEHTA (STU1003) - Low Marks in 2 subjects (<40% Fail) and Low Attendance ---
        # Mid-Term (2025-03-15)
        {"student_id": s_rohan, "subject": "Python Programming", "internal": 11.0, "asgn": 5.0, "exam": 32.0, "att": 60.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "D"}, # 48%
        {"student_id": s_rohan, "subject": "Database Management Systems", "internal": 10.5, "asgn": 5.0, "exam": 30.5, "att": 58.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "D"}, # 46%
        {"student_id": s_rohan, "subject": "Mathematics", "internal": 9.0, "asgn": 4.5, "exam": 24.5, "att": 55.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "F"}, # 38% Fail
        {"student_id": s_rohan, "subject": "Computer Networks", "internal": 8.5, "asgn": 4.0, "exam": 22.5, "att": 52.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "F"}, # 35% Fail
        {"student_id": s_rohan, "subject": "Data Structures", "internal": 9.5, "asgn": 4.5, "exam": 25.0, "att": 56.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "F"}, # 39% Fail
        # End-Semester (2025-05-20)
        {"student_id": s_rohan, "subject": "Python Programming", "internal": 12.0, "asgn": 5.5, "exam": 34.0, "att": 62.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "D"}, # 51.5%
        {"student_id": s_rohan, "subject": "Database Management Systems", "internal": 11.5, "asgn": 5.0, "exam": 32.0, "att": 60.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "D"}, # 48.5%
        {"student_id": s_rohan, "subject": "Mathematics", "internal": 10.0, "asgn": 5.0, "exam": 26.0, "att": 58.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "F"}, # 41% Pass
        {"student_id": s_rohan, "subject": "Computer Networks", "internal": 8.0, "asgn": 4.0, "exam": 21.0, "att": 50.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "F"}, # 33% Fail
        {"student_id": s_rohan, "subject": "Data Structures", "internal": 8.5, "asgn": 4.0, "exam": 23.5, "att": 53.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "F"}, # 36% Fail

        # --- ANANYA SINGH (STU1004) - Average marks with clear upward trend ---
        # Mid-Term (2025-03-15) - ~52% average
        {"student_id": s_ananya, "subject": "Python Programming", "internal": 13.0, "asgn": 6.5, "exam": 34.5, "att": 76.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "B"}, # 54%
        {"student_id": s_ananya, "subject": "Database Management Systems", "internal": 12.5, "asgn": 6.0, "exam": 33.5, "att": 75.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "B"}, # 52%
        {"student_id": s_ananya, "subject": "Mathematics", "internal": 12.0, "asgn": 6.0, "exam": 32.0, "att": 74.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "D"}, # 50%
        {"student_id": s_ananya, "subject": "Computer Networks", "internal": 13.5, "asgn": 6.5, "exam": 35.0, "att": 77.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "B"}, # 55%
        {"student_id": s_ananya, "subject": "Data Structures", "internal": 12.0, "asgn": 6.0, "exam": 31.0, "att": 75.0, "dt": "2025-03-15", "type": "Mid-Term", "grade": "D"}, # 49%
        # End-Semester (2025-05-20) - ~75% average (Substantial Improvement)
        {"student_id": s_ananya, "subject": "Python Programming", "internal": 17.0, "asgn": 8.5, "exam": 54.5, "att": 82.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "A"}, # 80%
        {"student_id": s_ananya, "subject": "Database Management Systems", "internal": 16.5, "asgn": 8.0, "exam": 52.0, "att": 80.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "A"}, # 76.5%
        {"student_id": s_ananya, "subject": "Mathematics", "internal": 15.5, "asgn": 7.5, "exam": 49.0, "att": 78.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "B+"}, # 72%
        {"student_id": s_ananya, "subject": "Computer Networks", "internal": 16.0, "asgn": 8.0, "exam": 51.5, "att": 81.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "A"}, # 75.5%
        {"student_id": s_ananya, "subject": "Data Structures", "internal": 16.5, "asgn": 8.0, "exam": 53.0, "att": 80.0, "dt": "2025-05-20", "type": "End-Semester", "grade": "A"}, # 77.5%
    ]

    for item in academic_evaluations:
        try:
            database.add_academic_record({
                "student_id": item["student_id"],
                "subject": item["subject"],
                "examination_type": item["type"],
                "internal_marks": item["internal"],
                "assignment_marks": item["asgn"],
                "exam_marks": item["exam"],
                "attendance_percentage": item["att"],
                "grade": item["grade"],
                "exam_date": item["dt"],
            }, db_path=db_path)
        except Exception:
            pass  # Already recorded

    # ========================================================================
    # 6. ASSIGNMENTS & REAL ATTACHMENTS (At least 5 assignments)
    # ========================================================================
    # Create sample attachment documents on disk
    def _create_sample_doc(filename: str, content: str) -> Path:
        filepath = ASSIGNMENTS_DIR / filename
        if not filepath.exists():
            filepath.write_text(content, encoding="utf-8")
        return filepath

    doc1 = _create_sample_doc("Assignment_Python_OOP_ProblemSheet.txt", "Assignment 1: Python Object-Oriented Programming & File Processing Tasks.")
    doc2 = _create_sample_doc("Assignment_DBMS_Normalization_Task.txt", "Assignment 2: Database Schema Normalization (1NF, 2NF, 3NF, BCNF).")
    doc3 = _create_sample_doc("Assignment_Math_LinearAlgebra_ProblemSet.txt", "Assignment 3: Eigenvalues, Vector Spaces, and Linear Transformations.")
    doc4 = _create_sample_doc("Assignment_CN_Subnetting_Design.txt", "Assignment 4: IPv4/IPv6 Subnetting and Routing Table Construction.")
    doc5 = _create_sample_doc("Assignment_DS_BinarySearchTree_Lab.txt", "Assignment 5: Self-Balancing Trees (AVL and Red-Black Trees) Implementation.")

    assign_specs = [
        {
            "title": "Assignment 1: Python OOP & File Stream Processing",
            "subject": "Python Programming",
            "due": "2025-02-15",  # Overdue assignment
            "desc": "Implement an object-oriented file parsing hierarchy handling structured JSON and CSV streams.",
            "max": 10.0,
            "creator": kapoor_user_id,
            "path": str(doc1),
        },
        {
            "title": "Assignment 2: Relational Normalization & SQL Queries",
            "subject": "Database Management Systems",
            "due": "2025-03-30",
            "desc": "Normalize the provided college registrar schema to BCNF and write optimized JOIN queries.",
            "max": 10.0,
            "creator": kapoor_user_id,
            "path": str(doc2),
        },
        {
            "title": "Assignment 3: Discrete Probability & Matrix Transformations",
            "subject": "Mathematics",
            "due": "2025-04-10",
            "desc": "Solve problem set on orthogonal eigenvectors and Bayes theorem applications.",
            "max": 10.0,
            "creator": malhotra_user_id,
            "path": str(doc3),
        },
        {
            "title": "Assignment 4: Network Subnetting & Packet Flow Tracing",
            "subject": "Computer Networks",
            "due": "2025-04-25",
            "desc": "Design a classless inter-domain routing (CIDR) topology for 4 enterprise branch offices.",
            "max": 10.0,
            "creator": malhotra_user_id,
            "path": str(doc4),
        },
        {
            "title": "Assignment 5: AVL Tree & Graph Traversal Algorithms",
            "subject": "Data Structures",
            "due": "2025-05-10",
            "desc": "Implement an AVL Tree with dynamic rotations and Dijkstra's shortest-path algorithm.",
            "max": 10.0,
            "creator": malhotra_user_id,
            "path": str(doc5),
        },
    ]

    all_assigns = database.get_assignments(db_path=db_path)
    existing_titles = set(all_assigns["title"].tolist()) if not all_assigns.empty else set()
    assign_id_map = {}

    for a_item in assign_specs:
        if a_item["title"] not in existing_titles:
            a_id = database.create_assignment(
                title=a_item["title"],
                subject_name=a_item["subject"],
                course="B.Tech",
                semester=3,
                due_date=a_item["due"],
                description=a_item["desc"],
                max_marks=a_item["max"],
                attachment_path=a_item["path"],
                created_by=a_item["creator"],
                db_path=db_path,
            )
            assign_id_map[a_item["title"]] = a_id
        else:
            match_row = all_assigns[all_assigns["title"] == a_item["title"]].iloc[0]
            assign_id_map[a_item["title"]] = int(match_row["id"])

    # Student Submissions (Mixture of Graded, Submitted, and Pending):
    a1_id = assign_id_map.get("Assignment 1: Python OOP & File Stream Processing")
    a2_id = assign_id_map.get("Assignment 2: Relational Normalization & SQL Queries")
    a3_id = assign_id_map.get("Assignment 3: Discrete Probability & Matrix Transformations")
    a4_id = assign_id_map.get("Assignment 4: Network Subnetting & Packet Flow Tracing")
    a5_id = assign_id_map.get("Assignment 5: AVL Tree & Graph Traversal Algorithms")

    # Aarav Sharma: All submitted, A1 & A2 graded with top marks
    if a1_id:
        sub_a1 = database.submit_assignment(a1_id, s_aarav, "Completed OOP stream architecture with clean modular class hierarchy.", db_path=db_path)
        database.grade_assignment_submission(sub_a1, 10.0, "Flawless object model and exception handling.", db_path=db_path)
    if a2_id:
        sub_a2 = database.submit_assignment(a2_id, s_aarav, "Full 3NF & BCNF functional decomposition with relational algebra proofs.", db_path=db_path)
        database.grade_assignment_submission(sub_a2, 9.5, "Strong mathematical proofs on dependencies.", db_path=db_path)
    if a3_id:
        database.submit_assignment(a3_id, s_aarav, "Calculated orthogonal projections and probability density distribution.", db_path=db_path)
    if a4_id:
        database.submit_assignment(a4_id, s_aarav, "CIDR masks and routing table simulator completed.", db_path=db_path)

    # Priya Verma: A1 & A2 submitted and graded, A3 pending
    if a1_id:
        sub_p1 = database.submit_assignment(a1_id, s_priya, "Implemented Python stream reader with JSON parsing support.", db_path=db_path)
        database.grade_assignment_submission(sub_p1, 9.0, "Well structured code.", db_path=db_path)
    if a2_id:
        sub_p2 = database.submit_assignment(a2_id, s_priya, "Normalized tables to 3NF with SQL query execution script.", db_path=db_path)
        database.grade_assignment_submission(sub_p2, 8.5, "Good database design.", db_path=db_path)
    if a4_id:
        database.submit_assignment(a4_id, s_priya, "Subnetting calculations attached.", db_path=db_path)

    # Rohan Mehta: A1 submitted late/graded low, A2, A3, A4 pending
    if a1_id:
        sub_r1 = database.submit_assignment(a1_id, s_rohan, "Basic class implementation submitted.", db_path=db_path)
        database.grade_assignment_submission(sub_r1, 5.0, "Incomplete exception handling; misses stream boundary checks.", db_path=db_path)

    # Ananya Singh: A1, A2 submitted, showing improvement
    if a1_id:
        sub_an1 = database.submit_assignment(a1_id, s_ananya, "Initial Python OOP design submission.", db_path=db_path)
        database.grade_assignment_submission(sub_an1, 7.5, "Good initial effort.", db_path=db_path)
    if a2_id:
        sub_an2 = database.submit_assignment(a2_id, s_ananya, "Comprehensive normalization with clear ER explanations.", db_path=db_path)
        database.grade_assignment_submission(sub_an2, 9.0, "Great improvement in schema design clarity.", db_path=db_path)
    if a5_id:
        database.submit_assignment(a5_id, s_ananya, "AVL tree rotation logic tested and verified.", db_path=db_path)

    # ========================================================================
    # 7. STUDY MATERIALS (5 real downloadable educational documents)
    # ========================================================================
    def _create_study_file(filename: str, content: str) -> Path:
        filepath = MATERIALS_DIR / filename
        if not filepath.exists():
            filepath.write_text(content, encoding="utf-8")
        return filepath

    f_py = _create_study_file(
        "Python_Programming_Fundamentals_Notes.txt",
        "=== Python Programming Core Fundamentals ===\n"
        "1. Dynamic Typing and Memory Model: Variables as Object References.\n"
        "2. List Comprehensions & Generator Expressions: Memory-efficient iteration.\n"
        "3. OOP Concepts: Encapsulation, Polymorphism, Abstract Base Classes (abc).\n"
        "4. Decorators & Context Managers (with statement protocol).\n"
        "5. File Handling & Stream Processing with JSON and CSV.\n"
    )

    f_db = _create_study_file(
        "Database_Management_SQL_Normalization_Guide.txt",
        "=== Database Management Systems: Normalization Guide ===\n"
        "1. First Normal Form (1NF): Atomic attributes, no repeating groups.\n"
        "2. Second Normal Form (2NF): 1NF + No partial functional dependencies on candidate keys.\n"
        "3. Third Normal Form (3NF): 2NF + No transitive dependencies.\n"
        "4. Boyce-Codd Normal Form (BCNF): For every X -> Y, X must be a superkey.\n"
        "5. Query Execution Optimization: Clustered vs Non-Clustered B+ Tree Indexing.\n"
    )

    f_math = _create_study_file(
        "Applied_Mathematics_Formula_Sheet.txt",
        "=== Applied Mathematics: Discrete & Linear Algebra Revision ===\n"
        "1. Determinants and Matrix Inversion: A * adj(A) = det(A) * I.\n"
        "2. Eigenvalues & Eigenvectors: det(A - lambda*I) = 0.\n"
        "3. Diagonalization: A = P * D * P^(-1).\n"
        "4. Bayes Theorem: P(A|B) = [P(B|A) * P(A)] / P(B).\n"
        "5. Mathematical Expectation and Variance of Discrete Random Variables.\n"
    )

    f_net = _create_study_file(
        "Computer_Networks_Protocols_Revision_Notes.txt",
        "=== Computer Networks: OSI & TCP/IP Layer Reference ===\n"
        "1. Physical & Data Link Layer: Framing, CSMA/CD, MAC Addressing.\n"
        "2. Network Layer: IPv4/IPv6, CIDR Subnetting, Routing Protocols (OSPF, BGP).\n"
        "3. Transport Layer: TCP 3-Way Handshake, Flow Control (Sliding Window), Congestion Control.\n"
        "4. Application Layer: DNS Resolution, HTTP/2 vs HTTP/3, TLS/SSL Handshake.\n"
    )

    f_ds = _create_study_file(
        "Data_Structures_Algorithms_Quick_Reference.txt",
        "=== Data Structures & Algorithms Quick Reference ===\n"
        "1. Complexity Classes: O(1), O(log n), O(n), O(n log n), O(n^2).\n"
        "2. Linked Lists, Stacks, Queues, and Priority Queues (Binary Heaps).\n"
        "3. Binary Search Trees (BST) & Self-Balancing AVL Trees (LL, RR, LR, RL Rotations).\n"
        "4. Graph Algorithms: Breadth-First Search (BFS), Depth-First Search (DFS), Dijkstra.\n"
        "5. Dynamic Programming: Optimal Substructure and Overlapping Subproblems.\n"
    )

    materials_specs = [
        ("Python Programming Core Fundamentals Notes", "Python Programming", "B.Tech", 3, str(f_py), "Comprehensive notes covering OOP, generators, decorators, and stream I/O.", kapoor_user_id),
        ("SQL Normalization and Relational Schema Design Guide", "Database Management Systems", "B.Tech", 3, str(f_db), "In-depth reference on 1NF, 2NF, 3NF, BCNF, and B+ Tree indexing.", kapoor_user_id),
        ("Applied Mathematics Formula & Theorem Sheet", "Mathematics", "B.Tech", 3, str(f_math), "Quick formula sheet on matrices, eigenvalues, and discrete probability distributions.", malhotra_user_id),
        ("Computer Networks Protocol Architecture Summary", "Computer Networks", "B.Tech", 3, str(f_net), "Concise revision sheet on OSI layers, subnetting, TCP flow control, and DNS.", malhotra_user_id),
        ("Data Structures and Algorithmic Complexity Reference", "Data Structures", "B.Tech", 3, str(f_ds), "Summary of AVL balance rotations, graph traversals, and heap operations.", malhotra_user_id),
    ]

    all_mats = database.get_study_materials(db_path=db_path)
    existing_mat_titles = set(all_mats["title"].tolist()) if not all_mats.empty else set()

    for m_title, m_subj, m_course, m_sem, m_path, m_desc, m_creator in materials_specs:
        if m_title not in existing_mat_titles:
            database.add_study_material(
                title=m_title,
                subject_name=m_subj,
                course=m_course,
                semester=m_sem,
                file_path=m_path,
                description=m_desc,
                uploaded_by=m_creator,
                db_path=db_path,
            )

    # ========================================================================
    # 8. ANNOUNCEMENTS (Exactly 4 specific notices)
    # ========================================================================
    announcements_seed = [
        {
            "title": "📅 Mid-Semester Examination Schedule Announced",
            "message": "The mid-semester theoretical and lab practical evaluations for B.Tech Semester 3 will be conducted from March 15 to March 25, 2025. Please check the department notice board for your room allocations.",
            "dept": "Computer Science and Engineering",
            "course": "B.Tech",
            "sem": 3,
            "creator": kapoor_user_id,
        },
        {
            "title": "🐍 Python Programming Assignment Deadline Reminder",
            "message": "Reminder from Dr. Neha Kapoor: Assignment 1 (Python OOP & File Stream Processing) is due for final submission. Please ensure your solution scripts adhere to PEP 8 standards.",
            "dept": "Computer Science and Engineering",
            "course": "B.Tech",
            "sem": 3,
            "creator": kapoor_user_id,
        },
        {
            "title": "💾 Database Management Lab Submission Deadline",
            "message": "All students enrolled in CS302 Database Management Systems must submit their normalized schema diagrams and SQL scripts by the end of this week for continuous evaluation grading.",
            "dept": "Computer Science and Engineering",
            "course": "B.Tech",
            "sem": 3,
            "creator": kapoor_user_id,
        },
        {
            "title": "⚠️ Attendance Advisory: Mandatory 75% Requirement",
            "message": "Notice from Prof. Arjun Malhotra: Students with overall class attendance below 75% are strongly advised to meet their course instructors immediately. Attendance below the threshold risks debarment from the final examination.",
            "dept": "Computer Science and Engineering",
            "course": "B.Tech",
            "sem": 3,
            "creator": malhotra_user_id,
        },
    ]

    all_anns = database.get_all_announcements(db_path=db_path)
    existing_ann_titles = set(all_anns["title"].tolist()) if not all_anns.empty else set()

    for ann in announcements_seed:
        if ann["title"] not in existing_ann_titles:
            database.add_announcement(
                title=ann["title"],
                message=ann["message"],
                department=ann["dept"],
                course=ann["course"],
                semester=ann["sem"],
                created_by=ann["creator"],
                db_path=db_path,
            )


def reset_demo_data(actor_user: Optional[Dict[str, Any]] = None, db_path: Optional[str] = None) -> None:
    """
    Restore the demo dataset back to the standard baseline.
    Cleans modified records and re-runs complete demo seeder.
    """
    with database.get_db(db_path) as conn:
        cursor = conn.cursor()
        # Delete dependent tables
        cursor.execute("DELETE FROM attendance_records;")
        cursor.execute("DELETE FROM attendance_sessions;")
        cursor.execute("DELETE FROM academic_records;")
        cursor.execute("DELETE FROM assignment_submissions;")
        cursor.execute("DELETE FROM assignments;")
        cursor.execute("DELETE FROM study_materials;")
        cursor.execute("DELETE FROM announcements;")
        cursor.execute("DELETE FROM student_subjects;")
        cursor.execute("DELETE FROM professor_subjects;")

        # Reset standard subject names and active status
        standard_subjects = [
            ("CS301", "Python Programming"),
            ("CS302", "Database Management Systems"),
            ("MA301", "Mathematics"),
            ("CS303", "Computer Networks"),
            ("CS304", "Data Structures"),
        ]
        for c, n in standard_subjects:
            cursor.execute("UPDATE subjects SET subject_name = ?, is_active = 1 WHERE subject_code = ?", (n, c))

        # Reactivate all users
        cursor.execute("UPDATE users SET is_active = 1;")

    # Re-seed the baseline data
    seed_demo_data(db_path=db_path)

    # Log audit event
    u_name = actor_user.get("username", "coordinator") if actor_user else "coordinator"
    u_id = actor_user.get("id") if actor_user else None
    u_role = actor_user.get("role", "coordinator") if actor_user else "coordinator"
    database.log_audit_action(
        user_id=u_id,
        username=u_name,
        role=u_role,
        action="RESET_DEMO_DATA",
        entity_type="SYSTEM",
        new_values="Restored standard demo baseline dataset",
        reason="Manual demo state reset requested by coordinator",
        db_path=db_path,
    )


if __name__ == "__main__":
    seed_demo_data()
    print("Complete pre-populated demo dataset seeded successfully!")
