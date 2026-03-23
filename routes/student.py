from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Profile, Course, Enrollment, Exam, ExamScore, Job, Internship, Application, Certificate, StartupIdea, Project, Workshop, WorkshopAttendance, ParentChildLink
from datetime import datetime
import os

student_bp = Blueprint('student_bp', __name__)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    # Get profile
    profile = Profile.query.filter_by(user_id=current_user.id).first()

    # Get enrollments
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    enrolled_course_ids = [e.course_id for e in enrollments]
    enrolled_courses = Course.query.filter(Course.id.in_(enrolled_course_ids)).all()

    # Get available courses
    available_courses = Course.query.filter(~Course.id.in_(enrolled_course_ids)).all()

    # Language improvement programs (course category)
    language_courses = Course.query.filter_by(category='Language').all()

    # Exam scores
    exam_scores = ExamScore.query.filter_by(user_id=current_user.id).all()

    daily_exams = Exam.query.filter_by(type='daily').all()
    weekly_exams = Exam.query.filter_by(type='weekly').all()
    monthly_exams = Exam.query.filter_by(type='monthly').all()

    competitive_exams = Exam.query.filter(
        (Exam.title.ilike('%gate%')) |
        (Exam.title.ilike('%cat%')) |
        (Exam.title.ilike('%gmat%')) |
        (Exam.title.ilike('%etc%'))
    ).all()

    # Applications
    applications = Application.query.filter_by(user_id=current_user.id).all()

    # Certificates
    certificates = Certificate.query.filter_by(user_id=current_user.id).all()

    # Startup ideas
    startup_ideas = StartupIdea.query.filter_by(user_id=current_user.id).all()

    # Projects
    projects = Project.query.filter_by(user_id=current_user.id).all()

    # Branch-specific internships and projects
    if profile and profile.branch:
        internships_by_branch = Internship.query.filter_by(branch=profile.branch).all()
        project_branch = Project.query.filter_by(category=profile.branch).all()
    else:
        internships_by_branch = Internship.query.all()
        project_branch = Project.query.all()

    # Govt jobs area-based
    area_jobs = Job.query
    if profile and profile.state:
        area_jobs = area_jobs.filter(Job.location.ilike(f"%{profile.state}%"))
    area_jobs = area_jobs.all()

    # Workshops
    workshops = Workshop.query.all()
    attended_workshop_ids = [wa.workshop_id for wa in WorkshopAttendance.query.filter_by(user_id=current_user.id).all()]
    attended_workshops = Workshop.query.filter(Workshop.id.in_(attended_workshop_ids)).all()

    # Eligibility
    analytic_score = profile.analytic_score if profile else 0
    language_proficiency = profile.language_proficiency if profile else 0.0
    mentor_info = {
        'name': profile.mentor_name if profile else '',
        'email': profile.mentor_email if profile else '',
        'phone': profile.mentor_phone if profile else ''
    }
    behavior = profile.behavior if profile else 'GOOD'
    eligible_internships = internships_by_branch
    eligible_jobs = Job.query.filter(Job.min_score <= analytic_score).all()
    campus_drive_eligible = analytic_score >= 75

    return render_template('auth/student_dashboard.html',
                         profile=profile,
                         enrolled_courses=enrolled_courses,
                         available_courses=available_courses,
                         language_courses=language_courses,
                         daily_exams=daily_exams,
                         weekly_exams=weekly_exams,
                         monthly_exams=monthly_exams,
                         competitive_exams=competitive_exams,
                         applications=applications,
                         certificates=certificates,
                         startup_ideas=startup_ideas,
                         projects=projects,
                         project_branch=project_branch,
                         internships_by_branch=internships_by_branch,
                         area_jobs=area_jobs,
                         attended_workshops=attended_workshops,
                         analytic_score=analytic_score,
                         language_proficiency=language_proficiency,
                         mentor_info=mentor_info,
                         behavior=behavior,
                         eligible_internships=eligible_internships,
                         eligible_jobs=eligible_jobs,
                         campus_drive_eligible=campus_drive_eligible,
                         datetime=datetime)

@student_bp.route('/student/enroll_course/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    course = Course.query.get_or_404(course_id)
    existing = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()

    if existing:
        return jsonify({'error': 'Already enrolled'}), 400

    try:
        enrollment = Enrollment(user_id=current_user.id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        return jsonify({'success': 'Enrolled successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Enrollment failed'}), 500

@student_bp.route('/student/unenroll_course/<int:course_id>', methods=['POST'])
@login_required
def unenroll_course(course_id):
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        return jsonify({'error': 'Not enrolled'}), 400

    try:
        db.session.delete(enrollment)
        db.session.commit()
        return jsonify({'success': 'Unenrolled successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Unenrollment failed'}), 500

@student_bp.route('/student/submit_startup_idea', methods=['POST'])
@login_required
def submit_startup_idea():
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')
    stage = request.form.get('stage', 'concept')

    if not all([title, description, category]):
        return jsonify({'error': 'All fields required'}), 400

    try:
        idea = StartupIdea(
            user_id=current_user.id,
            title=title,
            description=description,
            category=category,
            stage=stage
        )
        db.session.add(idea)
        db.session.commit()
        return jsonify({'success': 'Idea submitted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Submission failed'}), 500

@student_bp.route('/student/submit_project', methods=['POST'])
@login_required
def submit_project():
    if current_user.role != 'student':
        return jsonify({'error': 'Unauthorized'}), 403

    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')

    if not all([title, description, category]):
        return jsonify({'error': 'All fields required'}), 400

    # Handle file upload
    file = request.files.get('project_file')
    file_path = None
    if file:
        filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = os.path.join('static/uploads/projects', filename)
        file.save(file_path)

    try:
        project = Project(
            user_id=current_user.id,
            title=title,
            description=description,
            category=category,
            file_path=file_path,
            status='submitted'
        )
        db.session.add(project)
        db.session.commit()
        return jsonify({'success': 'Project submitted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Submission failed'}), 500

# Add more routes for exams, internships, etc. as needed

@student_bp.route('/profile')
@login_required
def profile():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    # Get profile
    profile = Profile.query.filter_by(user_id=current_user.id).first()

    # Get enrollments and courses
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    enrolled_course_ids = [e.course_id for e in enrollments]
    enrolled_courses = Course.query.filter(Course.id.in_(enrolled_course_ids)).all()

    # Get workshop attendance
    workshop_attendance = WorkshopAttendance.query.filter_by(user_id=current_user.id).all()
    attended_workshops = Workshop.query.filter(Workshop.id.in_([wa.workshop_id for wa in workshop_attendance])).all()

    # Get certificates
    certificates = Certificate.query.filter_by(user_id=current_user.id).all()

    # Get verified internships
    verified_internships = Application.query.filter_by(user_id=current_user.id, status='accepted').all()
    internship_ids = [app.internship_id for app in verified_internships if app.internship_id]
    internships = Internship.query.filter(Internship.id.in_(internship_ids)).all()

    # Get verified projects
    verified_projects = Project.query.filter_by(user_id=current_user.id, status='verified').all()

    # Get exam scores
    exam_scores = ExamScore.query.filter_by(user_id=current_user.id).all()

    # Course suggestions based on enrolled courses and branch
    if profile:
        branch_courses = Course.query.filter_by(category=profile.branch).filter(~Course.id.in_(enrolled_course_ids)).limit(5).all()
        other_courses = Course.query.filter(~Course.id.in_(enrolled_course_ids)).filter(~Course.id.in_([c.id for c in branch_courses])).limit(3).all()
        suggested_courses = branch_courses + other_courses
    else:
        suggested_courses = Course.query.limit(5).all()

    # Check for GATE course enrollment (assuming GATE is a special course)
    gate_course = None
    for course in enrolled_courses:
        if 'gate' in course.name.lower():
            gate_course = course
            break

    # Seminars (assuming workshops are seminars)
    seminars = attended_workshops

    # Eligibility calculations
    analytic_score = profile.analytic_score if profile else 0

    # Eligible internships (based on branch and score)
    if profile:
        eligible_internships = Internship.query.filter_by(branch=profile.branch).all()
    else:
        eligible_internships = Internship.query.all()

    # Eligible jobs (based on score requirements)
    eligible_jobs = Job.query.filter(Job.min_score <= analytic_score).all()

    # Campus drive eligibility
    campus_drive_eligible = analytic_score >= 75

    # Analytics
    language_proficiency = profile.language_proficiency if profile else 0.0
    behavior = profile.behavior if profile else 'GOOD'
    mentor_info = {
        'name': profile.mentor_name if profile else '',
        'email': profile.mentor_email if profile else '',
        'phone': profile.mentor_phone if profile else ''
    }

    return render_template('auth/student_profile.html',
                         profile=profile,
                         enrolled_courses=enrolled_courses,
                         attended_workshops=attended_workshops,
                         certificates=certificates,
                         internships=internships,
                         verified_projects=verified_projects,
                         exam_scores=exam_scores,
                         suggested_courses=suggested_courses,
                         gate_course=gate_course,
                         seminars=seminars,
                         eligible_internships=eligible_internships,
                         eligible_jobs=eligible_jobs,
                         campus_drive_eligible=campus_drive_eligible,
                         analytic_score=analytic_score,
                         language_proficiency=language_proficiency,
                         behavior=behavior,
                         mentor_info=mentor_info,
                         datetime=datetime)

@student_bp.route('/courses')
@login_required
def courses():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    # Get enrollments
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    enrolled_course_ids = [e.course_id for e in enrollments]
    enrolled_courses = Course.query.filter(Course.id.in_(enrolled_course_ids)).all()

    # Get available courses
    available_courses = Course.query.filter(~Course.id.in_(enrolled_course_ids)).all()

    return render_template('auth/courses.html',
                         enrolled_courses=enrolled_courses,
                         available_courses=available_courses)

@student_bp.route('/exams')
@login_required
def exams():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    # Get exam scores
    exam_scores = ExamScore.query.filter_by(user_id=current_user.id).all()

    # Get available exams (assuming exams are available to all students)
    available_exams = Exam.query.all()

    return render_template('auth/exams.html',
                         exam_scores=exam_scores,
                         available_exams=available_exams)

@student_bp.route('/internships')
@login_required
def internships():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    # Get internships
    internships = Internship.query.all()

    # Get applications
    applications = Application.query.filter_by(user_id=current_user.id).all()

    return render_template('auth/internships.html',
                         internships=internships,
                         applications=applications)

@student_bp.route('/projects')
@login_required
def projects():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    # Get projects
    projects = Project.query.filter_by(user_id=current_user.id).all()

    return render_template('auth/projects.html',
                         projects=projects)

@student_bp.route('/workshops')
@login_required
def workshops():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    # Get workshops
    workshops = Workshop.query.all()
    attended_workshop_ids = [wa.workshop_id for wa in WorkshopAttendance.query.filter_by(user_id=current_user.id).all()]
    attended_workshops = Workshop.query.filter(Workshop.id.in_(attended_workshop_ids)).all()

    return render_template('auth/workshops.html',
                         workshops=workshops,
                         attended_workshops=attended_workshops)

@student_bp.route('/startup')
@login_required
def startup():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    startup_ideas = StartupIdea.query.filter_by(user_id=current_user.id).all()

    return render_template('auth/startup.html',
                         startup_ideas=startup_ideas)

@student_bp.route('/govt-job-preparation')
@login_required
def govt_job_preparation():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    return render_template('auth/govt_job_preparation.html')

@student_bp.route('/jobs')
@login_required
def jobs():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    # Get profile
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    
    # Get user's analytic score
    analytic_score = profile.analytic_score if profile else 0

    # Get eligible jobs based on score
    eligible_jobs = Job.query.filter(Job.min_score <= analytic_score).all()
    
    # Get job applications
    applications = Application.query.filter_by(user_id=current_user.id).all()

    return render_template('auth/govt_jobs_available.html',
                         eligible_jobs=eligible_jobs,
                         applications=applications,
                         analytic_score=analytic_score)

@student_bp.route('/certificates')
@login_required
def certificates():
    if current_user.role != 'student':
        return redirect(url_for('home'))

    certificates = Certificate.query.filter_by(user_id=current_user.id).all()

    return render_template('auth/certificates.html',
                         certificates=certificates)


@student_bp.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)

    if current_user.role == 'student':
        if project.user_id != current_user.id:
            return redirect(url_for('home'))
    elif current_user.role == 'parent':
        link = ParentChildLink.query.filter_by(parent_id=current_user.id, child_id=project.user_id).first()
        if not link:
            return redirect(url_for('home'))
    elif current_user.role == 'college':
        # colleges can view all student projects
        pass
    else:
        return redirect(url_for('home'))

    return render_template('auth/project_detail.html', project=project)


@student_bp.route('/certificate/<int:certificate_id>')
@login_required
def certificate_detail(certificate_id):
    certificate = Certificate.query.get_or_404(certificate_id)

    if current_user.role == 'student':
        if certificate.user_id != current_user.id:
            return redirect(url_for('home'))
    elif current_user.role == 'parent':
        link = ParentChildLink.query.filter_by(parent_id=current_user.id, child_id=certificate.user_id).first()
        if not link:
            return redirect(url_for('home'))
    elif current_user.role == 'college':
        pass
    else:
        return redirect(url_for('home'))

    return render_template('auth/certificate_detail.html', certificate=certificate)
