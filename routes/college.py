from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Profile, Course, Enrollment, Exam, ExamScore, Job, Internship, Application, Certificate, StartupIdea, Project, Workshop, WorkshopAttendance, PreRegistrationQuery
from datetime import datetime, timedelta

college_bp = Blueprint('college_bp', __name__)

@college_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'college':
        return redirect(url_for('home'))

    # Get college students
    college_students = User.query.filter(
        User.role == 'student',
        Profile.user_id == User.id,
        Profile.college.ilike(f'%{current_user.name}%')
    ).join(Profile).all()

    # Get pre-registration queries
    queries = PreRegistrationQuery.query.all()

    # Get college statistics
    total_students = len(college_students)
    active_students = len([s for s in college_students if s.created_at > datetime.now() - timedelta(days=30)])

    college_student_ids = [s.id for s in college_students]
    total_projects = Project.query.filter(Project.user_id.in_(college_student_ids)).count()

    total_applications = Application.query.filter(Application.user_id.in_(college_student_ids)).count()

    internship_eligible = len(Application.query.filter(Application.user_id.in_(college_student_ids), Application.internship_id.isnot(None), Application.status == 'approved').all())
    placement_eligible = len(Application.query.filter(Application.user_id.in_(college_student_ids), Application.job_id.isnot(None), Application.status == 'selected').all())
    jobs_got = len(Application.query.filter(Application.user_id.in_(college_student_ids), Application.job_id.isnot(None), Application.status == 'selected').all())
    workshops_attended = WorkshopAttendance.query.filter(WorkshopAttendance.user_id.in_(college_student_ids)).count()

    gate_qualified_students = len([s for s in college_students if s.profile and (s.profile.analytic_score or 0) >= 70])
    companies_ready = Job.query.count()

    from sqlalchemy import func
    pre_reg_students = Profile.query.filter(Profile.college.ilike(f'%{current_user.name}%')).count()
    mentors_count = 0
    if college_students:
        mentors_count = len(set([s.profile.mentor_name for s in college_students if s.profile and s.profile.mentor_name]))

    return render_template('auth/college_dashboard.html',
                         college_students=college_students,
                         queries=queries,
                         stats={
                             'total_students': total_students,
                             'active_students': active_students,
                             'total_projects': total_projects,
                             'total_applications': total_applications,
                             'internship_eligible': internship_eligible,
                             'placement_eligible': placement_eligible,
                             'jobs_got': jobs_got,
                             'workshops_attended': workshops_attended,
                             'gate_qualified': gate_qualified_students,
                             'companies_ready': companies_ready,
                             'registered_from_clg': pre_reg_students,
                             'mentors': mentors_count,
                             'students': total_students
                         },
                         datetime=datetime)


@college_bp.route('/student/<int:student_id>')
@login_required
def view_student(student_id):
    if current_user.role != 'college':
        return redirect(url_for('home'))

    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return redirect(url_for('college_bp.dashboard'))

    # Verify college access
    profile = Profile.query.filter_by(user_id=student_id).first()
    if not profile or current_user.name.lower() not in profile.college.lower():
        flash('Access denied', 'error')
        return redirect(url_for('college_bp.dashboard'))

    # Get student data
    enrollments = Enrollment.query.filter_by(user_id=student_id).all()
    courses = Course.query.filter(Course.id.in_([e.course_id for e in enrollments])).all()
    exam_scores = ExamScore.query.filter_by(user_id=student_id).all()
    projects = Project.query.filter_by(user_id=student_id).all()
    applications = Application.query.filter_by(user_id=student_id).all()
    certificates = Certificate.query.filter_by(user_id=student_id).all()

    return render_template('auth/student_detail.html',
                         student=student,
                         profile=profile,
                         courses=courses,
                         exam_scores=exam_scores,
                         projects=projects,
                         applications=applications,
                         certificates=certificates)

@college_bp.route('/student/<int:student_id>/update', methods=['POST'])
@login_required
def update_student(student_id):
    if current_user.role != 'college':
        return redirect(url_for('home'))

    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return redirect(url_for('college_bp.dashboard'))

    profile = Profile.query.filter_by(user_id=student_id).first()
    if not profile:
        profile = Profile(user_id=student_id)
        db.session.add(profile)

    activity_notes = request.form.get('activity_notes')
    project_feedback = request.form.get('project_feedback')
    assignment_status = request.form.get('assignment_status')
    backlog_count = request.form.get('backlogs')
    lang_score = request.form.get('language_proficiency')
    gate_score = request.form.get('analytic_score')

    # Save profile data
    try:
        if backlog_count:
            profile.backlogs = int(backlog_count)
        if lang_score:
            profile.language_proficiency = float(lang_score)
        if gate_score:
            profile.analytic_score = int(gate_score)

        if activity_notes:
            # save in behavior field as a temporary activity log summary
            profile.behavior = activity_notes[:200]

        db.session.commit()
        flash('Student records updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Unable to update student records', 'error')

    return redirect(url_for('college_bp.view_student', student_id=student_id))

@college_bp.route('/project/<int:project_id>/verify', methods=['POST'])
@login_required
def verify_project(project_id):
    if current_user.role != 'college':
        return jsonify({'error': 'Unauthorized'}), 403

    project = Project.query.get_or_404(project_id)

    # Verify college access
    profile = Profile.query.filter_by(user_id=project.user_id).first()
    if not profile or current_user.name.lower() not in profile.college.lower():
        return jsonify({'error': 'Access denied'}), 403

    action = request.form.get('action')
    feedback = request.form.get('feedback', '')

    if action == 'approve':
        project.status = 'verified'
        project.verified_by = current_user.id
        project.verification_date = datetime.utcnow()
        project.feedback = feedback
    elif action == 'reject':
        project.status = 'rejected'
        project.feedback = feedback
    else:
        return jsonify({'error': 'Invalid action'}), 400

    try:
        db.session.commit()
        return jsonify({'success': f'Project {action}d successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update project'}), 500

@college_bp.route('/college/query/<int:query_id>/delete', methods=['POST'])
@login_required
def delete_query(query_id):
    if current_user.role != 'college':
        return jsonify({'error': 'Unauthorized'}), 403

    query = PreRegistrationQuery.query.get_or_404(query_id)

    try:
        db.session.delete(query)
        db.session.commit()
        return jsonify({'success': 'Query deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete query'}), 500