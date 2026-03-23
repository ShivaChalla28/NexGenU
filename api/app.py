from app import app

# Vercel expects the Flask app to be exported
app = app

if __name__ == "__main__":
    app.run()