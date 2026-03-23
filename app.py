from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from config import Config
from database import db
from models import User, Profile, Course, Enrollment, Exam, ExamScore, Job, Internship, Application, Certificate, StartupIdea, Project, ParentChildLink, Workshop, WorkshopAttendance, PreRegistrationQuery

app = Flask(__name__)
app.config.from_object(Config)

# Disable database initialization on Vercel
if os.environ.get('VERCEL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = None

try:
    db.init_app(app)
except Exception as e:
    print(f"Database initialization error: {e}")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

# Import routes
try:
    from routes.auth import auth
    from routes.student import student_bp
    from routes.parent import parent_bp
    from routes.college import college_bp

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(parent_bp, url_prefix='/parent')
    app.register_blueprint(college_bp, url_prefix='/college')
except Exception as e:
    print(f"Error importing routes: {e}")

# Simple health check endpoint that doesn't require database
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'NexGenU',
        'message': 'Application is running'
    }), 200

@app.route('/')
def home():
    try:
        # Get dynamic stats
        student_count = User.query.filter_by(role='student').count()
        college_count = User.query.filter_by(role='college').count()
        return render_template('home.html', student_count=student_count, college_count=college_count)
    except Exception as e:
        print(f"Error in home route: {e}")
        return jsonify({'error': 'Error loading home page', 'message': str(e)}), 500

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/create-sample-data')
def create_sample_data():
    with app.app_context():
        try:
            # Create sample courses
            if Course.query.count() == 0:
                courses = [
                    Course(name="Data Structures", description="Learn fundamental data structures", category="CSE"),
                    Course(name="Machine Learning", description="Introduction to ML algorithms", category="CSE"),
                    Course(name="Digital Electronics", description="Digital circuit design", category="ECE"),
                    Course(name="Thermodynamics", description="Engineering thermodynamics", category="MECH"),
                    Course(name="Power Systems", description="Electrical power systems", category="EEE"),
                    Course(name="Web Development", description="Full-stack web development", category="CSE"),
                    Course(name="Database Management", description="SQL and NoSQL databases", category="CSE"),
                ]
                for course in courses:
                    db.session.add(course)
                db.session.commit()
                print("Sample courses created")

            # Create sample users (only if no users exist)
            if User.query.count() == 0:
                # Create students
                students_data = [
                    {"name": "Alice Johnson", "email": "alice@nexgenu.com", "unique_id": "241001CSE001NEXG"},
                    {"name": "Bob Smith", "email": "bob@nexgenu.com", "unique_id": "241002CSE002NEXG"},
                    {"name": "Charlie Brown", "email": "charlie@nexgenu.com", "unique_id": "241003ECE001NEXG"},
                    {"name": "Diana Prince", "email": "diana@nexgenu.com", "unique_id": "241004MECH001NEXG"},
                ]
                
                students = []
                for student_data in students_data:
                    student = User(
                        name=student_data["name"], 
                        email=student_data["email"], 
                        password=generate_password_hash("password"),
                        role="student", 
                        unique_id=student_data["unique_id"]
                    )
                    db.session.add(student)
                    students.append(student)
                
                # Create parents
                parents_data = [
                    {"name": "John Johnson", "email": "john.johnson@nexgenu.com"},
                    {"name": "Mary Smith", "email": "mary.smith@nexgenu.com"},
                ]
                
                parents = []
                for parent_data in parents_data:
                    parent = User(
                        name=parent_data["name"], 
                        email=parent_data["email"], 
                        password=generate_password_hash("password"),
                        role="parent"
                    )
                    db.session.add(parent)
                    parents.append(parent)
                
                # Create colleges
                colleges_data = [
                    {"name": "ABC Engineering College", "email": "admin@abc.edu"},
                    {"name": "XYZ Technical Institute", "email": "admin@xyz.edu"},
                ]
                
                colleges = []
                for college_data in colleges_data:
                    college = User(
                        name=college_data["name"], 
                        email=college_data["email"], 
                        password=generate_password_hash("password"),
                        role="college"
                    )
                    db.session.add(college)
                    colleges.append(college)
                
                db.session.commit()
                print("Sample users created")

            # Get existing users or newly created ones
            students = User.query.filter_by(role="student").all()
            parents = User.query.filter_by(role="parent").all()
            colleges = User.query.filter_by(role="college").all()
            
            # Ensure we have enough sample users for demonstration
            if len(students) < 4:
                # Create additional students
                additional_students = [
                    {"name": "Alice Johnson", "email": f"alice{len(students)}@nexgenu.com", "unique_id": f"241001CSE00{len(students)+1}NEXG"},
                    {"name": "Bob Smith", "email": f"bob{len(students)}@nexgenu.com", "unique_id": f"241002CSE00{len(students)+2}NEXG"},
                    {"name": "Charlie Brown", "email": f"charlie{len(students)}@nexgenu.com", "unique_id": f"241003ECE00{len(students)+1}NEXG"},
                    {"name": "Diana Prince", "email": f"diana{len(students)}@nexgenu.com", "unique_id": f"241004MECH00{len(students)+1}NEXG"},
                ]
                
                for i in range(4 - len(students)):
                    student = User(
                        name=additional_students[i]["name"], 
                        email=additional_students[i]["email"], 
                        password=generate_password_hash("password"),
                        role="student", 
                        unique_id=additional_students[i]["unique_id"]
                    )
                    db.session.add(student)
                    students.append(student)
                
                db.session.commit()
                print("Additional sample students created")
            
            if len(parents) < 2:
                # Create additional parents
                additional_parents = [
                    {"name": "John Johnson", "email": f"john{len(parents)}@nexgenu.com"},
                    {"name": "Mary Smith", "email": f"mary{len(parents)}@nexgenu.com"},
                ]
                
                for i in range(2 - len(parents)):
                    parent = User(
                        name=additional_parents[i]["name"], 
                        email=additional_parents[i]["email"], 
                        password=generate_password_hash("password"),
                        role="parent"
                    )
                    db.session.add(parent)
                    parents.append(parent)
                
                db.session.commit()
                print("Additional sample parents created")
            
            if len(colleges) < 2:
                # Create additional colleges
                additional_colleges = [
                    {"name": "ABC Engineering College", "email": f"admin{len(colleges)}@abc.edu"},
                    {"name": "XYZ Technical Institute", "email": f"admin{len(colleges)}@xyz.edu"},
                ]
                
                for i in range(2 - len(colleges)):
                    college = User(
                        name=additional_colleges[i]["name"], 
                        email=additional_colleges[i]["email"], 
                        password=generate_password_hash("password"),
                        role="college"
                    )
                    db.session.add(college)
                    colleges.append(college)
                
                db.session.commit()
                print("Additional sample colleges created")
            courses = Course.query.all()

            # Create sample profiles
            if Profile.query.count() == 0:
                profiles_data = [
                    {
                        "user_id": students[0].id,
                        "branch": "CSE",
                        "college": "ABC Engineering College",
                        "college_roll_number": "CSE001",
                        "mobile_number": "9876543210",
                        "parents_mobile": "9876543211",
                        "state": "Karnataka",
                        "analytic_score": 85,
                        "language_proficiency": 0.8,
                        "backlogs": 0,
                        "attendance_percentage": 92.5,
                        "mentor_name": "Dr. Sarah Johnson",
                        "mentor_email": "sarah.johnson@abc.edu",
                        "mentor_phone": "+91-9876543210",
                        "principal_name": "Dr. Robert Wilson",
                        "hod_name": "Prof. Michael Davis",
                        "admin_contact": "admin@abc.edu"
                    },
                    {
                        "user_id": students[1].id,
                        "branch": "CSE",
                        "college": "ABC Engineering College", 
                        "college_roll_number": "CSE002",
                        "mobile_number": "9876543212",
                        "parents_mobile": "9876543213",
                        "state": "Maharashtra",
                        "analytic_score": 78,
                        "language_proficiency": 0.7,
                        "backlogs": 1,
                        "attendance_percentage": 85.0,
                        "mentor_name": "Dr. Sarah Johnson",
                        "mentor_email": "sarah.johnson@abc.edu",
                        "mentor_phone": "+91-9876543210",
                        "principal_name": "Dr. Robert Wilson",
                        "hod_name": "Prof. Michael Davis",
                        "admin_contact": "admin@abc.edu"
                    },
                    {
                        "user_id": students[2].id,
                        "branch": "ECE",
                        "college": "XYZ Technical Institute",
                        "college_roll_number": "ECE001", 
                        "mobile_number": "9876543214",
                        "parents_mobile": "9876543215",
                        "state": "Tamil Nadu",
                        "analytic_score": 92,
                        "language_proficiency": 0.9,
                        "backlogs": 0,
                        "attendance_percentage": 95.2,
                        "mentor_name": "Prof. Lisa Chen",
                        "mentor_email": "lisa.chen@xyz.edu",
                        "mentor_phone": "+91-9876543211",
                        "principal_name": "Dr. James Anderson",
                        "hod_name": "Prof. Emily Rodriguez",
                        "admin_contact": "admin@xyz.edu"
                    },
                    {
                        "user_id": students[3].id,
                        "branch": "MECH",
                        "college": "XYZ Technical Institute",
                        "college_roll_number": "MECH001",
                        "mobile_number": "9876543216", 
                        "parents_mobile": "9876543217",
                        "state": "Gujarat",
                        "analytic_score": 88,
                        "language_proficiency": 0.85,
                        "backlogs": 2,
                        "attendance_percentage": 78.5,
                        "mentor_name": "Prof. David Kumar",
                        "mentor_email": "david.kumar@xyz.edu",
                        "mentor_phone": "+91-9876543212",
                        "principal_name": "Dr. James Anderson",
                        "hod_name": "Prof. Mark Thompson",
                        "admin_contact": "admin@xyz.edu"
                    },
                ]
                
                for profile_data in profiles_data:
                    profile = Profile(**profile_data)
                    db.session.add(profile)
                
                db.session.commit()
                print("Sample profiles created")

            # Create sample enrollments
            if Enrollment.query.count() == 0:
                enrollments_data = [
                    {"user_id": students[0].id, "course_id": courses[0].id},  # Alice in Data Structures
                    {"user_id": students[0].id, "course_id": courses[1].id},  # Alice in ML
                    {"user_id": students[1].id, "course_id": courses[0].id},  # Bob in Data Structures
                    {"user_id": students[1].id, "course_id": courses[5].id},  # Bob in Web Dev
                    {"user_id": students[2].id, "course_id": courses[2].id},  # Charlie in Digital Electronics
                    {"user_id": students[3].id, "course_id": courses[3].id},  # Diana in Thermodynamics
                ]
                
                for enrollment_data in enrollments_data:
                    enrollment = Enrollment(**enrollment_data)
                    db.session.add(enrollment)
                
                db.session.commit()
                print("Sample enrollments created")

            # Create sample exams
            if Exam.query.count() == 0:
                exams_data = [
                    {
                        "title": "Data Structures Quiz 1",
                        "type": "weekly",
                        "questions": '{"q1": "What is a stack?", "q2": "What is a queue?", "q3": "Explain linked list"}'
                    },
                    {
                        "title": "Machine Learning Fundamentals",
                        "type": "monthly", 
                        "questions": '{"q1": "What is supervised learning?", "q2": "What is unsupervised learning?", "q3": "Explain neural networks"}'
                    },
                    {
                        "title": "Digital Electronics Test",
                        "type": "weekly",
                        "questions": '{"q1": "What is a logic gate?", "q2": "Explain flip-flops", "q3": "What is Boolean algebra?"}'
                    },
                ]
                
                exams = []
                for exam_data in exams_data:
                    exam = Exam(**exam_data)
                    db.session.add(exam)
                    exams.append(exam)
                
                db.session.commit()
                print("Sample exams created")

            # Get exams
            exams = Exam.query.all()

            # Create sample exam scores
            if ExamScore.query.count() == 0:
                exam_scores_data = [
                    {"user_id": students[0].id, "exam_id": exams[0].id, "score": 85},
                    {"user_id": students[0].id, "exam_id": exams[1].id, "score": 78},
                    {"user_id": students[1].id, "exam_id": exams[0].id, "score": 92},
                    {"user_id": students[2].id, "exam_id": exams[2].id, "score": 88},
                ]
                
                for score_data in exam_scores_data:
                    score = ExamScore(**score_data)
                    db.session.add(score)
                
                db.session.commit()
                print("Sample exam scores created")

            # Create sample jobs
            if Job.query.count() == 0:
                jobs_data = [
                    {
                        "title": "Software Engineer",
                        "company": "Tech Corp",
                        "location": "Bangalore",
                        "requirements": "B.Tech in CSE, 2+ years experience",
                        "min_score": 75
                    },
                    {
                        "title": "Data Analyst", 
                        "company": "Data Inc",
                        "location": "Mumbai",
                        "requirements": "Statistics background, Python skills",
                        "min_score": 70
                    },
                    {
                        "title": "Embedded Systems Engineer",
                        "company": "Electronics Solutions",
                        "location": "Chennai", 
                        "requirements": "B.Tech in ECE, C/C++ programming",
                        "min_score": 80
                    },
                    {
                        "title": "Mechanical Design Engineer",
                        "company": "AutoTech",
                        "location": "Pune",
                        "requirements": "B.Tech in Mechanical, CAD experience",
                        "min_score": 75
                    },
                ]
                
                jobs = []
                for job_data in jobs_data:
                    job = Job(**job_data)
                    db.session.add(job)
                    jobs.append(job)
                
                db.session.commit()
                print("Sample jobs created")

            # Get jobs
            jobs = Job.query.all()

            # Create sample internships
            if Internship.query.count() == 0:
                internships_data = [
                    {
                        "title": "Web Development Intern",
                        "company": "Web Solutions",
                        "branch": "CSE",
                        "duration": "6 months"
                    },
                    {
                        "title": "ML Research Intern",
                        "company": "AI Labs", 
                        "branch": "CSE",
                        "duration": "3 months"
                    },
                    {
                        "title": "Embedded Systems Intern",
                        "company": "IoT Solutions",
                        "branch": "ECE", 
                        "duration": "4 months"
                    },
                ]
                
                internships = []
                for internship_data in internships_data:
                    internship = Internship(**internship_data)
                    db.session.add(internship)
                    internships.append(internship)
                
                db.session.commit()
                print("Sample internships created")

            # Get internships
            internships = Internship.query.all()

            # Create sample applications
            if Application.query.count() == 0:
                applications_data = [
                    {"user_id": students[0].id, "job_id": jobs[0].id, "status": "pending"},
                    {"user_id": students[0].id, "internship_id": internships[0].id, "status": "accepted"},
                    {"user_id": students[1].id, "job_id": jobs[1].id, "status": "pending"},
                    {"user_id": students[2].id, "internship_id": internships[2].id, "status": "pending"},
                    {"user_id": students[3].id, "job_id": jobs[3].id, "status": "rejected"},
                ]
                
                for app_data in applications_data:
                    application = Application(**app_data)
                    db.session.add(application)
                
                db.session.commit()
                print("Sample applications created")

            # Create sample projects
            if Project.query.count() == 0:
                projects_data = [
                    {
                        "user_id": students[0].id,
                        "title": "E-Learning Platform",
                        "description": "A web-based learning management system",
                        "category": "CSE",
                        "status": "submitted",
                        "file_path": "/uploads/projects/elearning.zip",
                        "verified_by": colleges[0].id,
                        "verification_date": datetime.utcnow(),
                        "feedback": "Excellent project! Well implemented."
                    },
                    {
                        "user_id": students[1].id,
                        "title": "Data Analysis Dashboard",
                        "description": "Interactive dashboard for data visualization",
                        "category": "CSE", 
                        "status": "draft",
                        "file_path": "/uploads/projects/dashboard.zip"
                    },
                    {
                        "user_id": students[2].id,
                        "title": "IoT Home Automation",
                        "description": "Smart home system using Arduino",
                        "category": "ECE",
                        "status": "verified",
                        "file_path": "/uploads/projects/iot_home.zip",
                        "verified_by": colleges[1].id,
                        "verification_date": datetime.utcnow(),
                        "feedback": "Good hardware implementation."
                    },
                ]
                
                for project_data in projects_data:
                    project = Project(**project_data)
                    db.session.add(project)
                
                db.session.commit()
                print("Sample projects created")

            # Create sample startup ideas
            if StartupIdea.query.count() == 0:
                startup_ideas_data = [
                    {
                        "user_id": students[0].id,
                        "title": "EduTech Platform",
                        "description": "Online education platform for rural areas",
                        "category": "Education",
                        "status": "draft"
                    },
                    {
                        "user_id": students[1].id,
                        "title": "AgriTech Solution",
                        "description": "Smart farming using IoT sensors",
                        "category": "Agriculture", 
                        "status": "submitted"
                    },
                    {
                        "user_id": students[2].id,
                        "title": "Health Monitor App",
                        "description": "Mobile app for health tracking",
                        "category": "Healthcare",
                        "status": "draft"
                    },
                ]
                
                for idea_data in startup_ideas_data:
                    idea = StartupIdea(**idea_data)
                    db.session.add(idea)
                
                db.session.commit()
                print("Sample startup ideas created")

            # Create sample certificates
            if Certificate.query.count() == 0:
                certificates_data = [
                    {
                        "user_id": students[0].id,
                        "title": "Python Programming",
                        "issued_at": datetime.utcnow(),
                    },
                    {
                        "user_id": students[0].id,
                        "title": "Machine Learning",
                        "issued_at": datetime.utcnow(),
                    },
                    {
                        "user_id": students[1].id,
                        "title": "Data Science",
                        "issued_at": datetime.utcnow(),
                    },
                ]
                
                for cert_data in certificates_data:
                    certificate = Certificate(**cert_data)
                    db.session.add(certificate)
                
                db.session.commit()
                print("Sample certificates created")

            # Create sample workshops
            if Workshop.query.count() == 0:
                workshops_data = [
                    {
                        "title": "Career Guidance Workshop",
                        "description": "Learn about career opportunities in tech",
                        "date": datetime.utcnow() + timedelta(days=7),
                        "branch": "CSE",
                    },
                    {
                        "title": "Entrepreneurship Workshop",
                        "description": "Start your own business journey",
                        "date": datetime.utcnow() + timedelta(days=14),
                        "branch": "General",
                    },
                    {
                        "title": "Technical Skills Workshop",
                        "description": "Advanced programming techniques",
                        "date": datetime.utcnow() + timedelta(days=21),
                        "branch": "CSE",
                    },
                ]
                
                workshops = []
                for workshop_data in workshops_data:
                    workshop = Workshop(**workshop_data)
                    db.session.add(workshop)
                    workshops.append(workshop)
                
                db.session.commit()
                print("Sample workshops created")

            # Get workshops
            workshops = Workshop.query.all()

            # Create sample workshop attendance
            if WorkshopAttendance.query.count() == 0:
                attendance_data = [
                    {"user_id": students[0].id, "workshop_id": workshops[0].id},
                    {"user_id": students[0].id, "workshop_id": workshops[1].id},
                    {"user_id": students[1].id, "workshop_id": workshops[0].id},
                    {"user_id": students[2].id, "workshop_id": workshops[2].id},
                ]
                
                for attendance in attendance_data:
                    workshop_attendance = WorkshopAttendance(**attendance)
                    db.session.add(workshop_attendance)
                
                db.session.commit()
                print("Sample workshop attendance created")

            # Create parent-child links
            if ParentChildLink.query.count() == 0:
                parent_child_links = [
                    {"parent_id": parents[0].id, "child_id": students[0].id},
                    {"parent_id": parents[1].id, "child_id": students[1].id},
                ]
                
                for link_data in parent_child_links:
                    link = ParentChildLink(**link_data)
                    db.session.add(link)
                
                db.session.commit()
                print("Sample parent-child links created")

            # Create sample pre-registration queries
            if PreRegistrationQuery.query.count() == 0:
                queries_data = [
                    {
                        "name": "Raj Kumar",
                        "email": "raj@example.com",
                        "phone": "+91-9876543210",
                        "message": "Interested in computer science courses"
                    },
                    {
                        "name": "Priya Sharma", 
                        "email": "priya@example.com",
                        "phone": "+91-9876543211",
                        "message": "Want to know about admission process"
                    },
                ]
                
                for query_data in queries_data:
                    query = PreRegistrationQuery(**query_data)
                    db.session.add(query)
                
                db.session.commit()
                print("Sample pre-registration queries created")

            db.session.commit()
            return "Comprehensive sample data created successfully!"

        except Exception as e:
            db.session.rollback()
            return f"Error creating sample data: {str(e)}"

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"App startup error: {e}")
