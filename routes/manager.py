import os
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.models import db, User, Employee, Department, LeaveType, LeaveBalance, LeaveRequest, Holiday, Attendance, Notification
from utils.helpers import login_required, role_required, get_current_user, get_current_employee, log_audit, create_notification

manager = Blueprint('manager', __name__, url_prefix='/manager')

@manager.before_request
@login_required
@role_required(['Manager', 'Admin'])
def before_request():
    pass

@manager.route('/dashboard')
def dashboard():
    today = date.today()
    current_year = today.year

    total_employees = Employee.query.filter_by(status='Active').count()
    pending_count = LeaveRequest.query.filter_by(status='Pending').count()
    approved_count = LeaveRequest.query.filter_by(status='Approved').count()
    rejected_count = LeaveRequest.query.filter_by(status='Rejected').count()

    # Employees currently on leave today
    on_leave_today = LeaveRequest.query.filter(
        LeaveRequest.status == 'Approved',
        LeaveRequest.start_date <= today,
        LeaveRequest.end_date >= today
    ).all()

    # Upcoming approved leaves in next 14 days
    upcoming_leaves = LeaveRequest.query.filter(
        LeaveRequest.status == 'Approved',
        LeaveRequest.start_date > today,
        LeaveRequest.start_date <= today + timedelta(days=14)
    ).order_by(LeaveRequest.start_date.asc()).all()

    # Pending requests queue for quick review
    pending_requests = LeaveRequest.query.filter_by(status='Pending').order_by(LeaveRequest.applied_at.asc()).limit(10).all()

    # Chart 1: Monthly Requests (last 6 months)
    months_labels = []
    monthly_data = []
    for i in range(5, -1, -1):
        target_month_date = today.replace(day=1) - timedelta(days=i*30)
        m_start = date(target_month_date.year, target_month_date.month, 1)
        if target_month_date.month == 12:
            m_end = date(target_month_date.year + 1, 1, 1) - timedelta(days=1)
        else:
            m_end = date(target_month_date.year, target_month_date.month + 1, 1) - timedelta(days=1)
        
        m_count = LeaveRequest.query.filter(LeaveRequest.applied_at >= m_start, LeaveRequest.applied_at <= datetime.combine(m_end, datetime.max.time())).count()
        months_labels.append(m_start.strftime('%b %Y'))
        monthly_data.append(m_count)

    # Chart 2: Status distribution
    status_counts = {
        'Approved': approved_count,
        'Pending': pending_count,
        'Rejected': rejected_count,
        'Cancelled': LeaveRequest.query.filter_by(status='Cancelled').count()
    }

    # Chart 3: Leave Type distribution
    leave_types = LeaveType.query.all()
    type_labels = [lt.name for lt in leave_types]
    type_counts = [LeaveRequest.query.filter_by(leave_type_id=lt.id).count() for lt in leave_types]

    # Chart 4: Department-wise leave usage
    departments = Department.query.filter_by(is_active=True).all()
    dept_labels = []
    dept_usage = []
    for dept in departments:
        dept_labels.append(dept.name)
        # Sum of days requested for approved leaves in this department
        days_sum = db.session.query(db.func.sum(LeaveRequest.days_requested))\
            .join(Employee, Employee.id == LeaveRequest.employee_id)\
            .filter(Employee.department_id == dept.id, LeaveRequest.status == 'Approved').scalar() or 0.0
        dept_usage.append(round(days_sum, 1))

    return render_template(
        'manager/dashboard.html',
        total_employees=total_employees,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        on_leave_today=on_leave_today,
        upcoming_leaves=upcoming_leaves,
        pending_requests=pending_requests,
        months_labels=months_labels,
        monthly_data=monthly_data,
        status_counts=status_counts,
        type_labels=type_labels,
        type_counts=type_counts,
        dept_labels=dept_labels,
        dept_usage=dept_usage
    )

@manager.route('/leave-requests')
def leave_requests():
    status_filter = request.args.get('status', '').strip()
    dept_filter = request.args.get('department', type=int)
    type_filter = request.args.get('leave_type', type=int)
    search_query = request.args.get('search', '').strip()

    query = LeaveRequest.query.join(Employee, Employee.id == LeaveRequest.employee_id)

    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)
    if dept_filter:
        query = query.filter(Employee.department_id == dept_filter)
    if type_filter:
        query = query.filter(LeaveRequest.leave_type_id == type_filter)
    if search_query:
        query = query.filter(
            db.or_(
                LeaveRequest.request_number.ilike(f'%{search_query}%'),
                Employee.first_name.ilike(f'%{search_query}%'),
                Employee.last_name.ilike(f'%{search_query}%'),
                Employee.employee_id.ilike(f'%{search_query}%'),
                LeaveRequest.reason.ilike(f'%{search_query}%')
            )
        )

    requests_list = query.order_by(LeaveRequest.applied_at.desc()).all()
    departments = Department.query.filter_by(is_active=True).all()
    leave_types = LeaveType.query.all()

    return render_template(
        'manager/leave_requests.html',
        leave_requests=requests_list,
        departments=departments,
        leave_types=leave_types,
        status_filter=status_filter,
        dept_filter=dept_filter,
        type_filter=type_filter,
        search_query=search_query
    )

@manager.route('/approve-leave/<int:request_id>', methods=['POST'])
def approve_leave(request_id):
    reviewer = get_current_employee()
    leave_req = LeaveRequest.query.get_or_404(request_id)

    if leave_req.status != 'Pending':
        flash(f'Request {leave_req.request_number} is already {leave_req.status}.', 'warning')
        return redirect(request.referrer or url_for('manager.leave_requests'))

    # Verify balance
    balance = LeaveBalance.query.filter_by(
        employee_id=leave_req.employee_id,
        leave_type_id=leave_req.leave_type_id,
        year=leave_req.start_date.year
    ).first()

    if not balance:
        flash('No leave balance record found for this employee and year.', 'danger')
        return redirect(request.referrer or url_for('manager.leave_requests'))

    if balance.remaining_days < leave_req.days_requested:
        flash(f'Cannot approve: Insufficient balance. Available: {balance.remaining_days}, Requested: {leave_req.days_requested}', 'danger')
        return redirect(request.referrer or url_for('manager.leave_requests'))

    # Deduct balance
    balance.used_days += leave_req.days_requested
    balance.update_balance()

    leave_req.status = 'Approved'
    leave_req.reviewed_by_id = reviewer.id if reviewer else None
    leave_req.reviewed_at = datetime.utcnow()

    # Integrate with attendance for the approved dates
    curr = leave_req.start_date
    while curr <= leave_req.end_date:
        if curr.weekday() < 5:  # Skip weekends for attendance integration
            att = Attendance.query.filter_by(employee_id=leave_req.employee_id, date=curr).first()
            if not att:
                att = Attendance(
                    employee_id=leave_req.employee_id,
                    date=curr,
                    status='Leave',
                    notes=f'Approved {leave_req.leave_type.code} ({leave_req.request_number})'
                )
                db.session.add(att)
            else:
                att.status = 'Leave'
                att.notes = f'Approved {leave_req.leave_type.code} ({leave_req.request_number})'
        curr += timedelta(days=1)

    db.session.commit()

    # Log audit
    log_audit(
        'Leave Approved',
        record_type='LeaveRequest',
        record_id=leave_req.id,
        details=f'Approved request {leave_req.request_number} ({leave_req.days_requested} days of {leave_req.leave_type.name}) for {leave_req.employee.full_name}'
    )

    # Notify Employee
    create_notification(
        user_id=leave_req.employee.user_id,
        title='Leave Request Approved',
        message=f'Great news! Your leave request {leave_req.request_number} for {leave_req.days_requested} days has been APPROVED by {session.get("name")}.',
        category='success',
        link=url_for('employee.my_leaves')
    )

    flash(f'Leave request {leave_req.request_number} approved successfully.', 'success')
    return redirect(request.referrer or url_for('manager.leave_requests'))

@manager.route('/reject-leave/<int:request_id>', methods=['POST'])
def reject_leave(request_id):
    reviewer = get_current_employee()
    leave_req = LeaveRequest.query.get_or_404(request_id)

    if leave_req.status != 'Pending':
        flash(f'Request {leave_req.request_number} is already {leave_req.status}.', 'warning')
        return redirect(request.referrer or url_for('manager.leave_requests'))

    rejection_reason = request.form.get('rejection_reason', '').strip()
    if not rejection_reason:
        rejection_reason = 'Rejected per managerial review.'

    leave_req.status = 'Rejected'
    leave_req.reviewed_by_id = reviewer.id if reviewer else None
    leave_req.reviewed_at = datetime.utcnow()
    leave_req.rejection_reason = rejection_reason
    db.session.commit()

    # Log audit
    log_audit(
        'Leave Rejected',
        record_type='LeaveRequest',
        record_id=leave_req.id,
        details=f'Rejected request {leave_req.request_number} for {leave_req.employee.full_name}. Reason: {rejection_reason}'
    )

    # Notify Employee
    create_notification(
        user_id=leave_req.employee.user_id,
        title='Leave Request Rejected',
        message=f'Your leave request {leave_req.request_number} was rejected by {session.get("name")}. Reason: {rejection_reason}',
        category='danger',
        link=url_for('employee.my_leaves')
    )

    flash(f'Leave request {leave_req.request_number} rejected.', 'info')
    return redirect(request.referrer or url_for('manager.leave_requests'))

@manager.route('/employees')
def employees():
    dept_filter = request.args.get('department', type=int)
    status_filter = request.args.get('status', '').strip()
    search_query = request.args.get('search', '').strip()

    query = Employee.query.join(User, User.id == Employee.user_id)

    if dept_filter:
        query = query.filter(Employee.department_id == dept_filter)
    if status_filter:
        query = query.filter(Employee.status == status_filter)
    if search_query:
        query = query.filter(
            db.or_(
                Employee.employee_id.ilike(f'%{search_query}%'),
                Employee.first_name.ilike(f'%{search_query}%'),
                Employee.last_name.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%'),
                Employee.designation.ilike(f'%{search_query}%')
            )
        )

    employees_list = query.order_by(Employee.employee_id.asc()).all()
    departments = Department.query.filter_by(is_active=True).all()

    return render_template(
        'manager/employees.html',
        employees=employees_list,
        departments=departments,
        dept_filter=dept_filter,
        status_filter=status_filter,
        search_query=search_query
    )

@manager.route('/employee/<int:id>')
def employee_detail(id):
    emp = Employee.query.get_or_404(id)
    current_year = date.today().year

    balances = LeaveBalance.query.filter_by(employee_id=emp.id, year=current_year).all()
    requests_history = LeaveRequest.query.filter_by(employee_id=emp.id).order_by(LeaveRequest.applied_at.desc()).all()
    
    # Recent attendance (last 30 days)
    recent_attendance = Attendance.query.filter_by(employee_id=emp.id).order_by(Attendance.date.desc()).limit(30).all()

    return render_template(
        'manager/employee_detail.html',
        employee=emp,
        balances=balances,
        requests=requests_history,
        attendance=recent_attendance
    )

@manager.route('/calendar')
def calendar():
    departments = Department.query.filter_by(is_active=True).all()
    return render_template('manager/calendar.html', departments=departments)

@manager.route('/api/calendar-events')
def api_calendar_events():
    dept_id = request.args.get('department_id', type=int)
    events = []

    # Holidays
    holidays = Holiday.query.all()
    for h in holidays:
        events.append({
            'title': f'Holiday: {h.name}',
            'start': h.date.strftime('%Y-%m-%d'),
            'end': h.date.strftime('%Y-%m-%d'),
            'type': 'holiday',
            'color': '#8b5cf6',
            'description': h.description or ''
        })

    # Organization leaves
    query = LeaveRequest.query.join(Employee, Employee.id == LeaveRequest.employee_id)
    if dept_id:
        query = query.filter(Employee.department_id == dept_id)

    leaves = query.filter(LeaveRequest.status.in_(['Approved', 'Pending'])).all()
    for l in leaves:
        is_pending = (l.status == 'Pending')
        color = '#f59e0b' if is_pending else '#10b981'
        end_inclusive = (l.end_date + timedelta(days=1)).strftime('%Y-%m-%d')
        events.append({
            'title': f'{l.employee.full_name} ({l.leave_type.code} - {l.status})',
            'start': l.start_date.strftime('%Y-%m-%d'),
            'end': end_inclusive,
            'type': 'leave',
            'status': l.status,
            'color': color,
            'request_number': l.request_number,
            'reason': l.reason
        })

    return jsonify(events)

@manager.route('/attendance')
def attendance():
    target_date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        target_date = date.today()

    dept_filter = request.args.get('department', type=int)
    query = Employee.query.filter_by(status='Active')
    if dept_filter:
        query = query.filter_by(department_id=dept_filter)

    active_employees = query.all()
    records = []

    for emp in active_employees:
        att = Attendance.query.filter_by(employee_id=emp.id, date=target_date).first()
        records.append({
            'employee': emp,
            'attendance': att
        })

    departments = Department.query.filter_by(is_active=True).all()
    return render_template(
        'manager/attendance.html',
        records=records,
        target_date=target_date,
        departments=departments,
        dept_filter=dept_filter
    )
