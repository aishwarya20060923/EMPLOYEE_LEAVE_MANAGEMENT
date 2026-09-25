import os
from datetime import datetime, date
from werkzeug.security import generate_password_hash
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.models import db, User, Employee, Department, LeaveType, LeaveBalance, LeaveRequest, Holiday, Attendance, AuditLog, Notification
from utils.helpers import login_required, role_required, get_current_user, get_current_employee, log_audit, create_notification

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.before_request
@login_required
@role_required(['Admin'])
def before_request():
    pass

@admin.route('/dashboard')
def dashboard():
    total_users = User.query.count()
    active_employees = Employee.query.filter_by(status='Active').count()
    total_departments = Department.query.count()
    total_leave_types = LeaveType.query.count()
    total_holidays = Holiday.query.count()
    pending_leaves = LeaveRequest.query.filter_by(status='Pending').count()
    total_requests = LeaveRequest.query.count()
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(8).all()
    recent_requests = LeaveRequest.query.order_by(LeaveRequest.applied_at.desc()).limit(6).all()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        active_employees=active_employees,
        total_departments=total_departments,
        total_leave_types=total_leave_types,
        total_holidays=total_holidays,
        pending_leaves=pending_leaves,
        total_requests=total_requests,
        recent_logs=recent_logs,
        recent_requests=recent_requests
    )

# --- EMPLOYEE MANAGEMENT ---
@admin.route('/employees')
def employees():
    dept_filter = request.args.get('department', type=int)
    role_filter = request.args.get('role', '').strip()
    status_filter = request.args.get('status', '').strip()
    search_query = request.args.get('search', '').strip()

    query = Employee.query.join(User, User.id == Employee.user_id)

    if dept_filter:
        query = query.filter(Employee.department_id == dept_filter)
    if role_filter:
        query = query.filter(User.role == role_filter)
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

    employees_list = query.order_by(Employee.id.desc()).all()
    departments = Department.query.filter_by(is_active=True).all()
    all_managers = Employee.query.join(User).filter(User.role.in_(['Manager', 'Admin']), Employee.status == 'Active').all()

    return render_template(
        'admin/employees.html',
        employees=employees_list,
        departments=departments,
        managers=all_managers,
        dept_filter=dept_filter,
        role_filter=role_filter,
        status_filter=status_filter,
        search_query=search_query
    )

@admin.route('/employees/add', methods=['GET', 'POST'])
def add_employee():
    departments = Department.query.filter_by(is_active=True).all()
    managers = Employee.query.join(User).filter(User.role.in_(['Manager', 'Admin']), Employee.status == 'Active').all()

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', 'Employee@123')
        role = request.form.get('role', 'Employee')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        department_id = request.form.get('department_id', type=int)
        designation = request.form.get('designation', '').strip()
        joining_date_str = request.form.get('joining_date')
        manager_id = request.form.get('manager_id', type=int)
        gender = request.form.get('gender')
        address = request.form.get('address', '').strip()

        if not email or not first_name or not last_name or not joining_date_str:
            flash('Please fill in all mandatory fields.', 'danger')
            return render_template('admin/employee_form.html', departments=departments, managers=managers, action='Add')

        if User.query.filter_by(email=email).first():
            flash('A user with this email address already exists.', 'danger')
            return render_template('admin/employee_form.html', departments=departments, managers=managers, action='Add')

        try:
            joining_date = datetime.strptime(joining_date_str, '%Y-%m-%d').date()
        except ValueError:
            joining_date = date.today()

        # Generate Employee ID e.g. EMP-101
        last_emp = Employee.query.order_by(Employee.id.desc()).first()
        next_num = (last_emp.id + 101) if last_emp else 101
        emp_code = f'EMP-{next_num:03d}'

        # Create User
        user = User(
            email=email,
            role=role,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Create Employee
        emp = Employee(
            user_id=user.id,
            employee_id=emp_code,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            department_id=department_id if department_id else None,
            designation=designation,
            joining_date=joining_date,
            manager_id=manager_id if manager_id else None,
            gender=gender,
            address=address,
            status='Active'
        )
        db.session.add(emp)
        db.session.flush()

        # Provision Leave Balances for all active Leave Types
        current_year = date.today().year
        active_types = LeaveType.query.filter_by(is_active=True).all()
        for lt in active_types:
            bal = LeaveBalance(
                employee_id=emp.id,
                leave_type_id=lt.id,
                year=current_year,
                entitled_days=lt.max_days,
                used_days=0.0,
                remaining_days=lt.max_days
            )
            db.session.add(bal)

        db.session.commit()

        log_audit(
            'Employee Created',
            record_type='Employee',
            record_id=emp.id,
            details=f'Created employee {emp.full_name} ({emp.employee_id}, {user.email}) as {role}'
        )

        flash(f'Employee {emp.full_name} ({emp.employee_id}) created successfully!', 'success')
        return redirect(url_for('admin.employees'))

    return render_template('admin/employee_form.html', departments=departments, managers=managers, action='Add')

@admin.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    emp = Employee.query.get_or_404(id)
    user = emp.user
    departments = Department.query.filter_by(is_active=True).all()
    managers = Employee.query.join(User).filter(User.role.in_(['Manager', 'Admin']), Employee.id != emp.id, Employee.status == 'Active').all()

    if request.method == 'POST':
        emp.first_name = request.form.get('first_name', '').strip()
        emp.last_name = request.form.get('last_name', '').strip()
        emp.phone = request.form.get('phone', '').strip()
        emp.department_id = request.form.get('department_id', type=int) or None
        emp.designation = request.form.get('designation', '').strip()
        emp.manager_id = request.form.get('manager_id', type=int) or None
        emp.gender = request.form.get('gender')
        emp.address = request.form.get('address', '').strip()

        role = request.form.get('role', user.role)
        user.role = role

        joining_date_str = request.form.get('joining_date')
        if joining_date_str:
            try:
                emp.joining_date = datetime.strptime(joining_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        new_password = request.form.get('new_password', '').strip()
        if new_password:
            user.set_password(new_password)
            flash('Password updated successfully.', 'info')

        db.session.commit()

        log_audit(
            'Employee Updated',
            record_type='Employee',
            record_id=emp.id,
            details=f'Updated details for {emp.full_name} ({emp.employee_id})'
        )

        flash(f'Employee {emp.full_name} updated successfully.', 'success')
        return redirect(url_for('admin.employees'))

    return render_template('admin/employee_form.html', employee=emp, departments=departments, managers=managers, action='Edit')

@admin.route('/employees/toggle-status/<int:id>', methods=['POST'])
def toggle_employee_status(id):
    emp = Employee.query.get_or_404(id)
    user = emp.user

    new_status = 'Inactive' if emp.status == 'Active' else 'Active'
    emp.status = new_status
    user.is_active = (new_status == 'Active')
    db.session.commit()

    log_audit(
        'Employee Status Changed',
        record_type='Employee',
        record_id=emp.id,
        details=f'Changed status of {emp.full_name} to {new_status}'
    )

    flash(f'Employee {emp.full_name} status set to {new_status}.', 'info')
    return redirect(url_for('admin.employees'))

# --- DEPARTMENT MANAGEMENT ---
@admin.route('/departments', methods=['GET', 'POST'])
def departments():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form.get('name', '').strip()
            code = request.form.get('code', '').strip().upper()
            description = request.form.get('description', '').strip()

            if not name or not code:
                flash('Department name and code are required.', 'danger')
            elif Department.query.filter((Department.name == name) | (Department.code == code)).first():
                flash('A department with that name or code already exists.', 'danger')
            else:
                dept = Department(name=name, code=code, description=description, is_active=True)
                db.session.add(dept)
                db.session.commit()
                log_audit('Department Created', record_type='Department', record_id=dept.id, details=f'Created {name} ({code})')
                flash(f'Department "{name}" created successfully.', 'success')

        elif action == 'edit':
            dept_id = request.form.get('dept_id', type=int)
            dept = Department.query.get_or_404(dept_id)
            dept.name = request.form.get('name', '').strip()
            dept.code = request.form.get('code', '').strip().upper()
            dept.description = request.form.get('description', '').strip()
            db.session.commit()
            log_audit('Department Updated', record_type='Department', record_id=dept.id, details=f'Updated department {dept.name}')
            flash('Department updated successfully.', 'success')

        elif action == 'toggle':
            dept_id = request.form.get('dept_id', type=int)
            dept = Department.query.get_or_404(dept_id)
            dept.is_active = not dept.is_active
            db.session.commit()
            status_text = 'activated' if dept.is_active else 'deactivated'
            log_audit('Department Status Changed', record_type='Department', record_id=dept.id, details=f'Department {dept.name} {status_text}')
            flash(f'Department "{dept.name}" {status_text}.', 'info')

        return redirect(url_for('admin.departments'))

    departments_list = Department.query.order_by(Department.name.asc()).all()
    return render_template('admin/departments.html', departments=departments_list)

# --- LEAVE TYPE MANAGEMENT ---
@admin.route('/leave-types', methods=['GET', 'POST'])
def leave_types():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form.get('name', '').strip()
            code = request.form.get('code', '').strip().upper()
            description = request.form.get('description', '').strip()
            max_days = request.form.get('max_days', type=float) or 12.0
            is_paid = bool(request.form.get('is_paid'))
            carry_forward = bool(request.form.get('carry_forward'))

            if not name or not code:
                flash('Leave type name and code are required.', 'danger')
            elif LeaveType.query.filter((LeaveType.name == name) | (LeaveType.code == code)).first():
                flash('A leave type with that name or code already exists.', 'danger')
            else:
                lt = LeaveType(
                    name=name,
                    code=code,
                    description=description,
                    max_days=max_days,
                    is_paid=is_paid,
                    carry_forward=carry_forward,
                    is_active=True
                )
                db.session.add(lt)
                db.session.flush()

                # Automatically create balances for all active employees for this new leave type
                current_year = date.today().year
                for emp in Employee.query.filter_by(status='Active').all():
                    existing_b = LeaveBalance.query.filter_by(employee_id=emp.id, leave_type_id=lt.id, year=current_year).first()
                    if not existing_b:
                        b = LeaveBalance(
                            employee_id=emp.id,
                            leave_type_id=lt.id,
                            year=current_year,
                            entitled_days=max_days,
                            used_days=0.0,
                            remaining_days=max_days
                        )
                        db.session.add(b)

                db.session.commit()
                log_audit('Leave Type Created', record_type='LeaveType', record_id=lt.id, details=f'Created leave type {name} ({max_days} days)')
                flash(f'Leave type "{name}" created and provisioned for active employees!', 'success')

        elif action == 'edit':
            lt_id = request.form.get('lt_id', type=int)
            lt = LeaveType.query.get_or_404(lt_id)
            lt.name = request.form.get('name', '').strip()
            lt.code = request.form.get('code', '').strip().upper()
            lt.description = request.form.get('description', '').strip()
            lt.max_days = request.form.get('max_days', type=float) or lt.max_days
            lt.is_paid = bool(request.form.get('is_paid'))
            lt.carry_forward = bool(request.form.get('carry_forward'))
            db.session.commit()
            log_audit('Leave Type Updated', record_type='LeaveType', record_id=lt.id, details=f'Updated leave type {lt.name}')
            flash('Leave type updated successfully.', 'success')

        elif action == 'toggle':
            lt_id = request.form.get('lt_id', type=int)
            lt = LeaveType.query.get_or_404(lt_id)
            lt.is_active = not lt.is_active
            db.session.commit()
            status_text = 'activated' if lt.is_active else 'deactivated'
            log_audit('Leave Type Status Changed', record_type='LeaveType', record_id=lt.id, details=f'Leave type {lt.name} {status_text}')
            flash(f'Leave type "{lt.name}" {status_text}.', 'info')

        return redirect(url_for('admin.leave_types'))

    types_list = LeaveType.query.all()
    return render_template('admin/leave_types.html', leave_types=types_list)

# --- HOLIDAY MANAGEMENT ---
@admin.route('/holidays', methods=['GET', 'POST'])
def holidays():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form.get('name', '').strip()
            date_str = request.form.get('date')
            description = request.form.get('description', '').strip()
            is_optional = bool(request.form.get('is_optional'))

            if not name or not date_str:
                flash('Holiday name and date are required.', 'danger')
            else:
                try:
                    h_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    if Holiday.query.filter_by(date=h_date).first():
                        flash('A holiday already exists on this date.', 'danger')
                    else:
                        hol = Holiday(name=name, date=h_date, description=description, is_optional=is_optional)
                        db.session.add(hol)
                        db.session.commit()
                        log_audit('Holiday Created', record_type='Holiday', record_id=hol.id, details=f'Added holiday {name} on {h_date}')
                        flash(f'Holiday "{name}" added successfully.', 'success')
                except ValueError:
                    flash('Invalid date provided.', 'danger')

        elif action == 'edit':
            hol_id = request.form.get('hol_id', type=int)
            hol = Holiday.query.get_or_404(hol_id)
            hol.name = request.form.get('name', '').strip()
            date_str = request.form.get('date')
            if date_str:
                try:
                    hol.date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            hol.description = request.form.get('description', '').strip()
            hol.is_optional = bool(request.form.get('is_optional'))
            db.session.commit()
            log_audit('Holiday Updated', record_type='Holiday', record_id=hol.id, details=f'Updated holiday {hol.name}')
            flash('Holiday updated successfully.', 'success')

        elif action == 'delete':
            hol_id = request.form.get('hol_id', type=int)
            hol = Holiday.query.get_or_404(hol_id)
            name = hol.name
            db.session.delete(hol)
            db.session.commit()
            log_audit('Holiday Deleted', record_type='Holiday', record_id=hol_id, details=f'Deleted holiday {name}')
            flash(f'Holiday "{name}" deleted.', 'info')

        return redirect(url_for('admin.holidays'))

    holidays_list = Holiday.query.order_by(Holiday.date.asc()).all()
    return render_template('admin/holidays.html', holidays=holidays_list)

# --- AUDIT LOGS ---
@admin.route('/audit-logs')
def audit_logs():
    action_filter = request.args.get('action', '').strip()
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)

    query = AuditLog.query

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    if search_query:
        query = query.filter(
            db.or_(
                AuditLog.user_email.ilike(f'%{search_query}%'),
                AuditLog.action.ilike(f'%{search_query}%'),
                AuditLog.details.ilike(f'%{search_query}%')
            )
        )

    logs = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=20, error_out=False)
    actions = [r[0] for r in db.session.query(AuditLog.action).distinct().all()]

    return render_template(
        'admin/audit_logs.html',
        logs=logs,
        actions=actions,
        action_filter=action_filter,
        search_query=search_query
    )

# --- SYSTEM SETTINGS ---
@admin.route('/settings')
def settings():
    return render_template('admin/settings.html')
