import sys
import getpass
from app import app
from models import db, User # <-- MODIFIED: Import db and User from models

def list_users():
    with app.app_context():
        users = User.query.all()
        if not users:
            print("No users found in the database.")
            return
        
        print("--- Current Store Managers ---")
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}")
        print("------------------------------")

def create_manager():
    with app.app_context():
        print("--- Create a New Store Manager ---")
        username = input("Enter username: ").strip()
        if not username:
            print("Error: Username cannot be empty.")
            return
        if User.query.filter_by(username=username).first():
            print(f"Error: User '{username}' already exists.")
            return
        password = getpass.getpass("Enter password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        if not password or password != confirm_password:
            print("Error: Passwords do not match or are empty.")
            return
        new_manager = User(username=username, password=password)
        db.session.add(new_manager)
        db.session.commit()
        print(f"✅ Success! Manager '{username}' has been created.")

def delete_manager():
    with app.app_context():
        print("--- Delete a Store Manager ---")
        username_to_delete = input("Enter the username of the manager to delete: ").strip()
        user = User.query.filter_by(username=username_to_delete).first()
        if not user:
            print(f"Error: User '{username_to_delete}' not found.")
            return
        confirm = input(f"Are you sure you want to PERMANENTLY DELETE user '{user.username}' (ID: {user.id})? [y/N]: ").lower()
        if confirm == 'y':
            db.session.delete(user)
            db.session.commit()
            print(f"✅ Success! User '{username_to_delete}' has been deleted.")
        else:
            print("Deletion cancelled.")

def print_usage():
    print("Usage: python manage_users.py [command]")
    print("Commands:")
    print("  list    - View all current managers")
    print("  create  - Create a new manager")
    print("  delete  - Delete an existing manager")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    command = sys.argv[1].lower()
    if command == 'list':
        list_users()
    elif command == 'create':
        create_manager()
    elif command == 'delete':
        delete_manager()
    else:
        print(f"Error: Unknown command '{command}'")
        print_usage()