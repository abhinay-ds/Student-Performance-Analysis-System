"""
Initial Academic Coordinator Setup CLI Utility.
Allows creation or password reset of the Academic Coordinator account safely.

Usage:
    python init_coordinator.py
    python init_coordinator.py --username coordinator --password MyCoordPassword123
"""

import sys
import argparse
import getpass
import database
from auth import register_user, hash_password


def main():
    parser = argparse.ArgumentParser(description="Create or configure initial Coordinator account.")
    parser.add_argument("--username", default="coordinator", help="Coordinator username")
    parser.add_argument("--password", help="Coordinator password")
    args = parser.parse_args()

    database.init_db()

    username = args.username.strip()
    password = args.password

    if not username:
        username = input("Enter coordinator username (e.g., coordinator): ").strip()

    if not password:
        password = getpass.getpass("Enter coordinator password (min 6 characters): ")
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Error: Passwords do not match.")
            sys.exit(1)

    # Check if user already exists
    existing = database.get_user_by_username(username)
    if existing:
        # Reset password
        h = hash_password(password)
        with database.get_db() as conn:
            conn.execute("UPDATE users SET password_hash = ?, role = 'coordinator', is_active = 1 WHERE id = ?", (h, existing["id"]))
        print(f"Success: Existing account '{username}' updated to active Coordinator with new password.")
    else:
        success, msg = register_user(username=username, password=password, role="coordinator")
        if success:
            print(f"Success: {msg}")
        else:
            print(f"Error: {msg}")
            sys.exit(1)


if __name__ == "__main__":
    main()
