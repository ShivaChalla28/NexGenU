#!/usr/bin/env python3
"""
Database connection test for NexGenU
"""

from app import app, db
from models import User

def test_database_connection():
    """Test database connection and basic queries"""
    with app.app_context():
        try:
            # Test basic connection with a simple query
            from sqlalchemy import text
            result = db.session.execute(text("SELECT 1"))
            print("✅ Database connection successful!")

            # Test user count
            user_count = User.query.count()
            print(f"✅ Found {user_count} users in database")

            # Test a simple query
            users = User.query.limit(3).all()
            print(f"✅ Sample users: {[user.name for user in users]}")

            print("🎉 All database tests passed!")

        except Exception as e:
            print(f"❌ Database error: {e}")
            return False

    return True

if __name__ == "__main__":
    test_database_connection()