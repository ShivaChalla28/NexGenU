from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import db, User, Profile, PreRegistrationQuery, ParentChildLink
from datetime import datetime
import re

auth = Blueprint("auth", __name__)

def generate_unique_id(email, roll_number, registration_year):
    """Generate unified unique ID: YYNNNNEEEE + NEXG"""
    yy = str(registration_year)[-2:]  # Last 2 digits of year
    nnnn = roll_number[-4:] if len(roll_number) >= 4 else roll_number.zfill(4)  # Last 4 digits of roll number
    eeee = email.split('@')[0][:4].upper()  # First 4 letters of email before @
    return f"{yy}{nnnn}{eeee}NEXG"

@auth.route("/pre_register", methods=["GET", "POST"])
def pre_register():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        # Basic validation
        if not all([name, email, phone, message]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.pre_register'))

        # Sanitize input
        name = name.strip()
        email = email.strip().lower()
        phone = phone.strip()
        message = message.strip()

        # Email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Invalid email format', 'error')
            return redirect(url_for('auth.pre_register'))

        # Phone validation
        if not re.match(r'^\+?[\d\s\-\(\)]{10,15}$', phone):
            flash('Invalid phone number', 'error')
            return redirect(url_for('auth.pre_register'))

        try:
            query = PreRegistrationQuery(
                name=name,
                email=email,
                phone=phone,
                message=message
            )
            db.session.add(query)
            db.session.commit()
            flash('Query submitted successfully! We will contact you soon.', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('Error submitting query. Please try again.', 'error')
            return redirect(url_for('auth.pre_register'))

    return render_template("pre_register.html")

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = request.form.get('role', 'student')

        if role == 'student':
            return redirect(url_for('auth.register_student'))
        elif role == 'parent':
            return redirect(url_for('auth.register_parent'))
        elif role == 'college':
            return redirect(url_for('auth.register_college'))

    return render_template("auth/register.html")

@auth.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        college_name = request.form.get('college_name')
        college_roll_number = request.form.get('college_roll_number')
        mobile_number = request.form.get('mobile_number')
        email = request.form.get('email')
        parents_mobile = request.form.get('parents_mobile')
        branch = request.form.get('branch')
        state = request.form.get('state')
        password = request.form.get('password')

        # Validation
        if not all([first_name, last_name, college_name, college_roll_number, mobile_number, email, parents_mobile, branch, state, password]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.register_student'))

        # Email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Invalid email format', 'error')
            return redirect(url_for('auth.register_student'))

        # Phone validation - accept 10-15 digit numbers
        if len(mobile_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')) < 10:
            flash('Invalid phone number format', 'error')
            return redirect(url_for('auth.register_student'))
        
        if len(parents_mobile.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')) < 10:
            flash('Invalid phone number format', 'error')
            return redirect(url_for('auth.register_student'))

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register_student'))

        try:
            # Generate unique ID
            registration_year = datetime.now().year
            unique_id = generate_unique_id(email, college_roll_number, registration_year)

            # Ensure unique ID is unique
            while User.query.filter_by(unique_id=unique_id).first():
                unique_id = generate_unique_id(email, college_roll_number, registration_year + 1)  # Fallback

            # Create user
            name = f"{first_name} {last_name}"
            hashed_password = generate_password_hash(password)

            user = User(
                name=name,
                email=email,
                password=hashed_password,
                role='student',
                unique_id=unique_id
            )
            db.session.add(user)
            db.session.flush()  # Get user.id

            # Create profile
            profile = Profile(
                user_id=user.id,
                branch=branch,
                college=college_name,
                college_roll_number=college_roll_number,
                mobile_number=mobile_number,
                parents_mobile=parents_mobile,
                state=state
            )
            db.session.add(profile)
            db.session.commit()

            # Send email with unique ID (placeholder)
            # send_email(email, 'Registration Successful', f'Your unique ID is: {unique_id}')

            flash(f'Registration successful! Your unique ID is: {unique_id}', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('auth.register_student'))

    return render_template("auth/register_student.html")

@auth.route("/register/parent", methods=["GET", "POST"])
def register_parent():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        mobile_number = request.form.get('mobile_number')
        password = request.form.get('password')

        # Validation
        if not all([name, email, mobile_number, password]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.register_parent'))

        # Email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Invalid email format', 'error')
            return redirect(url_for('auth.register_parent'))

        # Phone validation - accept 10-15 digit numbers
        if len(mobile_number.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')) < 10:
            flash('Invalid phone number format', 'error')
            return redirect(url_for('auth.register_parent'))

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register_parent'))

        try:
            hashed_password = generate_password_hash(password)

            user = User(
                name=name,
                email=email,
                password=hashed_password,
                role='parent'
            )
            db.session.add(user)
            db.session.commit()

            flash('Registration successful! Please login and link your child.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('auth.register_parent'))

    return render_template("auth/register_parent.html")

@auth.route("/register/college", methods=["GET", "POST"])
def register_college():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        # Add college-specific fields as needed

        # Validation similar to above
        if not all([name, email, password]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.register_college'))

        try:
            hashed_password = generate_password_hash(password)

            user = User(
                name=name,
                email=email,
                password=hashed_password,
                role='college'
            )
            db.session.add(user)
            db.session.commit()

            flash('Registration successful!', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return redirect(url_for('auth.register_college'))

    return render_template("auth/register_college.html")

@auth.route("/student_login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email, role='student').first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('student_bp.dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template("auth/student_login.html")

@auth.route("/parent_login", methods=["GET", "POST"])
def parent_login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email, role='parent').first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('parent_bp.dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template("auth/parent_login.html")

@auth.route("/college_login", methods=["GET", "POST"])
def college_login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email, role='college').first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('college_bp.dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template("auth/college_login.html")

@auth.route("/recruiter_login", methods=["GET", "POST"])
def recruiter_login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email, role='admin').first()  # Assuming admin is recruiter
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('auth.recruiter_dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template("auth/recruiter_login.html")

@auth.route("/recruiter_dashboard")
@login_required
def recruiter_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    return render_template("auth/recruiter_dashboard.html")

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student')

        user = User.query.filter_by(email=email, role=role).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'student':
                return redirect(url_for('student_bp.dashboard'))
            elif user.role == 'parent':
                return redirect(url_for('parent_bp.dashboard'))
            elif user.role == 'college':
                return redirect(url_for('college_bp.dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            # fallback to discover user in case role selection doesn't match exactly
            user_any = User.query.filter_by(email=email).first()
            if user_any and check_password_hash(user_any.password, password):
                login_user(user_any)
                flash('Logged in with detected role: ' + user_any.role, 'info')
                if user_any.role == 'student':
                    return redirect(url_for('student_bp.dashboard'))
                elif user_any.role == 'parent':
                    return redirect(url_for('parent_bp.dashboard'))
                elif user_any.role == 'college':
                    return redirect(url_for('college_bp.dashboard'))
                else:
                    return redirect(url_for('home'))
            flash('Invalid email, password or role. Please check and try again', 'error')

    return render_template("auth/login.html")

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@auth.route("/link_child", methods=["POST"])
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
