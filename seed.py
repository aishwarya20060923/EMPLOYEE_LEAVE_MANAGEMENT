from datetime import datetime, date, timedelta
from app import create_app
from models.models import db, User, Department, Employee, LeaveType, LeaveBalance, LeaveRequest, Holiday, Attendance, Notification, AuditLog

app = create_app()

def seed_database():
    with app.app_context():
        print("Resetting database...")
        db.drop_all()
        db.create_all()

        current_year = date.today().year

        # 1. DEPARTMENTS
        departments_data = [
            {'name': 'Information Technology', 'code': 'IT', 'description': 'Software engineering, cloud infrastructure, and technical support.'},
            {'name': 'Human Resources', 'code': 'HR', 'description': 'Talent management, employee relations, recruitment, and payroll.'},
            {'name': 'Finance & Accounts', 'code': 'FIN', 'description': 'Financial planning, accounting, tax, and auditing.'},
            {'name': 'Marketing & Sales', 'code': 'MKT', 'description': 'Brand management, sales enablement, campaigns, and customer outreach.'},
            {'name': 'Operations', 'code': 'OPS', 'description': 'Supply chain, business workflows, quality management, and facilities.'}
        ]
        dept_objects = {}
        for d in departments_data:
            dept = Department(name=d['name'], code=d['code'], description=d['description'], is_active=True)
            db.session.add(dept)
            dept_objects[d['code']] = dept
        db.session.flush()

        # 2. LEAVE TYPES
        leave_types_data = [
            {'name': 'Casual Leave', 'code': 'CL', 'max_days': 12.0, 'is_paid': True, 'carry_forward': False, 'desc': 'For personal affairs, urgent matters, and short planned breaks.'},
            {'name': 'Sick Leave', 'code': 'SL', 'max_days': 10.0, 'is_paid': True, 'carry_forward': False, 'desc': 'For medical treatment, health recovery, and doctor appointments.'},
            {'name': 'Annual Leave', 'code': 'AL', 'max_days': 18.0, 'is_paid': True, 'carry_forward': True, 'desc': 'Earned annual paid time off for vacations and family travel.'},
            {'name': 'Work From Home', 'code': 'WFH', 'max_days': 24.0, 'is_paid': True, 'carry_forward': False, 'desc': 'Remote work allotment for approved projects and focus periods.'},
            {'name': 'Optional Holiday', 'code': 'OH', 'max_days': 3.0, 'is_paid': True, 'carry_forward': False, 'desc': 'Floating/restricted festival holidays from the organizational list.'},
            {'name': 'Maternity / Paternity', 'code': 'MAT', 'max_days': 30.0, 'is_paid': True, 'carry_forward': False, 'desc': 'Parental leave granted for childbirth and newborn care.'}
        ]
        lt_objects = {}
        for lt in leave_types_data:
            ltype = LeaveType(name=lt['name'], code=lt['code'], max_days=lt['max_days'], is_paid=lt['is_paid'], carry_forward=lt['carry_forward'], description=lt['desc'], is_active=True)
            db.session.add(ltype)
            lt_objects[lt['code']] = ltype
        db.session.flush()

        # 3. HOLIDAYS (Year 2026)
        holidays_data = [
            {'name': 'Republic Day', 'date': date(current_year, 1, 26), 'desc': 'National Holiday celebrating the Constitution of India', 'optional': False},
            {'name': 'Maha Shivratri', 'date': date(current_year, 2, 15), 'desc': 'Festival celebrating Lord Shiva', 'optional': True},
            {'name': 'Holi', 'date': date(current_year, 3, 4), 'desc': 'Festival of colors and spring', 'optional': False},
            {'name': 'Good Friday', 'date': date(current_year, 4, 3), 'desc': 'Christian holy day commemorating the crucifixion', 'optional': False},
            {'name': 'Eid-ul-Fitr', 'date': date(current_year, 3, 20), 'desc': 'Islamic festival marking the end of Ramadan', 'optional': False},
            {'name': 'Independence Day', 'date': date(current_year, 8, 15), 'desc': 'National Holiday celebrating Indian independence', 'optional': False},
            {'name': 'Gandhi Jayanti', 'date': date(current_year, 10, 2), 'desc': 'National Holiday honoring Mahatma Gandhi', 'optional': False},
            {'name': 'Dussehra / Vijayadashami', 'date': date(current_year, 10, 20), 'desc': 'Celebration of the victory of good over evil', 'optional': False},
            {'name': 'Diwali / Deepavali', 'date': date(current_year, 11, 8), 'desc': 'Festival of Lights', 'optional': False},
            {'name': 'Guru Nanak Jayanti', 'date': date(current_year, 11, 24), 'desc': 'Birth anniversary of Guru Nanak Dev Ji', 'optional': True},
            {'name': 'Christmas Day', 'date': date(current_year, 12, 25), 'desc': 'Celebration of the birth of Jesus Christ', 'optional': False}
        ]
        for h in holidays_data:
            hol = Holiday(name=h['name'], date=h['date'], description=h['desc'], is_optional=h['optional'])
            db.session.add(hol)
        db.session.flush()

        # 4. USERS & EMPLOYEES
        # Admin
        admin_user = User(email='admin@example.com', role='Admin', is_active=True)
        admin_user.set_password('Admin@123')
        db.session.add(admin_user)
        db.session.flush()

        admin_emp = Employee(
            user_id=admin_user.id,
            employee_id='EMP-001',
            first_name='Rajesh',
            last_name='Sharma',
            phone='+91 98765 43210',
            department_id=dept_objects['IT'].id,
            designation='Head of IT & Systems Administrator',
            joining_date=date(2021, 1, 15),
            gender='Male',
            address='Suite 402, Cyber Tower, Sector 62, Noida',
            status='Active'
        )
        db.session.add(admin_emp)
        db.session.flush()

        # Manager 1 (HR Manager)
        mgr_user1 = User(email='manager@example.com', role='Manager', is_active=True)
        mgr_user1.set_password('Manager@123')
        db.session.add(mgr_user1)
        db.session.flush()

        mgr_emp1 = Employee(
            user_id=mgr_user1.id,
            employee_id='EMP-002',
            first_name='Priya',
            last_name='Patel',
            phone='+91 98112 23344',
            department_id=dept_objects['HR'].id,
            designation='Senior Human Resources Manager',
            joining_date=date(2021, 6, 1),
            gender='Female',
            address='B-12 Green Glen Layout, Bellandur, Bengaluru',
            status='Active'
        )
        db.session.add(mgr_emp1)
        db.session.flush()

        # Manager 2 (Tech Manager)
        mgr_user2 = User(email='vikram.singh@example.com', role='Manager', is_active=True)
        mgr_user2.set_password('Manager@123')
        db.session.add(mgr_user2)
        db.session.flush()

        mgr_emp2 = Employee(
            user_id=mgr_user2.id,
            employee_id='EMP-003',
            first_name='Vikram',
            last_name='Singh',
            phone='+91 98223 34455',
            department_id=dept_objects['IT'].id,
            designation='Engineering Lead & Tech Manager',
            joining_date=date(2022, 2, 10),
            manager_id=admin_emp.id,
            gender='Male',
            address='Villa 15, Palm Meadows, Whitefield, Bengaluru',
            status='Active'
        )
        db.session.add(mgr_emp2)
        db.session.flush()

        # Employees (Rahul Verma = demo employee)
        employees_specs = [
            {
                'email': 'employee@example.com',
                'emp_id': 'EMP-004',
                'first': 'Rahul',
                'last': 'Verma',
                'phone': '+91 98334 45566',
                'dept': 'IT',
                'designation': 'Senior Full Stack Developer',
                'join': date(2023, 3, 1),
                'mgr': mgr_emp2.id,
                'gender': 'Male',
                'addr': 'Flat 304, Marvel Heights, HSR Layout, Bengaluru'
            },
            {
                'email': 'neha.gupta@example.com',
                'emp_id': 'EMP-005',
                'first': 'Neha',
                'last': 'Gupta',
                'phone': '+91 98445 56677',
                'dept': 'IT',
                'designation': 'UI/UX Product Designer',
                'join': date(2023, 5, 15),
                'mgr': mgr_emp2.id,
                'gender': 'Female',
                'addr': 'Flat 102, Shanti Vihar, Indiranagar, Bengaluru'
            },
            {
                'email': 'amit.nair@example.com',
                'emp_id': 'EMP-006',
                'first': 'Amit',
                'last': 'Nair',
                'phone': '+91 98556 67788',
                'dept': 'FIN',
                'designation': 'Financial Analyst & Auditor',
                'join': date(2022, 11, 20),
                'mgr': mgr_emp1.id,
                'gender': 'Male',
                'addr': 'Tower C, Regency Park, DLF Phase 4, Gurugram'
            },
            {
                'email': 'ananya.iyer@example.com',
                'emp_id': 'EMP-007',
                'first': 'Ananya',
                'last': 'Iyer',
                'phone': '+91 98667 78899',
                'dept': 'HR',
                'designation': 'Talent Acquisition Partner',
                'join': date(2023, 8, 1),
                'mgr': mgr_emp1.id,
                'gender': 'Female',
                'addr': '45 Rajaji Road, Alwarpet, Chennai'
            },
            {
                'email': 'sneha.reddy@example.com',
                'emp_id': 'EMP-008',
                'first': 'Sneha',
                'last': 'Reddy',
                'phone': '+91 98778 89900',
                'dept': 'MKT',
                'designation': 'Senior Growth Marketing Specialist',
                'join': date(2023, 1, 10),
                'mgr': mgr_emp1.id,
                'gender': 'Female',
                'addr': 'Plot 88, Jubilee Hills, Hyderabad'
            },
            {
                'email': 'karan.malhotra@example.com',
                'emp_id': 'EMP-009',
                'first': 'Karan',
                'last': 'Malhotra',
                'phone': '+91 98889 90011',
                'dept': 'IT',
                'designation': 'DevOps & Cloud Engineer',
                'join': date(2023, 9, 15),
                'mgr': mgr_emp2.id,
                'gender': 'Male',
                'addr': 'B-403, Windmills of Your Mind, EPIP Zone, Bengaluru'
            },
            {
                'email': 'pooja.deshmukh@example.com',
                'emp_id': 'EMP-010',
                'first': 'Pooja',
                'last': 'Deshmukh',
                'phone': '+91 98990 01122',
                'dept': 'FIN',
                'designation': 'Payroll & Accounts Executive',
                'join': date(2024, 1, 5),
                'mgr': mgr_emp1.id,
                'gender': 'Female',
                'addr': 'Flat 205, Silver Oak Apartments, Baner, Pune'
            },
            {
                'email': 'rohit.joshi@example.com',
                'emp_id': 'EMP-011',
                'first': 'Rohit',
                'last': 'Joshi',
                'phone': '+91 98101 12233',
                'dept': 'OPS',
                'designation': 'Operations & Logistics Lead',
                'join': date(2023, 4, 18),
                'mgr': mgr_emp1.id,
                'gender': 'Male',
                'addr': 'Sector 14, Vashi, Navi Mumbai'
            },
            {
                'email': 'deepak.mehta@example.com',
                'emp_id': 'EMP-012',
                'first': 'Deepak',
                'last': 'Mehta',
                'phone': '+91 98212 23344',
                'dept': 'MKT',
                'designation': 'Content Marketing Strategist',
                'join': date(2024, 2, 1),
                'mgr': mgr_emp1.id,
                'gender': 'Male',
                'addr': 'A-701, Oberoi Splendor, Andheri East, Mumbai'
            }
        ]

        all_created_employees = [admin_emp, mgr_emp1, mgr_emp2]

        for spec in employees_specs:
            u = User(email=spec['email'], role='Employee', is_active=True)
            u.set_password('Employee@123')
            db.session.add(u)
            db.session.flush()

            e = Employee(
                user_id=u.id,
                employee_id=spec['emp_id'],
                first_name=spec['first'],
                last_name=spec['last'],
                phone=spec['phone'],
                department_id=dept_objects[spec['dept']].id,
                designation=spec['designation'],
                joining_date=spec['join'],
                manager_id=spec['mgr'],
                gender=spec['gender'],
                address=spec['addr'],
                status='Active'
            )
            db.session.add(e)
            all_created_employees.append(e)

        db.session.flush()

        # 5. INITIALIZE LEAVE BALANCES FOR ALL EMPLOYEES
        all_ltypes = LeaveType.query.all()
        for emp in all_created_employees:
            for lt in all_ltypes:
                b = LeaveBalance(
                    employee_id=emp.id,
                    leave_type_id=lt.id,
                    year=current_year,
                    entitled_days=lt.max_days,
                    used_days=0.0,
                    remaining_days=lt.max_days
                )
                db.session.add(b)
        db.session.flush()

        # Helper to deduct balance on approved leaves
        def apply_approved_deduction(emp_id, lt_id, days):
            bal = LeaveBalance.query.filter_by(employee_id=emp_id, leave_type_id=lt_id, year=current_year).first()
            if bal:
                bal.used_days += days
                bal.update_balance()

        # 6. SEED REALISTIC LEAVE REQUESTS
        demo_emp = Employee.query.filter_by(employee_id='EMP-004').first()  # Rahul Verma
        neha_emp = Employee.query.filter_by(employee_id='EMP-005').first()  # Neha Gupta
        amit_emp = Employee.query.filter_by(employee_id='EMP-006').first()  # Amit Nair
        ananya_emp = Employee.query.filter_by(employee_id='EMP-007').first() # Ananya Iyer
        karan_emp = Employee.query.filter_by(employee_id='EMP-009').first() # Karan Malhotra

        requests_data = [
            # Rahul's leaves (Past approved)
            {
                'req_num': 'LR-2026-0001',
                'emp': demo_emp,
                'type': 'CL',
                'start': date(current_year, 2, 10),
                'end': date(current_year, 2, 11),
                'half': False,
                'days': 2.0,
                'reason': 'Attending family wedding in hometown Jaipur.',
                'status': 'Approved',
                'reviewer': mgr_emp2,
                'applied': datetime(current_year, 2, 1, 10, 30),
                'reviewed': datetime(current_year, 2, 2, 14, 15)
            },
            {
                'req_num': 'LR-2026-0002',
                'emp': demo_emp,
                'type': 'SL',
                'start': date(current_year, 4, 14),
                'end': date(current_year, 4, 15),
                'half': False,
                'days': 2.0,
                'reason': 'Viral fever and prescribed medical rest by physician.',
                'status': 'Approved',
                'reviewer': mgr_emp2,
                'applied': datetime(current_year, 4, 13, 8, 45),
                'reviewed': datetime(current_year, 4, 13, 11, 0)
            },
            # Rahul's Pending request (Current - ready to demonstrate manager approval in review!)
            {
                'req_num': 'LR-2026-0003',
                'emp': demo_emp,
                'type': 'AL',
                'start': date(current_year, 10, 12),
                'end': date(current_year, 10, 16),
                'half': False,
                'days': 5.0,
                'reason': 'Annual vacation with family to Himachal Pradesh.',
                'status': 'Pending',
                'reviewer': None,
                'applied': datetime(current_year, 9, 22, 16, 0),
                'reviewed': None
            },
            # Rahul's Cancelled request
            {
                'req_num': 'LR-2026-0004',
                'emp': demo_emp,
                'type': 'WFH',
                'start': date(current_year, 5, 20),
                'end': date(current_year, 5, 21),
                'half': False,
                'days': 2.0,
                'reason': 'Home broadband maintenance and electrical repair work.',
                'status': 'Cancelled',
                'reviewer': None,
                'applied': datetime(current_year, 5, 18, 9, 0),
                'reviewed': None,
                'cancelled': datetime(current_year, 5, 19, 11, 30),
                'cancel_reason': 'Technician rescheduled visit, no longer required.'
            },
            # Neha Gupta's leaves
            {
                'req_num': 'LR-2026-0005',
                'emp': neha_emp,
                'type': 'AL',
                'start': date(current_year, 6, 8),
                'end': date(current_year, 6, 12),
                'half': False,
                'days': 5.0,
                'reason': 'Personal leave for attending cousin’s convocation in Mumbai.',
                'status': 'Approved',
                'reviewer': mgr_emp2,
                'applied': datetime(current_year, 5, 28, 11, 20),
                'reviewed': datetime(current_year, 5, 29, 16, 45)
            },
            # Neha Gupta's Pending request
            {
                'req_num': 'LR-2026-0006',
                'emp': neha_emp,
                'type': 'CL',
                'start': date(current_year, 10, 5),
                'end': date(current_year, 10, 6),
                'half': False,
                'days': 2.0,
                'reason': 'Bank paperwork and apartment lease registration.',
                'status': 'Pending',
                'reviewer': None,
                'applied': datetime(current_year, 9, 23, 14, 10),
                'reviewed': None
            },
            # Amit Nair's leaves
            {
                'req_num': 'LR-2026-0007',
                'emp': amit_emp,
                'type': 'CL',
                'start': date(current_year, 3, 12),
                'end': date(current_year, 3, 13),
                'half': False,
                'days': 2.0,
                'reason': 'Visiting parents in Kerala.',
                'status': 'Approved',
                'reviewer': mgr_emp1,
                'applied': datetime(current_year, 3, 1, 10, 0),
                'reviewed': datetime(current_year, 3, 2, 12, 0)
            },
            {
                'req_num': 'LR-2026-0008',
                'emp': amit_emp,
                'type': 'AL',
                'start': date(current_year, 7, 15),
                'end': date(current_year, 7, 24),
                'half': False,
                'days': 8.0,
                'reason': 'Extended leave during critical quarterly financial audit closure.',
                'status': 'Rejected',
                'reviewer': mgr_emp1,
                'applied': datetime(current_year, 7, 1, 9, 30),
                'reviewed': datetime(current_year, 7, 2, 15, 0),
                'rejection_reason': 'Conflict with Q2 statutory tax filing and annual external audit deadline.'
            },
            # Karan Malhotra's leaves
            {
                'req_num': 'LR-2026-0009',
                'emp': karan_emp,
                'type': 'WFH',
                'start': date(current_year, 9, 21),
                'end': date(current_year, 9, 22),
                'half': False,
                'days': 2.0,
                'reason': 'Monitoring scheduled AWS database migration over weekend.',
                'status': 'Approved',
                'reviewer': mgr_emp2,
                'applied': datetime(current_year, 9, 18, 11, 0),
                'reviewed': datetime(current_year, 9, 19, 14, 0)
            },
            # Ananya Iyer's Pending request
            {
                'req_num': 'LR-2026-0010',
                'emp': ananya_emp,
                'type': 'CL',
                'start': date(current_year, 10, 8),
                'end': date(current_year, 10, 9),
                'half': False,
                'days': 2.0,
                'reason': 'Personal commitments and family function.',
                'status': 'Pending',
                'reviewer': None,
                'applied': datetime(current_year, 9, 24, 9, 15),
                'reviewed': None
            }
        ]

        for req in requests_data:
            lt = lt_objects[req['type']]
            l_req = LeaveRequest(
                request_number=req['req_num'],
                employee_id=req['emp'].id,
                leave_type_id=lt.id,
                start_date=req['start'],
                end_date=req['end'],
                is_half_day=req['half'],
                days_requested=req['days'],
                reason=req['reason'],
                status=req['status'],
                reviewed_by_id=req['reviewer'].id if req['reviewer'] else None,
                reviewed_at=req.get('reviewed'),
                rejection_reason=req.get('rejection_reason'),
                applied_at=req['applied'],
                cancelled_at=req.get('cancelled'),
                cancellation_reason=req.get('cancel_reason')
            )
            db.session.add(l_req)

            if req['status'] == 'Approved':
                apply_approved_deduction(req['emp'].id, lt.id, req['days'])

        db.session.flush()

        # 7. SEED ATTENDANCE RECORDS (Past 30 weekdays for all employees)
        print("Seeding realistic attendance history...")
        today = date.today()
        for emp in all_created_employees:
            for day_offset in range(30, 0, -1):
                att_date = today - timedelta(days=day_offset)
                if att_date.weekday() in (5, 6):
                    continue  # Skip weekends

                # Check if employee had approved leave on this date
                on_leave = LeaveRequest.query.filter(
                    LeaveRequest.employee_id == emp.id,
                    LeaveRequest.status == 'Approved',
                    LeaveRequest.start_date <= att_date,
                    LeaveRequest.end_date >= att_date
                ).first()

                if on_leave:
                    status = 'Leave'
                    check_in = None
                    check_out = None
                    notes = f'Approved Leave ({on_leave.leave_type.code})'
                elif (emp.id + day_offset) % 19 == 0:
                    status = 'Absent'
                    check_in = None
                    check_out = None
                    notes = 'Unplanned Absence'
                elif (emp.id + day_offset) % 23 == 0:
                    status = 'Half Day'
                    check_in = '09:30'
                    check_out = '13:45'
                    notes = 'Half day afternoon'
                else:
                    status = 'Present'
                    check_in = '09:15'
                    check_out = '18:10'
                    notes = 'Regular Attendance'

                att = Attendance(
                    employee_id=emp.id,
                    date=att_date,
                    status=status,
                    check_in=check_in,
                    check_out=check_out,
                    notes=notes
                )
                db.session.add(att)

        # 8. NOTIFICATIONS
        notifs_data = [
            {
                'user_id': demo_emp.user_id,
                'title': 'Welcome to ELMS',
                'msg': 'Welcome to the Employee Leave Management System. Check your leave balances and policies anytime.',
                'cat': 'info'
            },
            {
                'user_id': demo_emp.user_id,
                'title': 'Leave Request LR-2026-0001 Approved',
                'msg': 'Your Casual Leave application for 2 days has been approved by Vikram Singh.',
                'cat': 'success'
            },
            {
                'user_id': demo_emp.user_id,
                'title': 'Leave Request LR-2026-0003 Submitted',
                'msg': 'Your Annual Leave request for 5 days is currently pending review by your manager.',
                'cat': 'info'
            },
            {
                'user_id': mgr_user1.id,
                'title': 'Pending Leave Requests Awaiting Review',
                'msg': 'There are 3 pending leave applications requiring HR/Managerial decision.',
                'cat': 'warning'
            },
            {
                'user_id': admin_user.id,
                'title': 'System Setup Completed',
                'msg': 'Initial organization setup, departments, and leave policies have been loaded successfully.',
                'cat': 'success'
            }
        ]
        for n in notifs_data:
            notif = Notification(user_id=n['user_id'], title=n['title'], message=n['msg'], category=n['cat'], is_read=False, created_at=datetime.utcnow() - timedelta(hours=2))
            db.session.add(notif)

        # 9. AUDIT LOGS
        audit_records = [
            {'user': 'admin@example.com', 'action': 'System Initialized', 'type': 'System', 'id': '1', 'details': 'Created departments, leave policies, and admin account.'},
            {'user': 'admin@example.com', 'action': 'Employee Created', 'type': 'Employee', 'id': 'EMP-004', 'details': 'Provisioned Rahul Verma with standard leave balances.'},
            {'user': 'employee@example.com', 'action': 'User Login', 'type': 'User', 'id': str(demo_emp.user_id), 'details': 'Logged in via web portal.'},
            {'user': 'employee@example.com', 'action': 'Leave Applied', 'type': 'LeaveRequest', 'id': 'LR-2026-0001', 'details': 'Applied for 2 days Casual Leave.'},
            {'user': 'vikram.singh@example.com', 'action': 'Leave Approved', 'type': 'LeaveRequest', 'id': 'LR-2026-0001', 'details': 'Approved Casual Leave for Rahul Verma.'},
            {'user': 'manager@example.com', 'action': 'Leave Rejected', 'type': 'LeaveRequest', 'id': 'LR-2026-0008', 'details': 'Rejected Annual Leave for Amit Nair due to Q2 audit.'},
            {'user': 'employee@example.com', 'action': 'Leave Cancelled', 'type': 'LeaveRequest', 'id': 'LR-2026-0004', 'details': 'Cancelled WFH request.'},
            {'user': 'employee@example.com', 'action': 'Leave Applied', 'type': 'LeaveRequest', 'id': 'LR-2026-0003', 'details': 'Applied for 5 days Annual Leave.'}
        ]
        for a in audit_records:
            log = AuditLog(
                user_email=a['user'],
                action=a['action'],
                record_type=a['type'],
                record_id=a['id'],
                details=a['details'],
                ip_address='127.0.0.1',
                timestamp=datetime.utcnow() - timedelta(hours=5)
            )
            db.session.add(log)

        db.session.commit()
        print("Database seeded successfully with 1 Admin, 2 Managers, 9 Employees, Departments, Leave Balances, Requests, Attendance, and Audit Logs!")

if __name__ == '__main__':
    seed_database()
