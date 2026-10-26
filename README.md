# Campus Performance Portal 🎓
### Complete Academic Governance & Student Performance Analysis System

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%203-003B57.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-42%20Passed-16A34A.svg)](https://pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-gray.svg)](LICENSE)

A production-grade Python web application for educational institutions to manage academic records, monitor student attendance, import institutional datasets, analyze multi-semester performance trends, and facilitate coursework collaboration across specialized, role-based workflows.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Four Access Modes](#-four-access-modes)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Installation and Setup](#-installation-and-setup)
  - [Prerequisites](#prerequisites)
  - [1. Clone Repository](#1-clone-repository)
  - [2. Create Virtual Environment](#2-create-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Environment Configuration](#4-environment-configuration)
- [Database Initialization and Coordinator Setup](#-database-initialization-and-coordinator-setup)
  - [Automatic Initialization](#automatic-initialization)
  - [Manual Seeding via CLI](#manual-seeding-via-cli)
  - [Provisioning the Coordinator Account](#provisioning-the-coordinator-account)
- [Running the Application](#-running-the-application)
- [Login and Demo Personas](#-login-and-demo-personas)
- [Automated Testing](#-automated-testing)
- [Supported Datasets & Sample Files](#-supported-datasets--sample-files)
- [Database, Uploads, and Storage Architecture](#-database-uploads-and-storage-architecture)
- [Security and Safe Deployment](#-security-and-safe-deployment)
- [Limitations and Future Roadmap](#-limitations-and-future-roadmap)

---

## 🌟 Overview

The **Campus Performance Portal** bridges academic administration, faculty grading, and student self-monitoring in a unified, modern web portal. Built with an academic ERP design system (deep navy `#142B4A`, clean whites, subtle borders `#E2E8F0`, and interactive Plotly charts), the system eliminates fragmented spreadsheets through relational SQLite storage and automated analytical reporting.

---

## 🔑 Four Access Modes

The portal provides four distinct access modes with strict role separation:

| Access Mode | Intended User | Permissions & Scope |
| :--- | :--- | :--- |
| **🎓 Student** | Enrolled Students | Personal scorecard, attendance percentages with debarment alerts, assignment submissions, course study materials, official announcements, and academic transcript downloads. **Enforces horizontal isolation** (students cannot view peers' records). |
| **👨‍🏫 Professor** | Academic Faculty | Subject-scoped student rosters, daily session roll calls (Present, Absent, Late, Excused), coursework creation with attachments, assignment evaluation with feedback, internal/exam marks entry, and subject analytics. |
| **🛡️ Coordinator** | Academic Deans / Admins | Full institutional governance: degree programs, departments, curriculum subject management (with cascading rename integrity), professor teaching allocations, cohort enrollments, audited attendance/marks corrections, result verification workflows, system policies, and immutable audit logs. |
| **🚀 Explore Demo** | Evaluators / Reviewers | 1-Click access to explore pre-populated student personas, faculty accounts, or coordinator management without entering passwords. Changes persist across the session and can be restored using the 1-click baseline reset. |

---

## ⚡ Key Features

### 1. Academic Performance & Analytics
- Multi-component evaluation: Internal Assessments (max 20), Coursework/Assignments (max 10), and Final Examinations (max 70).
- Automated grade point calculation, percentage aggregation, and letter grade assignment (O, A+, A, B+, B, C, F) based on institutional grading rules.
- Interactive Plotly visualizations: Subject-wise mark comparison, attendance vs. score correlation scatter plots, pass/fail donuts, and grade distributions.
- Early intervention flags identifying at-risk students falling below minimum attendance (75%) or passing mark (40%) thresholds.

### 2. Daily Attendance Tracking
- Session-based roll call management by subject, date, and lecture label.
- Real-time attendance percentage recalculation per student and subject.
- Automated warning alerts and eligibility badges for examinations.

### 3. Coursework & Learning Materials
- Assignment distribution with attached reference documents.
- Online student submissions with time-stamped status tracking.
- Subject-organized repository for downloadable lecture notes, formula sheets, and study materials.

### 4. Coordinator Governance & Auditing
- **Cascading Subject Renaming:** Atomically synchronizes subject name updates across student marks, attendance sessions, assignments, and study materials without data loss.
- **Accredited Deletion Safeguard:** Prevents deletion of subjects containing historical student marks or attendance logs; archives them safely instead.
- **Audited Corrections:** Coordinator corrections to student attendance or marks require mandatory justification reasons recorded in the audit trail.
- **Formal Result Verification:** Staged grade verification and release workflow for institutional transcripts.
- **Configurable Thresholds:** Real-time adjustments to attendance limits, passing scores, institutional names, and academic calendar years.

---

## 🛠️ Technology Stack

| Technology | Role & Purpose |
| :--- | :--- |
| **Python 3.10 – 3.14** | Core programming language, backend business logic, validation, and CLI tools. |
| **Streamlit (>= 1.30)** | Single-page and multi-page web application interface, responsive layouts, forms, and session state management. |
| **SQLite 3** | Relational database engine with ACID transactions, foreign key constraints, and custom Python datetime/NumPy adapters. |
| **Pandas (>= 2.0)** | High-performance tabular data manipulation, roster aggregation, spreadsheet imports, and dataset transformations. |
| **NumPy (>= 1.24)** | Vectorized numerical operations, threshold evaluations, and statistical metrics. |
| **Plotly (>= 5.18)** | High-contrast, interactive academic charts (radar, bar charts, donut distributions, scatter plots). |
| **OpenPyXL (>= 3.1)** | Multi-tab formatted Excel report generation (`.xlsx`) and transcript generation. |
| **Pytest (>= 7.4)** | Automated test framework for database integrity, role permissions, analytics, and upload validation. |

---

## 📂 Project Directory Structure

```text
Campus-Performance-Portal/
├── .env.example                    # Sample environment variable template
├── .gitignore                      # Git exclusion rules (caches, DBs, exports, secrets)
├── .streamlit/
│   └── config.toml                 # Streamlit UI theme and server configuration
├── README.md                       # Comprehensive project documentation
├── requirements.txt                # Production and test Python dependencies
│
├── academic_service.py             # Coursework and study materials business logic
├── analytics.py                    # Plotly chart generation and statistical KPIs
├── app.py                          # Application entry point, routing, and login
├── attendance_service.py           # Roll-call tracking and attendance aggregation
├── auth.py                         # PBKDF2 password hashing and session management
├── config.py                       # Global constants, thresholds, paths, and policies
├── database.py                     # SQLite schema definitions, CRUD operations, transactions
├── demo_seeder.py                  # Synthetic demo dataset generator and baseline reset
├── init_admin.py                   # CLI utility to create the initial administrator
├── init_coordinator.py             # CLI utility to create or reset the academic coordinator
├── permissions.py                  # Role-based access control (RBAC) and page guards
├── report_generator.py             # Excel (.xlsx) and CSV academic report exporter
├── ui_theme.py                     # Centralized ERP UI styling, cards, and badges
├── upload_service.py               # Roster and marks file upload processors
├── validators.py                   # Data validation for student records and assessments
│
├── data/                           # Relational database directory
│   ├── .gitkeep                    # Preserves directory in git
│   └── student_performance.db     # Local SQLite database (ignored by git)
│
├── pages/                          # Role-based Streamlit application pages
│   ├── 1_Home.py                   # Role-specific dashboard (Student / Professor / Coordinator)
│   ├── 2_Attendance.py             # Student personal attendance breakdown
│   ├── 3_Academic_Performance.py   # Student personal marks scorecard & radar chart
│   ├── 4_Assignments.py            # Coursework submissions and grading
│   ├── 5_Study_Materials.py        # Educational resource center
│   ├── 6_Announcements.py          # Campus notices and broadcasts
│   ├── 7_Student_Management.py     # Faculty roster management
│   ├── 8_Attendance_Management.py  # Faculty roll-call marking
│   ├── 9_Marks_Management.py       # Faculty assessment grading
│   ├── 10_Dataset_Upload.py        # Coordinator batch CSV/Excel import
│   ├── 11_Academic_Analytics.py    # Institution-wide analytics and at-risk monitoring
│   ├── 12_Reports.py               # Excel and CSV export generation
│   ├── 13_Professor_Management.py  # Faculty onboarding and teaching allocation
│   ├── 14_Subject_Management.py    # Curriculum administration and cascading rename
│   ├── 15_Course_Department_Management.py # Degree programs and departments
│   ├── 16_Enrollment_Management.py # Cohort and subject enrollment
│   ├── 17_System_Settings.py       # Configurable institutional thresholds and policies
│   ├── 18_Audit_Logs.py            # Immutable administrative audit log viewer
│   ├── 19_Demo_Management.py       # 1-Click demo dataset baseline reset
│   └── profile.py                  # User account profile and password change
│
├── reports/                        # Exported academic reports
│   └── .gitkeep                    # Preserves directory in git
│
├── sample_data/                    # Ready-to-import sample datasets and templates
│   ├── academic_records_sample.csv # Sample multi-subject examination marks
│   ├── academic_records_template.csv # Empty header template for marks import
│   ├── attendance_sample.csv       # Sample session attendance log
│   ├── marks_sample.csv            # Sample single-subject marks records
│   ├── students_sample.csv         # Sample student cohort roster
│   └── students_template.csv       # Empty header template for student import
│
├── tests/                          # Automated Pytest test suite (42 tests)
│   ├── conftest.py                 # Pytest fixtures and isolated test database setup
│   ├── test_academics.py           # Tests for assignments and study materials
│   ├── test_analytics.py           # Tests for analytical aggregations and Plotly builders
│   ├── test_attendance.py          # Tests for roll calls and duplicate prevention
│   ├── test_auth.py                # Tests for password hashing and authentication
│   ├── test_coordinator.py         # Tests for cascading subject rename, corrections, RBAC
│   ├── test_database.py            # Tests for CRUD operations and ACID rollbacks
│   ├── test_permissions.py         # Tests for horizontal isolation and demo safeguards
│   ├── test_reports.py             # Tests for Excel generation and CSV sanitization
│   ├── test_uploads.py             # Tests for CSV parsing and roster validation
│   └── test_validators.py          # Tests for marks thresholds and schema validation
│
└── uploads/                        # Educational documents and attachments
    ├── assignments/                # Assignment problem sheets
    │   └── .gitkeep
    ├── materials/                  # Downloadable study notes and guides
    │   └── .gitkeep
    └── submissions/                # Student coursework submission uploads
        └── .gitkeep
```

---

## 💻 Installation and Setup

### Prerequisites
- **Python:** 3.10, 3.11, 3.12, 3.13, or 3.14.
- **Git:** Installed on your local machine.
- **Browser:** Any modern browser (Chrome, Firefox, Safari, Edge).

### 1. Clone Repository
```bash
git clone https://github.com/your-username/Campus-Performance-Portal.git
cd Campus-Performance-Portal
```

### 2. Create Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Configuration
The application runs out of the box with default paths. To customize paths or port bindings, copy the example environment configuration:
```bash
cp .env.example .env
```
*(On Windows: `copy .env.example .env`)*

---

## 🗄️ Database Initialization and Coordinator Setup

### Automatic Initialization
When you launch the Streamlit application for the first time via `streamlit run app.py`, the system:
1. Automatically executes `database.init_db()` to generate all relational tables and indexes.
2. Invokes `demo_seeder.seed_demo_data()` to populate the pre-configured synthetic academic dataset (4 students, 2 professors, 5 subjects, attendance sessions, assignments, study materials, and system settings).

### Manual Seeding via CLI
You can initialize or reseed the database directly from the terminal without starting the web server:
```bash
python demo_seeder.py
```

### Provisioning the Coordinator Account
To configure or reset the initial Academic Coordinator credentials with interactive, hidden-password prompts:
```bash
python init_coordinator.py
```
Or pass credentials explicitly via CLI flags:
```bash
python init_coordinator.py --username coordinator --password YourStrongPassword123!
```

To create an administrator account using `init_admin.py`:
```bash
python init_admin.py --username admin --password AdminStrongPassword123! --role coordinator
```

---

## 🚀 Running the Application

Launch the application using Streamlit:
```bash
streamlit run app.py
```

To run on a specific network port or host interface:
```bash
streamlit run app.py --server.port 8501 --server.address 127.0.0.1
```

Once running, navigate to:
```text
http://localhost:8501
```

---

## 👤 Login and Demo Personas

The portal includes safe, synthetic demo accounts for immediate demonstration during evaluations or code walkthroughs. All demo accounts use fictional identities under `example.com`:

### Fictional Personas Included in Demo Seed

| Role | Username | Persona / Scope | Academic Profile |
| :--- | :--- | :--- | :--- |
| **Student** | `aarav` *(or `STU1001`)* | Aarav Sharma (Semester 3, CSE) | Consistent high performer (92% average, 95% attendance). |
| **Student** | `priya` *(or `STU1002`)* | Priya Verma (Semester 3, CSE) | Strong overall (80%), requires focus in Mathematics. |
| **Student** | `rohan` *(or `STU1003`)* | Rohan Mehta (Semester 3, CSE) | At-risk alert: low attendance (<75%), failing in 2 subjects. |
| **Student** | `ananya` *(or `STU1004`)* | Ananya Singh (Semester 3, CSE) | Upward trajectory: improved from 52% to 76%. |
| **Professor** | `dr_kapoor` | Dr. Neha Kapoor (CSE Dept) | Teaches *Python Programming* & *Database Management Systems*. |
| **Professor** | `prof_malhotra` | Prof. Arjun Malhotra (CSE Dept) | Teaches *Mathematics*, *Computer Networks*, & *Data Structures*. |
| **Coordinator**| `coordinator` | Academic Governance Office | Full administrative access across all subjects, departments, and cohorts. |

> [!NOTE]
> Demo passwords seeded for local evaluation are structured as `Role123!` (e.g., `Student123!`, `Professor123!`, `Coordinator123!`). For production deployments, run `python init_coordinator.py` to set unique, strong credentials, or update your password via the **Profile** page.

---

## 🧪 Automated Testing

The project includes **42 automated test cases** covering database transactions, RBAC, analytics, validation, and file generation.

### Running the Full Test Suite
```bash
python -m pytest -v
```

### Running Specific Test Modules
```bash
# Run coordinator governance & cascading rename tests
python -m pytest tests/test_coordinator.py -v

# Run authentication and password hashing tests
python -m pytest tests/test_auth.py -v

# Run analytical calculations and Plotly builder tests
python -m pytest tests/test_analytics.py -v

# Run CSV and Excel report generation tests
python -m pytest tests/test_reports.py -v
```

> [!TIP]
> The automated test suite executes using an isolated in-memory or temporary SQLite database configured via `tests/conftest.py`. Running tests will never modify or overwrite your active `data/student_performance.db` file.

---

## 📊 Supported Datasets & Sample Files

The portal supports uploading student rosters, examination marks, and attendance logs via CSV (`.csv`) or Excel (`.xlsx`) files. Ready-to-import templates and pre-populated samples are located in the `sample_data/` folder:

| Sample File | Format | Expected Columns / Purpose |
| :--- | :--- | :--- |
| `sample_data/students_sample.csv` | CSV | `student_id`, `full_name`, `email`, `department`, `course`, `semester` |
| `sample_data/students_template.csv` | CSV | Blank header template for onboarding a new student cohort |
| `sample_data/marks_sample.csv` | CSV | `student_id`, `subject`, `internal_marks`, `assignment_marks`, `exam_marks`, `semester`, `exam_date` |
| `sample_data/academic_records_template.csv`| CSV | Blank header template for batch exam grade entry |
| `sample_data/attendance_sample.csv` | CSV | `student_id`, `subject`, `session_date`, `status`, `session_label` |

### Upload Guidelines:
- Maximum file size: **20 MB** per upload (configurable in `config.py`).
- Supported file extensions for study resources: `.pdf`, `.docx`, `.pptx`, `.txt`, `.png`, `.jpg`.
- File validation checks for required column headers, valid numeric score boundaries, and existing student IDs prior to database commit.

---

## 🗃️ Database, Uploads, and Storage Architecture

### Relational Schema Overview
The SQLite database (`student_performance.db`) enforces relational integrity across 18 tables:
- **Core Entities:** `users`, `students`, `professor_profiles`, `departments`, `courses`, `subjects`.
- **Academic Operations:** `academic_records`, `attendance_sessions`, `attendance_records`, `student_subjects`, `professor_subjects`.
- **Coursework & Content:** `assignments`, `assignment_submissions`, `study_materials`, `announcements`.
- **Governance & Auditing:** `system_settings`, `audit_logs`.

### Storage Paths
- **Database:** `data/student_performance.db` (override path using `STUDENT_DB_PATH`).
- **Generated Reports:** `reports/` (all exported `.xlsx` and `.csv` files).
- **Uploaded Study Materials:** `uploads/materials/`.
- **Assignment Attachments:** `uploads/assignments/`.
- **Student Submissions:** `uploads/submissions/`.

---

## 🔒 Security and Safe Deployment

### Security Safeguards Implemented
1. **Password Hashing:** Passwords are never stored in plain text. Stored credentials utilize `hashlib.pbkdf2_hmac` (`SHA-256`) with a cryptographically secure 16-byte random salt and 100,000 iterations.
2. **Horizontal Privilege Isolation:** Student endpoints strictly restrict database queries to the authenticated user's `student_id`. Students cannot read or query records belonging to other students.
3. **Role-Based Access Control (RBAC):** Administrative pages (`pages/10_*.py` through `pages/19_*.py`) verify coordinator privileges via `permissions.py`. Unauthorized users are immediately redirected.
4. **Audit Logging:** Administrative changes to attendance, grade corrections, subject renames, and demo resets generate immutable records in the `audit_logs` table containing the actor, timestamp, old values, new values, and mandatory justification reasons.
5. **Safe Data Policy:** All bundled datasets and demo records use fictional identities (`example.com`).

### Production Deployment Checklist
- [ ] Set a custom `STUDENT_DB_PATH` pointing to a secured persistent volume.
- [ ] Run `python init_coordinator.py` to configure a unique administrator password.
- [ ] Ensure `.env` and `.streamlit/secrets.toml` are never committed to version control (configured in `.gitignore`).
- [ ] Place the Streamlit application behind a reverse proxy (e.g., Nginx, Caddy) with TLS/SSL encryption enabled.
- [ ] Restrict file permissions on `data/` and `uploads/` to the application runtime service account.

---

## 🚀 Limitations and Future Roadmap

### Current Scope & Architectural Boundaries
- **Single-Tenant Database:** Engineered for individual institutions or campus departments. Multi-tenant database tenancy is not currently included.
- **Synchronous Notification System:** Announcements and broadcast notices are displayed within the web portal; external SMTP email delivery and SMS gateways are mocked.
- **Local File System Storage:** Uploaded lecture materials and assignments are stored on the local file system rather than S3/cloud object storage.

### Future Roadmap
- [ ] Cloud object storage integration (AWS S3, Google Cloud Storage, Azure Blob).
- [ ] Single Sign-On (SSO) integration via OAuth2, Google Workspace, and SAML.
- [ ] Automated email/SMS alerts to guardians when student attendance falls below 75%.
- [ ] Direct transcript generation with institutional cryptographic verification signatures.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
