import os
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from models.models import db, User, Employee, LeaveType, LeaveBalance, LeaveRequest, Holiday, Attendance, Notification
from utils.helpers import login_required, role_required, get_current_user, get_current_employee, calculate_working_days, check_leave_conflict, generate_request_number, log_audit, create_notification, allowed_file

employee = Blueprint('employee', __name__, url_prefix='/employee')

@employee.before_request
@login_required
def before_request():
    pass

@employee.route('/dashboard')
def dashboard():
    emp = get_current_employee()
    if not emp:
        flash('Employee profile not found.', 'danger')
        return redirect(url_for('auth.logout'))

    current_year = date.today().year

    # KPI 1: Balances
    balances = LeaveBalance.query.filter_by(employee_id=emp.id, year=current_year).all()
    total_entitlement = sum(b.entitled_days for b in balances)
    total_used = sum(b.used_days for b in balances)
    total_remaining = sum(b.remaining_days for b in balances)

    # Balance items with percentage
    balance_data = []
    for b in balances:
        pct = (b.used_days / b.entitled_days * 100) if b.entitled_days > 0 else 0
        balance_data.append({
            'type_name': b.leave_type.name,
            'code': b.leave_type.code,
            'is_paid': b.leave_type.is_paid,
            'entitled': b.entitled_days,
            'used': b.used_days,
            'remaining': b.remaining_days,
            'percent_used': round(pct, 1)
        })

    # KPI 2: Requests
    pending_count = LeaveRequest.query.filter_by(employee_id=emp.id, status='Pending').count()
    approved_count = LeaveRequest.query.filter_by(employee_id=emp.id, status='Approved').count()
    rejected_count = LeaveRequest.query.filter_by(employee_id=emp.id, status='Rejected').count()

    # Recent leave requests
    recent_requests = LeaveRequest.query.filter_by(employee_id=emp.id).order_by(LeaveRequest.applied_at.desc()).limit(5).all()

    # Upcoming approved leaves
    upcoming_leaves = LeaveRequest.query.filter(
        LeaveRequest.employee_id == emp.id,
        LeaveRequest.status == 'Approved',
        LeaveRequest.start_date >= date.today()
    ).order_by(LeaveRequest.start_date.asc()).limit(4).all()

    # Attendance stats for current month
    today = date.today()
    first_of_month = date(today.year, today.month, 1)
    month_attendances = Attendance.query.filter(
        Attendance.employee_id == emp.id,
        Attendance.date >= first_of_month,
        Attendance.date <= today
    ).all()

    present_days = sum(1 for a in month_attendances if a.status in ['Present', 'Half Day'])
    leave_days = sum(1 for a in month_attendances if a.status == 'Leave')
    absent_days = sum(1 for a in month_attendances if a.status == 'Absent')
    total_workdays_recorded = len(month_attendances)
    attendance_rate = round((present_days / total_workdays_recorded * 100), 1) if total_workdays_recorded > 0 else 100.0

    today_attendance = Attendance.query.filter_by(employee_id=emp.id, date=today).first()

    return render_template(
        'employee/dashboard.html',
        employee=emp,
        total_entitlement=total_entitlement,
        total_used=total_used,
        total_remaining=total_remaining,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        balances=balance_data,
        recent_requests=recent_requests,
        upcoming_leaves=upcoming_leaves,
        attendance_rate=attendance_rate,
        present_days=present_days,
        leave_days=leave_days,
        absent_days=absent_days,
        today_attendance=today_attendance
    )

@employee.route('/apply-leave', methods=['GET', 'POST'])
def apply_leave():
    emp = get_current_employee()
    if not emp:
        flash('Employee profile not found.', 'danger')
        return redirect(url_for('auth.logout'))

    current_year = date.today().year
    leave_types = LeaveType.query.filter_by(is_active=True).all()
    balances = {b.leave_type_id: b for b in LeaveBalance.query.filter_by(employee_id=emp.id, year=current_year).all()}

    # Holidays list for client side display
    upcoming_holidays = Holiday.query.filter(Holiday.date >= date.today()).order_by(Holiday.date.asc()).limit(6).all()

    if request.method == 'POST':
        leave_type_id = request.form.get('leave_type_id', type=int)
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        is_half_day = bool(request.form.get('is_half_day'))
        half_day_type = request.form.get('half_day_type', 'First Half')
        reason = request.form.get('reason', '').strip()

        # Basic validations
        if not leave_type_id or not start_date_str or not end_date_str or not reason:
            flash('Please fill in all required fields.', 'danger')
            return render_template('employee/apply_leave.html', leave_types=leave_types, balances=balances, upcoming_holidays=upcoming_holidays)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format provided.', 'danger')
            return render_template('employee/apply_leave.html', leave_types=leave_types, balances=balances, upcoming_holidays=upcoming_holidays)

        # Date validations
        if end_date < start_date:
            flash('End date cannot be earlier than start date.', 'danger')
            return render_template('employee/apply_leave.html', leave_types=leave_types, balances=balances, upcoming_holidays=upcoming_holidays)

        # Smart working days calculation (excluding weekends and mandatory holidays)
        working_days, weekends_skipped, holidays_skipped = calculate_working_days(start_date, end_date, is_half_day)

        if working_days <= 0:
            flash('The selected date range contains no working days (all days are weekends or national holidays).', 'warning')
            return render_template('employee/apply_leave.html', leave_types=leave_types, balances=balances, upcoming_holidays=upcoming_holidays)

        # Check Leave Balance
        balance = LeaveBalance.query.filter_by(employee_id=emp.id, leave_type_id=leave_type_id, year=start_date.year).first()
        selected_type = db.session.get(LeaveType, leave_type_id)

        if not balance or balance.remaining_days < working_days:
            avail = balance.remaining_days if balance else 0.0
            flash(f'Insufficient leave balance for {selected_type.name}. You have {avail} days available, but requested {working_days} working days.', 'danger')
            return render_template('employee/apply_leave.html', leave_types=leave_types, balances=balances, upcoming_holidays=upcoming_holidays)

        # Check for Overlapping Leave Conflict
        conflict = check_leave_conflict(emp.id, start_date, end_date)
        if conflict:
            flash(f'Leave request overlaps with an existing {conflict.status} request ({conflict.request_number}: {conflict.start_date.strftime("%d %b %Y")} to {conflict.end_date.strftime("%d %b %Y")}).', 'danger')
            return render_template('employee/apply_leave.html', leave_types=leave_types, balances=balances, upcoming_holidays=upcoming_holidays)

        # Handle optional file attachment
        attachment_filename = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(f"{emp.employee_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(upload_path)
                    attachment_filename = filename
                else:
                    flash('Invalid attachment format. Allowed formats: PNG, JPG, PDF, DOC, DOCX.', 'warning')
                    return render_template('employee/apply_leave.html', leave_types=leave_types, balances=balances, upcoming_holidays=upcoming_holidays)

        # Create Leave Request
        req_num = generate_request_number()
        leave_req = LeaveRequest(
            request_number=req_num,
            employee_id=emp.id,
            leave_type_id=leave_type_id,
            start_date=start_date,
            end_date=end_date,
            is_half_day=is_half_day,
            half_day_type=half_day_type if is_half_day else None,
            days_requested=working_days,
            reason=reason,
            attachment_filename=attachment_filename,
            status='Pending',
            applied_at=datetime.utcnow()
        )
        db.session.add(leave_req)
        db.session.commit()

        # Audit Log
        log_audit(
            'Leave Applied',
            record_type='LeaveRequest',
            record_id=leave_req.id,
            details=f'{emp.full_name} applied for {working_days} days of {selected_type.name} ({start_date} to {end_date})'
        )

        # Notify Employee
        create_notification(
            user_id=emp.user_id,
            title='Leave Application Submitted',
            message=f'Your leave request {req_num} for {working_days} days of {selected_type.name} has been submitted successfully and is pending review.',
            category='info',
            link=url_for('employee.my_leaves')
        )

        # Notify Manager if exists, or all Managers/Admins
        if emp.manager and emp.manager.user_id:
            create_notification(
                user_id=emp.manager.user_id,
                title='New Leave Request Pending Review',
                message=f'{emp.full_name} submitted a leave request {req_num} ({working_days} days from {start_date} to {end_date}).',
                category='warning',
                link=url_for('manager.leave_requests')
            )
        else:
            # Notify HR/Admin users
            managers = User.query.filter(User.role.in_(['Manager', 'Admin']), User.is_active == True).all()
            for m in managers:
                create_notification(
                    user_id=m.id,
                    title='New Leave Request Pending Review',
                    message=f'{emp.full_name} submitted a leave request {req_num} ({working_days} days).',
                    category='warning',
                    link=url_for('manager.leave_requests')
                )

        flash(f'Leave request {req_num} for {working_days} working days submitted successfully!', 'success')
        return redirect(url_for('employee.my_leaves'))

    return render_template(
        'employee/apply_leave.html',
        leave_types=leave_types,
        balances=balances,
        upcoming_holidays=upcoming_holidays
    )

@employee.route('/api/calculate-days', methods=['POST'])
def api_calculate_days():
    data = request.get_json() or {}
    start_str = data.get('start_date')
    end_str = data.get('end_date')
    is_half_day = bool(data.get('is_half_day'))

    if not start_str or not end_str:
        return jsonify({'error': 'Missing dates'}), 400

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    if end_date < start_date:
        return jsonify({'days': 0, 'error': 'End date cannot be earlier than start date'}), 400

    working_days, weekends, holidays = calculate_working_days(start_date, end_date, is_half_day)

    return jsonify({
        'days': working_days,
        'weekends_count': len(weekends),
        'holidays_count': len(holidays),
        'holidays': [{'date': h[0].strftime('%Y-%m-%d'), 'name': h[1]} for h in holidays]
    })

@employee.route('/my-leaves')
def my_leaves():
    emp = get_current_employee()
    if not emp:
        flash('Employee profile not found.', 'danger')
        return redirect(url_for('auth.logout'))

    # Filters
    status_filter = request.args.get('status', '').strip()
    leave_type_filter = request.args.get('leave_type', type=int)
    search_query = request.args.get('search', '').strip()

    query = LeaveRequest.query.filter_by(employee_id=emp.id)

    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)
    if leave_type_filter:
        query = query.filter(LeaveRequest.leave_type_id == leave_type_filter)
    if search_query:
        query = query.filter(
            db.or_(
                LeaveRequest.request_number.ilike(f'%{search_query}%'),
                LeaveRequest.reason.ilike(f'%{search_query}%')
            )
        )

    leave_requests = query.order_by(LeaveRequest.applied_at.desc()).all()
    leave_types = LeaveType.query.all()

    return render_template(
        'employee/my_leaves.html',
        leave_requests=leave_requests,
        leave_types=leave_types,
        status_filter=status_filter,
        leave_type_filter=leave_type_filter,
        search_query=search_query,
        today=date.today()
    )

@employee.route('/cancel-leave/<int:request_id>', methods=['POST'])
def cancel_leave(request_id):
    emp = get_current_employee()
    leave_req = LeaveRequest.query.filter_by(id=request_id, employee_id=emp.id).first_or_404()

    cancellation_reason = request.form.get('cancellation_reason', 'Cancelled by employee').strip()

    # Rule checks:
    # 1. Pending requests can always be cancelled
    # 2. Approved requests can only be cancelled if start_date >= today (future approved leave)
    # 3. Past approved leaves cannot be cancelled
    if leave_req.status == 'Cancelled':
        flash('This leave request has already been cancelled.', 'info')
        return redirect(url_for('employee.my_leaves'))

    if leave_req.status == 'Rejected':
        flash('Rejected leave requests cannot be cancelled.', 'warning')
        return redirect(url_for('employee.my_leaves'))

    if leave_req.status == 'Approved':
        if leave_req.start_date < date.today():
            flash('Cannot cancel leave that has already commenced or occurred in the past.', 'danger')
            return redirect(url_for('employee.my_leaves'))

        # Restore leave balance
        balance = LeaveBalance.query.filter_by(
            employee_id=emp.id,
            leave_type_id=leave_req.leave_type_id,
            year=leave_req.start_date.year
        ).first()

        if balance:
            balance.used_days = max(0.0, balance.used_days - leave_req.days_requested)
            balance.update_balance()

    leave_req.status = 'Cancelled'
    leave_req.cancelled_at = datetime.utcnow()
    leave_req.cancellation_reason = cancellation_reason
    db.session.commit()

    log_audit(
        'Leave Cancelled',
        record_type='LeaveRequest',
        record_id=leave_req.id,
        details=f'{emp.full_name} cancelled {leave_req.request_number} (reason: {cancellation_reason})'
    )

    create_notification(
        user_id=emp.user_id,
        title='Leave Request Cancelled',
        message=f'Your leave request {leave_req.request_number} has been cancelled successfully and balances updated.',
        category='warning',
        link=url_for('employee.my_leaves')
    )

    flash(f'Leave request {leave_req.request_number} has been cancelled successfully.', 'success')
    return redirect(url_for('employee.my_leaves'))

@employee.route('/calendar')
def calendar():
    return render_template('employee/calendar.html')

@employee.route('/api/calendar-events')
def api_calendar_events():
    emp = get_current_employee()
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
            'is_optional': h.is_optional,
            'description': h.description or ''
        })

    # Employee leaves
    leaves = LeaveRequest.query.filter_by(employee_id=emp.id).all()
    for l in leaves:
        color_map = {
            'Approved': '#10b981',
            'Pending': '#f59e0b',
            'Rejected': '#ef4444',
            'Cancelled': '#6b7280'
        }
        # Add 1 day to end for inclusive display in standard calendar
        end_inclusive = (l.end_date + timedelta(days=1)).strftime('%Y-%m-%d')
        events.append({
            'title': f'{l.leave_type.code}: {l.status} ({l.days_requested}d)',
            'start': l.start_date.strftime('%Y-%m-%d'),
            'end': end_inclusive,
            'type': 'leave',
            'status': l.status,
            'color': color_map.get(l.status, '#3b82f6'),
            'request_number': l.request_number,
            'reason': l.reason
        })

    return jsonify(events)

@employee.route('/attendance', methods=['GET', 'POST'])
def attendance():
    emp = get_current_employee()
    today = date.today()

    if request.method == 'POST':
        action = request.form.get('action')
        now_time = datetime.now().strftime('%H:%M')

        att = Attendance.query.filter_by(employee_id=emp.id, date=today).first()
        if not att:
            att = Attendance(
                employee_id=emp.id,
                date=today,
                status='Present',
                check_in=now_time
            )
            db.session.add(att)
            flash(f'Check-in successful at {now_time}. Marked as Present today.', 'success')
        elif action == 'checkout' and not att.check_out:
            att.check_out = now_time
            flash(f'Check-out recorded at {now_time}.', 'info')
        else:
            flash('Attendance already recorded for today.', 'info')

        db.session.commit()
        return redirect(url_for('employee.attendance'))

    # Retrieve attendance history for past 60 days
    sixty_days_ago = today - timedelta(days=60)
    attendance_records = Attendance.query.filter(
        Attendance.employee_id == emp.id,
        Attendance.date >= sixty_days_ago
    ).order_by(Attendance.date.desc()).all()

    today_record = Attendance.query.filter_by(employee_id=emp.id, date=today).first()

    return render_template(
        'employee/attendance.html',
        records=attendance_records,
        today_record=today_record,
        today=today
    )

@employee.route('/notifications')
def notifications():
    user = get_current_user()
    notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    return render_template('employee/notifications.html', notifications=notifs)

@employee.route('/notifications/read/<int:id>', methods=['POST'])
def mark_notification_read(id):
    user = get_current_user()
    notif = Notification.query.filter_by(id=id, user_id=user.id).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'status': 'ok'})

@employee.route('/notifications/read-all', methods=['POST'])
def mark_all_notifications_read():
    user = get_current_user()
    Notification.query.filter_by(user_id=user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('employee.notifications'))

@employee.route('/profile', methods=['GET', 'POST'])
def profile():
    emp = get_current_employee()
    user = emp.user

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_info':
            phone = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()
            emp.phone = phone
            emp.address = address
            db.session.commit()
            log_audit('Profile Updated', record_type='Employee', record_id=emp.id, details='Updated contact details')
            flash('Profile details updated successfully.', 'success')

        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')

            if not user.check_password(current_pw):
                flash('Current password entered is incorrect.', 'danger')
            elif len(new_pw) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
            elif new_pw != confirm_pw:
                flash('New password and confirmation do not match.', 'danger')
            else:
                user.set_password(new_pw)
                db.session.commit()
                log_audit('Password Changed', record_type='User', record_id=user.id, details='User changed password')
                flash('Password changed successfully!', 'success')

        return redirect(url_for('employee.profile'))

    balances = LeaveBalance.query.filter_by(employee_id=emp.id, year=date.today().year).all()
    return render_template('employee/profile.html', employee=emp, balances=balances)
