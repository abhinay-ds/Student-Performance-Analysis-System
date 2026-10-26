"""
Authentication, Credentials Verification, and Session Management.
Supports Student Login, Professor Login, Demo Sessions, and PBKDF2 Password Hashing.
"""

import hashlib
import hmac
import secrets
import re
from typing import Optional, Dict, Any, Tuple
import streamlit as st
import database
from config import PASSWORD_SALT_BYTES, PBKDF2_ITERATIONS, ROLE_STUDENT, ROLE_PROFESSOR, ROLE_COORDINATOR, ROLE_ADMIN, ROLE_DEMO


# ============================================================================
# Cryptographic Password Hashing
# ============================================================================

def hash_password(password: str) -> str:
    """Hash plaintext password using PBKDF2-HMAC-SHA256 with random salt."""
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Constant-time verification of password against stored salt:hash."""
    if not plain_password or not stored_hash or ":" not in stored_hash:
        return False
    try:
        salt_hex, key_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        candidate_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
        return hmac.compare_digest(candidate_key, expected_key)
    except Exception:
        return False


# ============================================================================
# User Registration and Authentication
# ============================================================================

def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format and length."""
    u = (username or "").strip()
    if len(u) < 3:
        return False, "Username must be at least 3 characters."
    if len(u) > 30:
        return False, "Username cannot exceed 30 characters."
    if not re.match(r"^[a-zA-Z0-9_.-]+$", u):
        return False, "Username may only contain letters, numbers, dots, hyphens, and underscores."
    return True, ""


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate password length and basic complexity."""
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters."
    return True, ""


def register_user(
    username: str,
    password: str,
    role: str = "student",
    db_path: Optional[str] = None,
) -> Tuple[bool, str]:
    """Register new user with hashed password."""
    u_ok, u_msg = validate_username(username)
    if not u_ok:
        return False, u_msg

    p_ok, p_msg = validate_password_strength(password)
    if not p_ok:
        return False, p_msg

    clean_user = username.strip()
    if database.get_user_by_username(clean_user, db_path=db_path):
        return False, f"Username '{clean_user}' is already taken."

    hashed = hash_password(password)
    try:
        database.create_user(clean_user, hashed, role=role, db_path=db_path)
        return True, f"User '{clean_user}' registered successfully."
    except Exception as e:
        return False, f"Registration failed: {str(e)}"


def authenticate_credentials(
    login_identifier: str,
    password: str,
    expected_role: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Authenticate against users table.
    Supports login by username OR student_id (for students).
    Optionally enforces expected role (e.g. 'professor', 'student').
    """
    ident = (login_identifier or "").strip()
    if not ident or not password:
        return None

    # Try lookup by username directly
    user = database.get_user_by_username(ident, db_path=db_path)

    # If not found and identifier might be a student_id, find linked user
    if not user:
        student = database.get_student_by_student_id(ident, db_path=db_path)
        if student and student.get("user_id"):
            user = database.get_user_by_id(student["user_id"], db_path=db_path)

    if not user or not user.get("is_active", 1):
        return None

    if verify_password(password, user["password_hash"]):
        # Verify role if requested
        if expected_role and user["role"] != expected_role and user["role"] != ROLE_ADMIN:
            if expected_role in [ROLE_COORDINATOR, ROLE_ADMIN] and user["role"] in [ROLE_COORDINATOR, ROLE_ADMIN]:
                pass
            else:
                return None
        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "created_at": user.get("created_at"),
        }

    return None


# Backward-compatible alias
authenticate_user = authenticate_credentials


# ============================================================================
# Session State Management
# ============================================================================

def init_session_state() -> None:
    """Initialize authentication session state keys."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "is_demo" not in st.session_state:
        st.session_state.is_demo = False
    if "demo_role" not in st.session_state:
        st.session_state.demo_role = None
    if "current_student_profile" not in st.session_state:
        st.session_state.current_student_profile = None


def login_user(user_dict: Dict[str, Any]) -> None:
    """Set authenticated session state."""
    init_session_state()
    st.session_state.authenticated = True
    st.session_state.is_demo = False
    st.session_state.current_user = user_dict
    st.session_state.demo_role = None
    st.session_state.current_student_profile = None


def start_demo_session(demo_role: str = "demo_student") -> None:
    """Initialize a safe read-only demo session."""
    init_session_state()
    st.session_state.authenticated = True
    st.session_state.is_demo = True
    st.session_state.demo_role = demo_role
    st.session_state.current_user = {
        "id": -99,
        "username": "demo_guest",
        "role": demo_role,
    }
    st.session_state.current_student_profile = None


def logout() -> None:
    """Clear all session credentials and reset portal state."""
    st.session_state.authenticated = False
    st.session_state.is_demo = False
    st.session_state.current_user = None
    st.session_state.demo_role = None
    st.session_state.current_student_profile = None


def render_sidebar_user_info() -> None:
    """Render authenticated user badge and logout button in the sidebar."""
    init_session_state()
    if st.session_state.authenticated:
        with st.sidebar:
            st.markdown("<hr style='border-color: #1E293B; margin: 18px 0 14px 0;'>", unsafe_allow_html=True)
            if st.session_state.get("is_demo"):
                demo_r = st.session_state.get("demo_role")
                if demo_r == "demo_student":
                    role_name = "Student Demo"
                    mode_desc = "Fictional Student Persona"
                    badge_color = "#38BDF8"
                elif demo_r == "demo_coordinator":
                    role_name = "Coordinator Tour"
                    mode_desc = "Full Administrative Access"
                    badge_color = "#A78BFA"
                else:
                    role_name = "Faculty Demo"
                    mode_desc = "Instructor Perspective"
                    badge_color = "#FBBF24"

                st.markdown(
                    f"""
                    <div style="background-color: #16243A; border: 1px solid #1E293B; border-radius: 6px; padding: 12px 14px; margin-bottom: 12px;">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <span style="font-size: 11px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px;">Demo Environment</span>
                            <span style="background-color: rgba(255,255,255,0.08); color: {badge_color}; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px;">
                                {role_name}
                            </span>
                        </div>
                        <p style="margin: 4px 0 0 0; font-size: 12px; color: #CBD5E1;">{mode_desc}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Exit Demo Mode", key="sidebar_exit_demo_btn", use_container_width=True, type="secondary"):
                    logout()
                    st.rerun()
            else:
                user = st.session_state.get("current_user", {})
                role_val = str(user.get("role", "Student")).capitalize()
                st.markdown(
                    f"""
                    <div style="background-color: #16243A; border: 1px solid #1E293B; border-radius: 6px; padding: 12px 14px; margin-bottom: 12px;">
                        <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #94A3B8; font-weight: 600;">Signed in as</span>
                        <div style="font-size: 14px; font-weight: 600; color: #F8FAFC; margin-top: 2px;">{user.get('username')}</div>
                        <div style="display: inline-block; background-color: rgba(37, 99, 235, 0.2); color: #93C5FD; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; margin-top: 6px;">
                            {role_val}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Sign Out", key="sidebar_logout_btn", use_container_width=True):
                    logout()
                    st.rerun()
