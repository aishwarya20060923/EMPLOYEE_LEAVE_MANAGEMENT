from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='Employee')  # 'Admin', 'Manager', 'Employee'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    employee = db.relationship('Employee', backref='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employees = db.relationship('Employee', backref='department', lazy='dynamic')

    def __repr__(self):
        return f'<Department {self.name}>'


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    employee_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    joining_date = db.Column(db.Date, nullable=False, default=date.today)
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='Active', nullable=False)  # 'Active', 'Inactive'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Self-referential relationship for manager/subordinates
    manager = db.relationship('Employee', remote_side=[id], backref=db.backref('subordinates', lazy='dynamic'))

    leave_balances = db.relationship('LeaveBalance', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    leave_requests = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.employee_id', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    reviewed_requests = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.reviewed_by_id', backref='reviewed_by', lazy='dynamic')
    attendances = db.relationship('Attendance', backref='employee', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def email(self):
        return self.user.email if self.user else ''

    @property
    def role(self):
        return self.user.role if self.user else 'Employee'

    def __repr__(self):
        return f'<Employee {self.employee_id} - {self.full_name}>'


class LeaveType(db.Model):
    __tablename__ = 'leave_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    max_days = db.Column(db.Float, default=12.0, nullable=False)
    is_paid = db.Column(db.Boolean, default=True, nullable=False)
    carry_forward = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    balances = db.relationship('LeaveBalance', backref='leave_type', lazy='dynamic', cascade='all, delete-orphan')
    requests = db.relationship('LeaveRequest', backref='leave_type', lazy='dynamic')

    def __repr__(self):
        return f'<LeaveType {self.name} ({self.max_days} days)>'


class LeaveBalance(db.Model):
    __tablename__ = 'leave_balances'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False, default=lambda: datetime.utcnow().year)
    entitled_days = db.Column(db.Float, default=0.0, nullable=False)
    used_days = db.Column(db.Float, default=0.0, nullable=False)
    remaining_days = db.Column(db.Float, default=0.0, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'leave_type_id', 'year', name='uq_emp_leave_year'),
    )

    def update_balance(self):
        self.remaining_days = max(0.0, self.entitled_days - self.used_days)

    def __repr__(self):
        return f'<LeaveBalance Emp={self.employee_id} Type={self.leave_type_id} {self.remaining_days}/{self.entitled_days}>'


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'

    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_half_day = db.Column(db.Boolean, default=False, nullable=False)
    half_day_type = db.Column(db.String(20), nullable=True)  # 'First Half', 'Second Half'
    days_requested = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    attachment_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='Pending', nullable=False)  # 'Pending', 'Approved', 'Rejected', 'Cancelled'
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<LeaveRequest {self.request_number} - {self.status}>'


class Holiday(db.Model):
    __tablename__ = 'holidays'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_optional = db.Column(db.Boolean, default=False, nullable=False)  # Mandatory (False) or Optional (True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Holiday {self.name} on {self.date}>'


class Attendance(db.Model):
    __tablename__ = 'attendances'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Present', nullable=False)  # 'Present', 'Absent', 'Leave', 'Half Day', 'Holiday'
    check_in = db.Column(db.String(10), nullable=True)   # e.g. '09:15'
    check_out = db.Column(db.String(10), nullable=True)  # e.g. '18:00'
    notes = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'date', name='uq_emp_date_attendance'),
    )

    def __repr__(self):
        return f'<Attendance Emp={self.employee_id} Date={self.date} Status={self.status}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), default='info', nullable=False)  # 'info', 'success', 'warning', 'danger'
    link = db.Column(db.String(200), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Notification {self.title} (Read: {self.is_read})>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    user_email = db.Column(db.String(120), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    record_type = db.Column(db.String(50), nullable=True)
    record_id = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_email} at {self.timestamp}>'
