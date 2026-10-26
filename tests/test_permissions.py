"""
Tests for Permissions, Role-Based Access Control, and Demo Mode Safeguards.
"""

import pytest
import streamlit as st
import permissions
import auth
from config import ROLE_STUDENT, ROLE_PROFESSOR, ROLE_DEMO


def test_unauthenticated_session_state():
    """Verify default session state is unauthenticated."""
    auth.logout()
    assert permissions.is_authenticated() is False
    assert permissions.is_demo_mode() is False
    assert permissions.get_current_user() is None


def test_student_role_checks():
    """Verify student role detection."""
    auth.login_user({"id": 1, "username": "stu_alice", "role": "student"})
    assert permissions.is_authenticated() is True
    assert permissions.is_student() is True
    assert permissions.is_professor() is False
    assert permissions.is_demo_mode() is False


def test_professor_role_checks():
    """Verify professor role detection."""
    auth.login_user({"id": 2, "username": "prof_jones", "role": "professor"})
    assert permissions.is_authenticated() is True
    assert permissions.is_student() is False
    assert permissions.is_professor() is True


def test_demo_session_safeguards():
    """Verify demo mode sets demo indicators and triggers mutation block."""
    auth.start_demo_session("demo_student")
    assert permissions.is_authenticated() is True
    assert permissions.is_demo_mode() is True
    assert permissions.is_student() is True
    assert permissions.is_professor() is False

    # Prevent demo mutation should return True
    blocked = permissions.prevent_demo_mutation()
    assert blocked is True

    # Switch to professor demo: professors can update demo records to demonstrate synchronization
    auth.start_demo_session("demo_professor")
    assert permissions.is_demo_mode() is True
    assert permissions.is_student() is False
    assert permissions.is_professor() is True
    # Professor demo allows updates to sync with student dashboard
    assert permissions.prevent_demo_mutation() is False

    # Switch back to student demo: students are strictly read-only
    auth.start_demo_session("demo_student")
    assert permissions.prevent_demo_mutation() is True


def test_student_isolation(test_db_path):
    """Ensure student access guard only permits their own records."""
    auth.login_user({"id": 10, "username": "alice", "role": "student"})
    st.session_state.current_student_profile = {"id": 10, "student_id": "STU101"}

    assert permissions.can_access_student("STU101") is True
    assert permissions.can_access_student("STU102") is False

    # Professors can access any student
    auth.login_user({"id": 20, "username": "prof", "role": "professor"})
    assert permissions.can_access_student("STU101") is True
    assert permissions.can_access_student("STU102") is True
