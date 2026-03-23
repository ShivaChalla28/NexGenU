import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or "nexgenu_secret_key"

    # Database configuration - SQLite for development, can be overridden for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or "sqlite:///instance/nexgenu.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Additional production settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = os.environ.get('FLASK_TESTING', 'False').lower() == 'true'

    # Serverless environment detection
    IS_SERVERLESS = os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
