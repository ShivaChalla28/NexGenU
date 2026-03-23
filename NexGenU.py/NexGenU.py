from flask import Flask, request, redirect, session
import sqlite3
import random

app = Flask(__name__)
app.secret_key = "nexgenu_secret_key"

# ---------- DATABASE ----------
def init_db():
    db = sqlite3.connect("database.db")
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            score INTEGER
        )
    """)
    db.commit()
    db.close()

# ---------- HOME ----------
@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>NEXGENU</title>
        <style>
            body { background:#0f172a; color:white; font-family:Segoe UI; text-align:center; padding-top:80px; margin:0; }
            .btn { background:#00f2ff; color:#000; padding:12px 24px; text-decoration:none; border-radius:25px; font-size:18px; margin:10px; display:inline-block; }
            h1 { font-size:3em; margin-bottom:20px; }
            .stats { font-size:24px; margin:20px 0; }
        </style>
    </head>
    <body>
        <h1>🚀 NEXGENU – EduTech Platform</h1>
        <div class="stats">
            <p>Students Registered: 12,000+</p>
            <p>Colleges Registered: 150+</p>
        </div>
        <br>
        <a href="/register" class="btn">Register Now</a>
        <a href="/login" class="btn">Student Login</a>
    </body>
    </html>
    """

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        score = random.randint(40, 95)

        try:
            db = sqlite3.connect("database.db")
            db.execute(
                "INSERT INTO users (name, email, score) VALUES (?, ?, ?)",
                (name, email, score)
            )
            db.commit()
            db.close()
            return redirect("/login")
        except sqlite3.IntegrityError:
            db.close()
            return """
            <html><body style="background:#020617;color:white;font-family:Segoe UI;text-align:center;padding-top:120px">
                <h2>❌ Email already registered!</h2>
                <a href="/register" style="color:#00f2ff;font-size:20px">Try Again</a> |
                <a href="/login" style="color:#00f2ff;font-size:20px">Go to Login</a>
            </body></html>
            """

    return """
    <html>
    <head>
        <style>
            body { background:#020617; color:white; font-family:Segoe UI; text-align:center; padding-top:80px; }
            input { padding:15px; margin:10px; width:300px; border-radius:10px; border:none; font-size:16px; }
            button { background:#00f2ff; color:#000; padding:15px 40px; border:none; border-radius:25px; font-size:20px; cursor:pointer; }
        </style>
    </head>
    <body>
        <h2>👨‍🎓 Student Registration</h2>
        <form method="post">
            <input name="name" placeholder="Full Name" required><br>
            <input name="email" type="email" placeholder="Email ID" required><br>
            <button type="submit">🎯 Register</button>
        </form>
        <p><a href="/" style="color:#00f2ff">← Back to Home</a></p>
    </body>
    </html>
    """

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]

        db = sqlite3.connect("database.db")
        user = db.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()
        db.close()

        if user:
            session["email"] = email
            return redirect("/dashboard")
        else:
            return """
            <html><body style="background:#020617;color:white;font-family:Segoe UI;text-align:center;padding-top:120px">
                <h2>❌ Email not found!</h2>
                <p>Please register first</p>
                <a href="/register" style="color:#00f2ff;font-size:20px">Register Now</a>
            </body></html>
            """

    return """
    <html>
    <head>
        <style>
            body { background:#020617; color:white; font-family:Segoe UI; text-align:center; padding-top:80px; }
            input { padding:15px; margin:10px; width:300px; border-radius:10px; border:none; font-size:16px; }
            button { background:#00f2ff; color:#000; padding:15px 40px; border:none; border-radius:25px; font-size:20px; cursor:pointer; }
        </style>
    </head>
    <body>
        <h2>🔐 Student Login</h2>
        <form method="post">
            <input name="email" type="email" placeholder="Enter Email" required><br>
            <button type="submit">Login</button>
        </form>
        <p><a href="/register" style="color:#00f2ff">New User? Register</a></p>
    </body>
    </html>
    """

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "email" not in session:
        return redirect("/login")

    db = sqlite3.connect("database.db")
    user = db.execute(
        "SELECT * FROM users WHERE email=?",
        (session["email"],)
    ).fetchone()
    db.close()

    score = user[3]
    campus_status = "✅ ENABLED" if score >= 75 else "❌ DISABLED"

    return f"""
    <html>
    <head>
        <style>
            body {{ background:linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color:white; font-family:Segoe UI; padding:40px; margin:0; }}
            .container {{ max-width:1000px; margin:0 auto; }}
            .score-card {{ background:rgba(0,242,255,0.1); padding:30px; border-radius:20px; margin:20px 0; text-align:center; }}
            .btn {{ background:#00f2ff; color:#000; padding:12px 24px; text-decoration:none; border-radius:25px; font-size:16px; margin:5px; display:inline-block; }}
            .status {{ font-size:24px; padding:15px; border-radius:10px; display:inline-block; margin:10px 0; }}
            .enabled {{ background:#10b981; color:white; }}
            .disabled {{ background:#ef4444; color:white; }}
            ul {{ list-style:none; padding:0; }}
            li {{ background:rgba(255,255,255,0.1); margin:10px 0; padding:15px; border-radius:15px; cursor:pointer; }}
            li:hover {{ background:rgba(0,242,255,0.2); }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Welcome, {user[1]}!</h1>
            
            <div class="score-card">
                <h2>📊 Analytic Score: <span style="color:#00f2ff;font-size:2.5em;">{score}/100</span></h2>
                <div class="status {'enabled' if score >= 75 else 'disabled'}">{campus_status}</div>
            </div>

            <h3>📚 Student Dashboard</h3>
            <ul>
                <li>🎓 <strong>Courses</strong> - Full Stack, DSA, AI/ML</li>
                <li>🗣️ <strong>Language Improvement</strong> - English Fluency</li>
                <li>💼 <strong>Workshops</strong> - Resume & Interview Skills</li>
                <li>🏢 <strong>Internships</strong> - 500+ Companies</li>
                <li>⚙️ <strong>Projects</strong> - Live Portfolio Projects</li>
                <li>🏛️ <strong>Govt Jobs</strong> - SSC, UPSC, Railways</li>
            </ul>

            <br>
            <a href="/logout" class="btn">🚪 Logout</a>
        </div>
    </body>
    </html>
    """

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
