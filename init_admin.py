"""
Initial Administrator Setup CLI Utility.
Allows creation of the first administrator account safely without hardcoding credentials.
Usage:
    python init_admin.py
    python init_admin.py --username admin --password MySecurePassword123
"""

import sys
import argparse
import getpass
import database
from auth import register_user


def main():
    parser = argparse.ArgumentParser(description="Create initial administrator account.")
    parser.add_argument("--username", help="Administrator username")
    parser.add_argument("--password", help="Administrator password")
    parser.add_argument("--role", default="admin", choices=["admin", "coordinator"], help="Administrative role")
    args = parser.parse_args()

    database.init_db()

    username = args.username
    password = args.password
    role = args.role

    if not username:
        username = input("Enter administrator username (e.g., admin): ").strip()

    if not password:
        password = getpass.getpass("Enter administrator password (min 6 characters): ")
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Error: Passwords do not match.")
            sys.exit(1)

    success, msg = register_user(username=username, password=password, role=role)
    if success:
        print(f"Success: {msg}")
    else:
        print(f"Error: {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
