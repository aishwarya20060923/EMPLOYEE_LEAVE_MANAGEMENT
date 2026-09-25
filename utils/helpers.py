from functools import wraps
from datetime import datetime, date, timedelta
from flask import session, redirect, url_for, flash, abort, request, current_app
from models.models import db, User, Employee, Holiday, LeaveRequest, AuditLog, Notification

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_active:
            session.clear()
            flash('Your account has been deactivated or does not exist. Please contact admin.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            user_role = session.get('role')
            if user_role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None

def get_current_employee():
    user = get_current_user()
    if user and user.employee:
        return user.employee
    return None

def calculate_working_days(start_date, end_date, is_half_day=False):
    # Calculate working leave days excluding weekends (Sat/Sun) and mandatory holidays
    if start_date > end_date:
        return 0.0, [], []

    holidays_query = Holiday.query.filter(
        Holiday.date >= start_date,
        Holiday.date <= end_date,
        Holiday.is_optional == False
    ).all()
    holiday_dates = {h.date: h.name for h in holidays_query}

    working_days = 0.0
    weekends_skipped = []
    holidays_skipped = []

    current = start_date
    while current <= end_date:
        if current.weekday() in (5, 6):
            weekends_skipped.append(current)
        elif current in holiday_dates:
            holidays_skipped.append((current, holiday_dates[current]))
        else:
            working_days += 1.0
        current += timedelta(days=1)

    if is_half_day and working_days > 0:
        working_days = 0.5

    return working_days, weekends_skipped, holidays_skipped

def check_leave_conflict(employee_id, start_date, end_date, exclude_request_id=None):
    # Check if employee has an overlapping Pending or Approved leave request
    query = LeaveRequest.query.filter(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status.in_(['Pending', 'Approved']),
        LeaveRequest.start_date <= end_date,
        LeaveRequest.end_date >= start_date
    )
    if exclude_request_id:
        query = query.filter(LeaveRequest.id != exclude_request_id)
    return query.first()

def generate_request_number():
    year = datetime.utcnow().year
    count = LeaveRequest.query.count() + 1
    return f'LR-{year}-{count:04d}'

def log_audit(action, record_type=None, record_id=None, details=None):
    try:
        user_id = session.get('user_id')
        user_email = session.get('email', 'System/Anonymous')
        ip_addr = request.remote_addr if request else '127.0.0.1'

        log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            record_type=record_type,
            record_id=str(record_id) if record_id else None,
            details=details,
            ip_address=ip_addr,
            timestamp=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print('Error logging audit:', e)

def create_notification(user_id, title, message, category='info', link=None):
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            link=link,
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.session.add(notif)
        db.session.commit()
        return notif
    except Exception as e:
        db.session.rollback()
        print('Error creating notification:', e)
        return None

def allowed_file(filename):
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
