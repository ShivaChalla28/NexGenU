#!/usr/bin/env python3
"""
Database initialization script for NexGenU
"""

from app import app, db
from models import User, Profile, Course, Enrollment, Exam, ExamScore, Job, Internship, Application, Certificate, StartupIdea, Project, ParentChildLink, Workshop, WorkshopAttendance, PreRegistrationQuery

def init_database():
    """Initialize the database and create all tables"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")

        # Check if we have any users
        user_count = User.query.count()
        print(f"Current user count: {user_count}")

        if user_count == 0:
            print("Database is empty. You can run /create-sample-data to populate it.")
        else:
            print("Database already has data.")

if __name__ == "__main__":
    init_database()