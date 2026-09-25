import io
import csv
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, make_response
from models.models import db, User, Employee, Department, LeaveType, LeaveBalance, LeaveRequest, Attendance
from utils.helpers import login_required, role_required

reports = Blueprint('reports', __name__, url_prefix='/reports')

@reports.before_request
@login_required
@role_required(['Manager', 'Admin'])
def before_request():
    pass

@reports.route('/')
def index():
    report_type = request.args.get('report_type', 'leave_requests')
    dept_filter = request.args.get('department', type=int)
    emp_filter = request.args.get('employee', type=int)
    type_filter = request.args.get('leave_type', type=int)
    status_filter = request.args.get('status', '').strip()
    from_date_str = request.args.get('from_date', '')
    to_date_str = request.args.get('to_date', '')

    departments = Department.query.filter_by(is_active=True).all()
    employees = Employee.query.filter_by(status='Active').order_by(Employee.first_name.asc()).all()
    leave_types = LeaveType.query.all()

    # Parse dates if provided
    from_date = None
    to_date = None
    if from_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    if to_date_str:
        try:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    records = []
    summary = {}

    if report_type == 'leave_requests':
        query = LeaveRequest.query.join(Employee, Employee.id == LeaveRequest.employee_id)
        if dept_filter:
            query = query.filter(Employee.department_id == dept_filter)
        if emp_filter:
            query = query.filter(Employee.id == emp_filter)
        if type_filter:
            query = query.filter(LeaveRequest.leave_type_id == type_filter)
        if status_filter:
            query = query.filter(LeaveRequest.status == status_filter)
        if from_date:
            query = query.filter(LeaveRequest.start_date >= from_date)
        if to_date:
            query = query.filter(LeaveRequest.end_date <= to_date)

        records = query.order_by(LeaveRequest.applied_at.desc()).all()

        summary['total_records'] = len(records)
        summary['total_days'] = sum(r.days_requested for r in records)
        summary['approved_count'] = sum(1 for r in records if r.status == 'Approved')
        summary['pending_count'] = sum(1 for r in records if r.status == 'Pending')
        summary['rejected_count'] = sum(1 for r in records if r.status == 'Rejected')

    elif report_type == 'balances':
        query = LeaveBalance.query.join(Employee, Employee.id == LeaveBalance.employee_id)
        if dept_filter:
            query = query.filter(Employee.department_id == dept_filter)
        if emp_filter:
            query = query.filter(Employee.id == emp_filter)
        if type_filter:
            query = query.filter(LeaveBalance.leave_type_id == type_filter)

        current_year = date.today().year
        records = query.filter(LeaveBalance.year == current_year).order_by(Employee.employee_id.asc()).all()

        summary['total_records'] = len(records)
        summary['total_entitled'] = sum(b.entitled_days for b in records)
        summary['total_used'] = sum(b.used_days for b in records)
        summary['total_remaining'] = sum(b.remaining_days for b in records)

    elif report_type == 'attendance':
        query = Attendance.query.join(Employee, Employee.id == Attendance.employee_id)
        if dept_filter:
            query = query.filter(Employee.department_id == dept_filter)
        if emp_filter:
            query = query.filter(Employee.id == emp_filter)
        if from_date:
            query = query.filter(Attendance.date >= from_date)
        if to_date:
            query = query.filter(Attendance.date <= to_date)
        else:
            # Default to last 30 days
            query = query.filter(Attendance.date >= date.today() - timedelta(days=30))

        records = query.order_by(Attendance.date.desc()).all()

        summary['total_records'] = len(records)
        summary['present_count'] = sum(1 for a in records if a.status in ['Present', 'Half Day'])
        summary['leave_count'] = sum(1 for a in records if a.status == 'Leave')
        summary['absent_count'] = sum(1 for a in records if a.status == 'Absent')

    return render_template(
        'reports/index.html',
        report_type=report_type,
        departments=departments,
        employees=employees,
        leave_types=leave_types,
        records=records,
        summary=summary,
        dept_filter=dept_filter,
        emp_filter=emp_filter,
        type_filter=type_filter,
        status_filter=status_filter,
        from_date=from_date_str,
        to_date=to_date_str
    )

@reports.route('/export-csv')
def export_csv():
    report_type = request.args.get('report_type', 'leave_requests')
    dept_filter = request.args.get('department', type=int)
    emp_filter = request.args.get('employee', type=int)
    type_filter = request.args.get('leave_type', type=int)
    status_filter = request.args.get('status', '').strip()
    from_date_str = request.args.get('from_date', '')
    to_date_str = request.args.get('to_date', '')

    from_date = None
    to_date = None
    if from_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    if to_date_str:
        try:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    si = io.StringIO()
    cw = csv.writer(si)

    filename = f'{report_type}_report_{date.today().strftime("%Y%m%d")}.csv'

    if report_type == 'leave_requests':
        cw.writerow(['Request ID', 'Employee ID', 'Employee Name', 'Department', 'Leave Type', 'Start Date', 'End Date', 'Days', 'Status', 'Reason', 'Applied Date', 'Reviewed By', 'Review Date'])
        query = LeaveRequest.query.join(Employee, Employee.id == LeaveRequest.employee_id)
        if dept_filter:
            query = query.filter(Employee.department_id == dept_filter)
        if emp_filter:
            query = query.filter(Employee.id == emp_filter)
        if type_filter:
            query = query.filter(LeaveRequest.leave_type_id == type_filter)
        if status_filter:
            query = query.filter(LeaveRequest.status == status_filter)
        if from_date:
            query = query.filter(LeaveRequest.start_date >= from_date)
        if to_date:
            query = query.filter(LeaveRequest.end_date <= to_date)

        for r in query.order_by(LeaveRequest.applied_at.desc()).all():
            cw.writerow([
                r.request_number,
                r.employee.employee_id,
                r.employee.full_name,
                r.employee.department.name if r.employee.department else 'N/A',
                r.leave_type.name,
                r.start_date.strftime('%Y-%m-%d'),
                r.end_date.strftime('%Y-%m-%d'),
                r.days_requested,
                r.status,
                r.reason.replace('\n', ' '),
                r.applied_at.strftime('%Y-%m-%d %H:%M'),
                r.reviewed_by.full_name if r.reviewed_by else 'N/A',
                r.reviewed_at.strftime('%Y-%m-%d %H:%M') if r.reviewed_at else 'N/A'
            ])

    elif report_type == 'balances':
        cw.writerow(['Employee ID', 'Employee Name', 'Department', 'Leave Type', 'Entitled Days', 'Used Days', 'Remaining Days', 'Year'])
        query = LeaveBalance.query.join(Employee, Employee.id == LeaveBalance.employee_id)
        if dept_filter:
            query = query.filter(Employee.department_id == dept_filter)
        if emp_filter:
            query = query.filter(Employee.id == emp_filter)
        if type_filter:
            query = query.filter(LeaveBalance.leave_type_id == type_filter)

        for b in query.order_by(Employee.employee_id.asc()).all():
            cw.writerow([
                b.employee.employee_id,
                b.employee.full_name,
                b.employee.department.name if b.employee.department else 'N/A',
                b.leave_type.name,
                b.entitled_days,
                b.used_days,
                b.remaining_days,
                b.year
            ])

    elif report_type == 'attendance':
        cw.writerow(['Date', 'Employee ID', 'Employee Name', 'Department', 'Status', 'Check In', 'Check Out', 'Notes'])
        query = Attendance.query.join(Employee, Employee.id == Attendance.employee_id)
        if dept_filter:
            query = query.filter(Employee.department_id == dept_filter)
        if emp_filter:
            query = query.filter(Employee.id == emp_filter)
        if from_date:
            query = query.filter(Attendance.date >= from_date)
        if to_date:
            query = query.filter(Attendance.date <= to_date)

        for a in query.order_by(Attendance.date.desc()).all():
            cw.writerow([
                a.date.strftime('%Y-%m-%d'),
                a.employee.employee_id,
                a.employee.full_name,
                a.employee.department.name if a.employee.department else 'N/A',
                a.status,
                a.check_in or '',
                a.check_out or '',
                a.notes or ''
            ])

    output = make_response(si.getvalue())
    output.headers['Content-Disposition'] = f'attachment; filename={filename}'
    output.headers['Content-type'] = 'text/csv; charset=utf-8'
    return output
