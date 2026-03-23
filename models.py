from database import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')  # student, admin, college, parent
    score = db.Column(db.Integer, default=0)
    student_id = db.Column(db.String(20), unique=True)
    unique_id = db.Column(db.String(20), unique=True)  # For students: YYNNNNEEEE + NEXG
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False)
    enrollments = db.relationship('Enrollment', backref='user', lazy=True)
    exam_scores = db.relationship('ExamScore', backref='user', lazy=True)
    applications = db.relationship('Application', backref='user', lazy=True)
    projects = db.relationship('Project', foreign_keys='Project.user_id', lazy=True)
    verified_projects = db.relationship('Project', foreign_keys='Project.verified_by', lazy=True)
    certificates = db.relationship('Certificate', backref='user', lazy=True)
    startup_ideas = db.relationship('StartupIdea', backref='user', lazy=True)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    # Parent-child relationships
    parent_links = db.relationship('ParentChildLink', foreign_keys='ParentChildLink.parent_id', backref='parent', lazy=True)
    child_links = db.relationship('ParentChildLink', foreign_keys='ParentChildLink.child_id', backref='child', lazy=True)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    behavior = db.Column(db.Text, default='GOOD')  # GOOD or BAD
    mentor_name = db.Column(db.String(100))
    mentor_email = db.Column(db.String(120))
    mentor_phone = db.Column(db.String(20))
    branch = db.Column(db.String(50))  # CSE, ECE, MECH, EEE
    college = db.Column(db.String(100))
    college_roll_number = db.Column(db.String(20))
    mobile_number = db.Column(db.String(15))
    parents_mobile = db.Column(db.String(15))
    state = db.Column(db.String(50))
    principal_name = db.Column(db.String(100))
    principal_email = db.Column(db.String(120))
    hod_name = db.Column(db.String(100))
    hod_email = db.Column(db.String(120))
    admin_contact = db.Column(db.String(100))
    analytic_score = db.Column(db.Integer, default=0)  # 0-100
    language_proficiency = db.Column(db.Float, default=0.0)  # percentage
    backlogs = db.Column(db.Integer, default=0)  # Number of backlogs
    attendance_percentage = db.Column(db.Float, default=0.0)  # Attendance percentage

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    enrollments = db.relationship('Enrollment', backref='course', lazy=True)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(20))  # daily, weekly, monthly
    questions = db.Column(db.Text)  # JSON string of questions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    scores = db.relationship('ExamScore', backref='exam', lazy=True)

class ExamScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    company = db.Column(db.String(100))
    location = db.Column(db.String(100))
    requirements = db.Column(db.Text)
    min_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='job', lazy=True)

class Internship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    company = db.Column(db.String(100))
    branch = db.Column(db.String(50))  # CSE, ECE, etc.
    duration = db.Column(db.String(50))
    requirements = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='internship', lazy=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=True)
    internship_id = db.Column(db.Integer, db.ForeignKey('internship.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)

class StartupIdea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    stage = db.Column(db.String(20), default='concept')  # concept, prototype, mvp, beta, launched
    status = db.Column(db.String(20), default='submitted')  # submitted, under_review, approved, rejected
    mentor_feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # CSE, ECE, MECH, etc.
    status = db.Column(db.String(20), default='draft')  # draft, submitted, verified, rejected
    file_path = db.Column(db.String(500))  # Path to uploaded file
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    verification_date = db.Column(db.DateTime)
    feedback = db.Column(db.Text)
    verified_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Admin who verified

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], overlaps="projects,verified_projects")
    verifier = db.relationship('User', foreign_keys=[verified_by], overlaps="projects,verified_projects")

class PreRegistrationQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan = db.Column(db.String(20), nullable=False)  # monthly, yearly, 3year, 4year
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, expired, cancelled
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    payment_id = db.Column(db.String(100))  # For payment tracking

class ParentChildLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    linked_at = db.Column(db.DateTime, default=datetime.utcnow)

class Workshop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    branch = db.Column(db.String(50))  # CSE, ECE, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WorkshopAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshop.id'), nullable=False)
    attended_at = db.Column(db.DateTime, default=datetime.utcnow)