"""
Authorization and Role-Based Access Control Module for Campus Performance Portal.
Enforces server-side permissions for students, professors, and administrators,
manages interactive demo switching, and restricts professors to authorized subjects.
"""

from typing import List, Optional, Dict, Any
import streamlit as st
import database
from config import ROLE_STUDENT, ROLE_PROFESSOR, ROLE_COORDINATOR, ROLE_ADMIN, ROLE_DEMO

DEMO_STUDENTS = {
    "STU1001": "Aarav Sharma (STU1001) — High Marks & High Attendance",
    "STU1002": "Priya Verma (STU1002) — Good Marks with Weaker Subject",
    "STU1003": "Rohan Mehta (STU1003) — Low Attendance (<75%) & Needs Support",
    "STU1004": "Ananya Singh (STU1004) — Average Marks with Improving Trend",
}

DEMO_PROFESSORS = {
    "dr_kapoor": "Dr. Neha Kapoor — Python Programming & Database Management",
    "prof_malhotra": "Prof. Arjun Malhotra — Mathematics, Computer Networks & Data Structures",
}

PROFESSOR_SUBJECT_MAP = {
    "dr_kapoor": ["Python Programming", "Database Management Systems"],
    "prof_malhotra": ["Mathematics", "Computer Networks", "Data Structures"],
}


def is_authenticated() -> bool:
    """Return whether current session has an active authenticated user or demo session."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    return bool(st.session_state.authenticated)


def is_demo_mode() -> bool:
    """Return whether current session is in Demo Mode."""
    if "is_demo" not in st.session_state:
        st.session_state.is_demo = False
    return bool(st.session_state.is_demo)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return current user dictionary from session state."""
    return st.session_state.get("current_user")


def get_current_role() -> str:
    """Return active role of logged-in user or demo persona."""
    if is_demo_mode():
        return st.session_state.get("demo_role", "demo_student")
    user = get_current_user()
    return user.get("role", "student") if user else "guest"


def is_coordinator() -> bool:
    """Return whether active session is an academic coordinator or admin."""
    role = get_current_role()
    return role in [ROLE_COORDINATOR, ROLE_ADMIN, "demo_coordinator"]


def is_student() -> bool:
    """Return whether active session is a student (real or demo)."""
    role = get_current_role()
    return role in [ROLE_STUDENT, "demo_student"]


def is_professor() -> bool:
    """Return whether active session has faculty privileges."""
    if is_coordinator():
        return True
    role = get_current_role()
    return role in [ROLE_PROFESSOR, "demo_professor"]


def get_current_student_profile() -> Optional[Dict[str, Any]]:
    """
    For student sessions, retrieve the active student's demographic profile.
    In Demo Mode, returns the student selected via the demo student switcher.
    Guarantees that a student can only view their own records.
    """
    if is_demo_mode() and is_student():
        target_s_id = st.session_state.get("demo_selected_student_id", "STU1001")
        stu = database.get_student_by_student_id(target_s_id)
        if stu:
            st.session_state.current_student_profile = stu
            return stu

    if "current_student_profile" in st.session_state and st.session_state.current_student_profile:
        return st.session_state.current_student_profile

    user = get_current_user()
    if not user:
        return None

    student = database.get_student_by_user_id(user["id"])
    if not student:
        student = database.get_student_by_student_id(user["username"])
    st.session_state.current_student_profile = student
    return student


def get_active_professor_username() -> str:
    """Return username of active professor (in demo or live mode)."""
    if is_demo_mode() and is_professor():
        return st.session_state.get("demo_selected_professor", "dr_kapoor")
    user = get_current_user()
    return user.get("username", "dr_kapoor") if user else "dr_kapoor"


def get_professor_authorized_subjects(prof_username: Optional[str] = None) -> List[str]:
    """
    Return list of subjects authorized for the given professor.
    Coordinators and Administrators have institution-wide access across all subjects.
    Faculty members have access to their assigned subjects.
    """
    if is_coordinator():
        all_s = database.get_all_subjects()
        if not all_s.empty:
            return all_s["subject_name"].tolist()
        return ["Python Programming", "Database Management Systems", "Mathematics", "Computer Networks", "Data Structures"]

    username = prof_username or get_active_professor_username()
    # Check dynamic DB assignments first
    assigned = database.get_professor_assigned_subjects(username)
    if assigned:
        return assigned

    return PROFESSOR_SUBJECT_MAP.get(username, ["Python Programming", "Database Management Systems", "Mathematics", "Computer Networks", "Data Structures"])


def can_access_student(target_student_id_str: str) -> bool:
    """
    Server-side verification preventing horizontal privilege escalation.
    Students can only access their own student_id.
    """
    if is_professor():
        return True
    student = get_current_student_profile()
    if not student:
        return False
    return student["student_id"].upper() == target_student_id_str.strip().upper()


def prevent_demo_mutation() -> bool:
    """
    Student interface guard: Students cannot alter official marks, attendance, or profiles.
    Professors in demo mode CAN perform demo changes so evaluators see live updates.
    """
    if is_student():
        st.warning("🔒 **Action Blocked:** Official university academic records can only be modified by authorized faculty.")
        return True
    return False


def require_role(allowed_roles: List[str]) -> None:
    """Block execution and display access restriction if active role is not in allowed_roles."""
    if not is_authenticated():
        st.error("⚠️ Authentication required. Please sign in to access this portal.")
        st.stop()

    current_role = get_current_role()
    # Academic Coordinator and Administrator have comprehensive administrative access
    if is_coordinator() and any(r in ["coordinator", "admin", "professor", "demo_coordinator", "demo_professor"] for r in allowed_roles):
        return

    normalized = "student" if "student" in current_role else ("professor" if "professor" in current_role or "admin" in current_role or "coordinator" in current_role else current_role)

    if current_role not in allowed_roles and normalized not in allowed_roles:
        st.error(f"🚫 Access Denied: This page is restricted to authorized {', '.join(allowed_roles)} accounts.")
        st.stop()


def render_demo_banner() -> None:
    """Render interactive persona switcher and persistent status banner in Demo Mode."""
    if not is_demo_mode():
        return

    if is_student():
        current_sel = st.session_state.get("demo_selected_student_id", "STU1001")
        st.markdown(
            """
            <div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px;
                        padding: 10px 16px; margin-bottom: 12px; display: flex;
                        justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-weight: 700; color: #1D4ED8; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">
                        Demo Environment
                    </span>
                    <span style="color: #334155; font-size: 13px; margin-left: 8px;">
                        Interactive synthetic student dataset. Changes reflect immediately across records.
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Interactive Student Switcher
        c_label, c_sel = st.columns([1.2, 3.8])
        with c_label:
            st.markdown("<p style='margin-top:6px; font-weight:600; font-size:13px; color:#475569;'>Switch Persona:</p>", unsafe_allow_html=True)
        with c_sel:
            student_keys = list(DEMO_STUDENTS.keys())
            idx = student_keys.index(current_sel) if current_sel in student_keys else 0
            new_sel = st.selectbox(
                "Active Student",
                student_keys,
                format_func=lambda k: DEMO_STUDENTS[k],
                index=idx,
                label_visibility="collapsed",
                key="demo_student_picker",
            )
            if new_sel != current_sel:
                st.session_state.demo_selected_student_id = new_sel
                st.session_state.current_student_profile = database.get_student_by_student_id(new_sel)
                st.rerun()

    elif is_coordinator():
        st.markdown(
            """
            <div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px;
                        padding: 10px 16px; margin-bottom: 12px; display: flex;
                        justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-weight: 700; color: #142B4A; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">
                        Coordinator Tour Mode
                    </span>
                    <span style="color: #475569; font-size: 13px; margin-left: 8px;">
                        Institutional administrative privileges. Re-seed clean dataset anytime in Demo Management.
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        current_prof = st.session_state.get("demo_selected_professor", "dr_kapoor")
        st.markdown(
            """
            <div style="background-color: #FEF3C7; border: 1px solid #FDE68A; border-radius: 8px;
                        padding: 10px 16px; margin-bottom: 12px; display: flex;
                        justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-weight: 700; color: #92400E; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">
                        Faculty Demo Mode
                    </span>
                    <span style="color: #78350F; font-size: 13px; margin-left: 8px;">
                        Grading and attendance entries update the synchronized database instance live.
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Interactive Professor Switcher
        c_label, c_sel = st.columns([1.2, 3.8])
        with c_label:
            st.markdown("<p style='margin-top:6px; font-weight:600; font-size:13px; color:#475569;'>Switch Faculty:</p>", unsafe_allow_html=True)
        with c_sel:
            prof_keys = list(DEMO_PROFESSORS.keys())
            idx = prof_keys.index(current_prof) if current_prof in prof_keys else 0
            new_prof = st.selectbox(
                "Active Faculty",
                prof_keys,
                format_func=lambda k: DEMO_PROFESSORS[k],
                index=idx,
                label_visibility="collapsed",
                key="demo_prof_picker",
            )
            if new_prof != current_prof:
                st.session_state.demo_selected_professor = new_prof
                st.rerun()
            new_prof = st.selectbox(
                "Active Faculty",
                prof_keys,
                format_func=lambda k: DEMO_PROFESSORS[k],
                index=idx,
                label_visibility="collapsed",
                key="demo_prof_picker",
            )
            if new_prof != current_prof:
                st.session_state.demo_selected_professor = new_prof
                st.rerun()
