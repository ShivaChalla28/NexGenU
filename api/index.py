import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment variable for Vercel
os.environ['VERCEL'] = 'true'

try:
    from app import app
except Exception as e:
    print(f"Error importing app: {e}")
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def error_handler():
        return jsonify({'error': 'Failed to import main app', 'message': str(e)}), 500

# Export the Flask WSGI application
application = app