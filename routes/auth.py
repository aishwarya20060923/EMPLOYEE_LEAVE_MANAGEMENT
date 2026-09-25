import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from models.models import db, User, Employee
from utils.helpers import log_audit, get_current_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET' and 'user_id' in session:
        role = session.get('role')
        if role == 'Admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'Manager':
            return redirect(url_for('manager.dashboard'))
        else:
            return redirect(url_for('employee.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password. Please check your credentials.', 'danger')
            return render_template('auth/login.html', email=email)

        if not user.is_active:
            flash('Your account has been deactivated. Please contact the administrator.', 'danger')
            return render_template('auth/login.html', email=email)

        # Successful login
        session.clear()
        session.permanent = remember
        session['user_id'] = user.id
        session['role'] = user.role
        session['email'] = user.email
        
        emp = user.employee
        session['employee_id'] = emp.id if emp else None
        session['employee_code'] = emp.employee_id if emp else None
        session['name'] = emp.full_name if emp else user.email.split('@')[0].capitalize()

        log_audit('User Login', record_type='User', record_id=user.id, details=f'Logged in as {user.role}')
        flash(f'Welcome back, {session["name"]}!', 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user.role == 'Admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'Manager':
            return redirect(url_for('manager.dashboard'))
        else:
            return redirect(url_for('employee.dashboard'))

    return render_template('auth/login.html')

@auth.route('/quick-login/<role>')
def quick_login(role):
    # Quick demo login helper for seamless testing during CRT viva
    role_map = {
        'admin': 'admin@example.com',
        'manager': 'manager@example.com',
        'employee': 'employee@example.com'
    }
    email = role_map.get(role.lower())
    if not email:
        flash('Invalid role specified.', 'warning')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash(f'Demo user for {role} not found. Please run seed.py first.', 'danger')
        return redirect(url_for('auth.login'))

    session.clear()
    session['user_id'] = user.id
    session['role'] = user.role
    session['email'] = user.email
    emp = user.employee
    session['employee_id'] = emp.id if emp else None
    session['employee_code'] = emp.employee_id if emp else None
    session['name'] = emp.full_name if emp else user.email.split('@')[0].capitalize()

    log_audit('Demo Quick Login', record_type='User', record_id=user.id, details=f'Quick demo login as {user.role}')
    flash(f'Logged in with demo credentials as {user.role} ({session["name"]})', 'info')

    if user.role == 'Admin':
        return redirect(url_for('admin.dashboard'))
    elif user.role == 'Manager':
        return redirect(url_for('manager.dashboard'))
    else:
        return redirect(url_for('employee.dashboard'))

@auth.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_audit('User Logout', record_type='User', record_id=user_id, details='Logged out')
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('auth.login'))
