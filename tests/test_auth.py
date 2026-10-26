"""
Tests for Password Hashing, Authentication, and User Account Registration.
"""

import pytest
import auth


def test_password_hashing_and_verification():
    """Verify PBKDF2 hashing produces salts and verifies correctly."""
    pwd = "MySecretPassword123"
    hashed = auth.hash_password(pwd)

    assert ":" in hashed
    assert auth.verify_password(pwd, hashed) is True
    assert auth.verify_password("WrongPassword", hashed) is False
    assert auth.verify_password("", hashed) is False


def test_user_registration_and_login(test_db_path):
    """Test full registration and authentication lifecycle."""
    # Register user
    ok, msg = auth.register_user("prof_smith", "SmithPass123", role="faculty", db_path=test_db_path)
    assert ok is True
    assert "successfully" in msg.lower()

    # Authenticate with valid credentials
    user = auth.authenticate_user("prof_smith", "SmithPass123", db_path=test_db_path)
    assert user is not None
    assert user["username"] == "prof_smith"
    assert user["role"] == "faculty"

    # Authenticate with wrong password
    bad_user = auth.authenticate_user("prof_smith", "IncorrectPassword", db_path=test_db_path)
    assert bad_user is None

    # Authenticate non-existent user
    non_user = auth.authenticate_user("ghost_user", "AnyPassword", db_path=test_db_path)
    assert non_user is None


def test_duplicate_username_rejected(test_db_path):
    """Ensure duplicate usernames cannot register."""
    auth.register_user("admin_user", "AdminSecret123", db_path=test_db_path)
    ok, msg = auth.register_user("admin_user", "AnotherSecret123", db_path=test_db_path)
    assert ok is False
    assert "already taken" in msg.lower()


def test_username_and_password_validation():
    """Test validation constraints on usernames and passwords."""
    # Username too short
    ok, msg = auth.validate_username("ab")
    assert ok is False

    # Username valid
    ok, msg = auth.validate_username("valid_user.1")
    assert ok is True

    # Password too short
    ok, msg = auth.validate_password_strength("12345")
    assert ok is False

    # Password valid
    ok, msg = auth.validate_password_strength("123456")
    assert ok is True
