from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Profile, Course, Enrollment, Exam, ExamScore, Job, Internship, Application, Certificate, StartupIdea, Project, Workshop, WorkshopAttendance, ParentChildLink
from datetime import datetime
import re

parent_bp = Blueprint('parent_bp', __name__)

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Profile, Course, Enrollment, Exam, ExamScore, Job, Internship, Application, Certificate, StartupIdea, Project, Workshop, WorkshopAttendance, ParentChildLink
from datetime import datetime, timedelta
import re

parent_bp = Blueprint('parent_bp', __name__)

@parent_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'parent':
        return redirect(url_for('home'))

    child_links = ParentChildLink.query.filter_by(parent_id=current_user.id).all()
    linked_child_ids = [link.child_id for link in child_links]

    # Fetch linked student accounts
    children = User.query.filter(User.id.in_(linked_child_ids), User.role == 'student').all() if linked_child_ids else []

    if not children:
        return render_template('auth/parent_dashboard.html',
                               child=None,
                               children=[],
                               has_child=False,
                               datetime=datetime,
                               notifications=[])

    selected_child_id = request.args.get('child_id', type=int)
    if selected_child_id and selected_child_id in linked_child_ids:
        child = User.query.get(selected_child_id)
    else:
        child = children[0]

    if not child or child.role != 'student':
        return render_template('auth/parent_dashboard.html',
                               child=None,
                               children=children,
                               has_child=False,
                               datetime=datetime,
                               notifications=[])

    # Get child's profile
    child_profile = Profile.query.filter_by(user_id=child.id).first()

    # Get child's data (read-only for parent)
    child_enrollments = Enrollment.query.filter_by(user_id=child.id).all()
    enrolled_course_ids = [e.course_id for e in child_enrollments]
    child_courses = Course.query.filter(Course.id.in_(enrolled_course_ids)).all()

    child_exam_scores = ExamScore.query.filter_by(user_id=child.id).all()
    child_applications = Application.query.filter_by(user_id=child.id).all()
    child_certificates = Certificate.query.filter_by(user_id=child.id).all()
    child_projects = Project.query.filter_by(user_id=child.id).all()
    child_startup_ideas = StartupIdea.query.filter_by(user_id=child.id).all()

    attended_workshop_ids = [wa.workshop_id for wa in WorkshopAttendance.query.filter_by(user_id=child.id).all()]
    child_workshops = Workshop.query.filter(Workshop.id.in_(attended_workshop_ids)).all()

    seminars = child_workshops
    assignments = []

    daily_exams = [score for score in child_exam_scores if score.exam and score.exam.type == 'daily']
    weekly_exams = [score for score in child_exam_scores if score.exam and score.exam.type == 'weekly']
    monthly_exams = [score for score in child_exam_scores if score.exam and score.exam.type == 'monthly']

    gate_scores = []

    total_applications = len(child_applications)
    selected_applications = len([app for app in child_applications if app.status == 'selected'])
    hiring_percentage = (selected_applications / total_applications * 100) if total_applications > 0 else 0

    notifications = []
    recent_cutoff = datetime.utcnow() - timedelta(days=7)

    recent_projects = [p for p in child_projects if p.submission_date and p.submission_date > recent_cutoff]
    for project in recent_projects:
        notifications.append({'message': f'New project "{project.title}" submitted', 'created_at': project.submission_date})

    recent_applications = [app for app in child_applications if app.applied_at and app.applied_at > recent_cutoff]
    for app in recent_applications:
        job_title = app.job.title if app.job else (app.internship.title if app.internship else 'Position')
        notifications.append({'message': f'Applied for {job_title} - Status: {app.status}', 'created_at': app.applied_at})

    recent_certificates = [cert for cert in child_certificates if cert.issued_at and cert.issued_at > recent_cutoff]
    for cert in recent_certificates:
        notifications.append({'message': f'Certificate earned: {cert.title}', 'created_at': cert.issued_at})

    notifications.sort(key=lambda x: x['created_at'], reverse=True)

    return render_template('auth/parent_dashboard.html',
                           child=child,
                           children=children,
                           child_profile=child_profile,
                           child_courses=child_courses,
                           child_exam_scores=child_exam_scores,
                           child_applications=child_applications,
                           child_certificates=child_certificates,
                           child_projects=child_projects,
                           child_startup_ideas=child_startup_ideas,
                           child_workshops=child_workshops,
                           has_child=True,
                           datetime=datetime,
                           notifications=notifications,
                           hiring_percentage=int(hiring_percentage),
                           seminars=seminars,
                           assignments=assignments,
                           daily_exams=daily_exams,
                           weekly_exams=weekly_exams,
                           monthly_exams=monthly_exams,
                           gate_scores=gate_scores)

@parent_bp.route('/link_child', methods=['POST'])
@login_required
def link_child():
    if current_user.role != 'parent':
        return jsonify({'error': 'Unauthorized'}), 403

    child_unique_id = request.form.get('child_unique_id', '').strip().upper()

    if not child_unique_id:
        flash('Child unique ID is required', 'error')
        return redirect(url_for('parent_bp.dashboard'))

    if not child_unique_id.endswith('NEXG'):
        flash('Invalid unique ID format. It should end with NEXG.', 'error')
        return redirect(url_for('parent_bp.dashboard'))

    child = User.query.filter_by(unique_id=child_unique_id, role='student').first()
    if not child:
        flash('Student not found. Check the Unique ID and try again.', 'error')
        return redirect(url_for('parent_bp.dashboard'))

    existing_link = ParentChildLink.query.filter_by(parent_id=current_user.id, child_id=child.id).first()
    if existing_link:
        flash('Child already linked.', 'error')
        return redirect(url_for('parent_bp.dashboard'))

    try:
        link = ParentChildLink(parent_id=current_user.id, child_id=child.id)
        db.session.add(link)
        db.session.commit()
        flash('Child linked successfully!', 'success')
        return redirect(url_for('parent_bp.dashboard'))
    except Exception as e:
        db.session.rollback()
        flash('Failed to link child. Please try again.', 'error')
        return redirect(url_for('parent_bp.dashboard'))


@parent_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != 'parent':
        return redirect(url_for('home'))

    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        mobile_number = request.form.get('mobile_number')
        parents_mobile = request.form.get('parents_mobile')
        state = request.form.get('state')
        child_unique_id = request.form.get('child_unique_id', '').strip().upper()

        if not all([name, email]):
            flash('Name and Email are required', 'error')
            return redirect(url_for('parent_bp.profile'))

        # Update user info
        current_user.name = name
        current_user.email = email

        if not profile:
            profile = Profile(user_id=current_user.id)
            db.session.add(profile)

        profile.mobile_number = mobile_number
        profile.parents_mobile = parents_mobile
        profile.state = state

        if child_unique_id:
            if not child_unique_id.endswith('NEXG'):
                flash('Invalid child Unique ID format.', 'error')
                return redirect(url_for('parent_bp.profile'))

            child = User.query.filter_by(unique_id=child_unique_id, role='student').first()
            if not child:
                flash('Student not found with that unique ID.', 'error')
                return redirect(url_for('parent_bp.profile'))

            existing_link = ParentChildLink.query.filter_by(parent_id=current_user.id, child_id=child.id).first()
            if existing_link:
                flash('Child already linked.', 'info')
            else:
                db.session.add(ParentChildLink(parent_id=current_user.id, child_id=child.id))
                flash('Child linked successfully!', 'success')

        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Failed to update profile. Please try again.', 'error')

        return redirect(url_for('parent_bp.profile'))

    child_links = ParentChildLink.query.filter_by(parent_id=current_user.id).all()
    child_ids = [link.child_id for link in child_links]
    children = User.query.filter(User.id.in_(child_ids), User.role == 'student').all() if child_ids else []

    return render_template('auth/parent_profile.html', parent=current_user, profile=profile, children=children)
