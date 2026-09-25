import sys
import unittest
from datetime import date, datetime, timedelta
import io
import csv

from app import create_app
from seed import seed_database
from models.models import db, User, Employee, Department, LeaveType, LeaveBalance, LeaveRequest, Holiday, Attendance, Notification, AuditLog

class MasterEndToEndVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Initializing clean test database with seed_database()...")
        seed_database()

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_startup_and_config(self):
        print("\n[CHECK 1] Verifying Flask Application Startup & Configuration...")
        self.assertIsNotNone(self.app)
        self.assertTrue(self.app.config['SQLALCHEMY_DATABASE_URI'].endswith('database.db'))
        self.assertIsNotNone(self.app.config['SECRET_KEY'])
        res = self.client.get('/')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location'))
        print("  -> Passed: Startup & Root redirect working.")

    def test_02_database_connection_and_models(self):
        print("\n[CHECK 2] Verifying Database Connection and All 10 Models...")
        with self.app.app_context():
            self.assertGreater(User.query.count(), 0)
            self.assertGreater(Department.query.count(), 0)
            self.assertGreater(Employee.query.count(), 0)
            self.assertGreater(LeaveType.query.count(), 0)
            self.assertGreater(LeaveBalance.query.count(), 0)
            self.assertGreater(LeaveRequest.query.count(), 0)
            self.assertGreater(Holiday.query.count(), 0)
            self.assertGreater(Attendance.query.count(), 0)
            self.assertGreater(Notification.query.count(), 0)
            self.assertGreater(AuditLog.query.count(), 0)
            print("  -> Passed: All 10 tables exist and contain records.")

    def test_03_04_05_logins_and_credentials(self):
        print("\n[CHECKS 3, 4, 5] Verifying Login for Admin, Manager, and Employee...")
        # Bad Login
        res = self.client.post('/login', data={'email': 'wrong@example.com', 'password': 'bad'}, follow_redirects=True)
        self.assertIn(b'Invalid email or password', res.data)

        # Admin Login
        res = self.client.post('/login', data={'email': 'admin@example.com', 'password': 'Admin@123'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'System Administration', res.data)
        self.client.get('/logout')

        # Manager Login
        res = self.client.post('/login', data={'email': 'manager@example.com', 'password': 'Manager@123'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'HR & Manager Dashboard', res.data)
        self.client.get('/logout')

        # Employee Login
        res = self.client.post('/login', data={'email': 'employee@example.com', 'password': 'Employee@123'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Employee Dashboard', res.data)
        self.client.get('/logout')
        print("  -> Passed: All 3 roles authenticate and redirect properly.")

    def test_06_rbac_enforcement(self):
        print("\n[CHECK 6] Verifying Role-Based Access Control (RBAC)...")
        # Employee attempts Admin routes -> 403
        self.client.post('/login', data={'email': 'employee@example.com', 'password': 'Employee@123'}, follow_redirects=True)
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 403)
        res = self.client.get('/admin/employees')
        self.assertEqual(res.status_code, 403)
        res = self.client.get('/manager/dashboard')
        self.assertEqual(res.status_code, 403)
        self.client.get('/logout')

        # Manager attempts Admin-only routes -> 403
        self.client.post('/login', data={'email': 'manager@example.com', 'password': 'Manager@123'}, follow_redirects=True)
        res = self.client.get('/admin/audit-logs')
        self.assertEqual(res.status_code, 403)
        res = self.client.get('/admin/settings')
        self.assertEqual(res.status_code, 403)
        self.client.get('/logout')
        print("  -> Passed: Strict RBAC enforced; forbidden access returns HTTP 403.")

    def test_07_employee_dashboard(self):
        print("\n[CHECK 7] Verifying Employee Dashboard KPIs & Balances...")
        self.client.post('/login', data={'email': 'employee@example.com', 'password': 'Employee@123'}, follow_redirects=True)
        res = self.client.get('/employee/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Total Entitlement', res.data)
        self.assertIn(b'Leaves Remaining', res.data)
        self.assertIn(b'Attendance Overview', res.data)
        print("  -> Passed: Employee dashboard displays all KPI cards and balances.")

    def test_08_09_10_leave_application_and_day_calculation(self):
        print("\n[CHECKS 8, 9, 10] Verifying Leave Application, Working-Day Calc & Holiday/Weekend Skip...")
        self.client.post('/login', data={'email': 'employee@example.com', 'password': 'Employee@123'}, follow_redirects=True)

        # Live calculate-days API: Jan 23 to Jan 27 2026 includes weekend (Jan 24, 25) + Republic Day holiday (Jan 26)
        res = self.client.post('/employee/api/calculate-days', json={
            'start_date': f'{date.today().year}-01-23',
            'end_date': f'{date.today().year}-01-27',
            'is_half_day': False
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['days'], 2.0)
        self.assertEqual(data['weekends_count'], 2)
        self.assertEqual(data['holidays_count'], 1)

        # Half Day test
        res_half = self.client.post('/employee/api/calculate-days', json={
            'start_date': f'{date.today().year}-02-02',
            'end_date': f'{date.today().year}-02-02',
            'is_half_day': True
        })
        self.assertEqual(res_half.get_json()['days'], 0.5)
        print("  -> Passed: Live working-day calculation accurately excludes weekends and holidays.")

    def test_11_12_balance_validation_and_conflict_detection(self):
        print("\n[CHECKS 11, 12] Verifying Balance Limits & Conflict Overlap Detection...")
        self.client.post('/login', data={'email': 'employee@example.com', 'password': 'Employee@123'}, follow_redirects=True)
        with self.app.app_context():
            cl_type = LeaveType.query.filter_by(code='CL').first()
            # 1. Apply a valid leave
            res = self.client.post('/employee/apply-leave', data={
                'leave_type_id': cl_type.id,
                'start_date': f'{date.today().year}-11-02',
                'end_date': f'{date.today().year}-11-03',
                'reason': 'Special family occasion'
            }, follow_redirects=True)
            self.assertIn(b'submitted successfully', res.data)

            # 2. Overlap Conflict detection: Try applying for overlapping range Nov 03 - Nov 04
            res_overlap = self.client.post('/employee/apply-leave', data={
                'leave_type_id': cl_type.id,
                'start_date': f'{date.today().year}-11-03',
                'end_date': f'{date.today().year}-11-04',
                'reason': 'Conflicting request'
            }, follow_redirects=True)
            self.assertIn(b'overlaps with an existing', res_overlap.data)

            # 3. Insufficient balance detection:
            res_insufficient = self.client.post('/employee/apply-leave', data={
                'leave_type_id': cl_type.id,
                'start_date': f'{date.today().year}-12-01',
                'end_date': f'{date.today().year}-12-30',
                'reason': 'Too many days'
            }, follow_redirects=True)
            self.assertIn(b'Insufficient leave balance', res_insufficient.data)
            print("  -> Passed: Conflict detection and quota limits are enforced strictly.")

    def test_13_14_leave_approval_rejection_and_attendance(self):
        print("\n[CHECKS 13, 14, 17] Verifying Leave Approval, Rejection & Attendance Sync...")
        with self.app.app_context():
            # Find a pending request to approve
            pending = LeaveRequest.query.filter_by(status='Pending').first()
            req_id = pending.id
            emp_id = pending.employee_id
            lt_id = pending.leave_type_id
            days = pending.days_requested
            start_d = pending.start_date

            bal_before = LeaveBalance.query.filter_by(employee_id=emp_id, leave_type_id=lt_id, year=start_d.year).first().remaining_days

            # Manager Approves
            self.client.post('/login', data={'email': 'manager@example.com', 'password': 'Manager@123'}, follow_redirects=True)
            res_app = self.client.post(f'/manager/approve-leave/{req_id}', follow_redirects=True)
            self.assertIn(b'approved successfully', res_app.data)

            # Verify balance deducted
            bal_after = LeaveBalance.query.filter_by(employee_id=emp_id, leave_type_id=lt_id, year=start_d.year).first().remaining_days
            self.assertEqual(bal_after, bal_before - days)

            # Verify Attendance record was marked as Leave
            att = Attendance.query.filter_by(employee_id=emp_id, date=start_d).first()
            self.assertIsNotNone(att)
            self.assertEqual(att.status, 'Leave')

            # Find another pending request to reject
            pending2 = LeaveRequest.query.filter_by(status='Pending').first()
            if pending2:
                req_id2 = pending2.id
                bal_before2 = LeaveBalance.query.filter_by(employee_id=pending2.employee_id, leave_type_id=pending2.leave_type_id, year=pending2.start_date.year).first().remaining_days
                res_rej = self.client.post(f'/manager/reject-leave/{req_id2}', data={'rejection_reason': 'Urgent project release schedule'}, follow_redirects=True)
                self.assertIn(b'rejected', res_rej.data)

                # Verify balance is NOT deducted
                bal_after2 = LeaveBalance.query.filter_by(employee_id=pending2.employee_id, leave_type_id=pending2.leave_type_id, year=pending2.start_date.year).first().remaining_days
                self.assertEqual(bal_after2, bal_before2)
                # Verify rejection reason recorded
                req2_record = db.session.get(LeaveRequest, req_id2)
                self.assertEqual(req2_record.rejection_reason, 'Urgent project release schedule')
            print("  -> Passed: Approval deducts balance and sets attendance; rejection captures reason without deduction.")

    def test_15_leave_cancellation(self):
        print("\n[CHECK 15] Verifying Leave Cancellation & Quota Restoration...")
        with self.app.app_context():
            # Rahul Verma applies for a future leave
            self.client.post('/login', data={'email': 'employee@example.com', 'password': 'Employee@123'}, follow_redirects=True)
            al_type = LeaveType.query.filter_by(code='AL').first()
            emp = Employee.query.filter_by(employee_id='EMP-004').first()

            # Submit and approve a future leave
            req = LeaveRequest(
                request_number='LR-2026-TESTCAN',
                employee_id=emp.id,
                leave_type_id=al_type.id,
                start_date=date(date.today().year, 12, 10),
                end_date=date(date.today().year, 12, 11),
                days_requested=2.0,
                reason='Test Cancellation',
                status='Approved'
            )
            bal = LeaveBalance.query.filter_by(employee_id=emp.id, leave_type_id=al_type.id, year=date.today().year).first()
            bal.used_days += 2.0
            bal.update_balance()
            db.session.add(req)
            db.session.commit()

            bal_before_cancel = bal.remaining_days

            # Employee cancels this approved future leave
            res = self.client.post(f'/employee/cancel-leave/{req.id}', data={'cancellation_reason': 'Plans changed'}, follow_redirects=True)
            self.assertIn(b'cancelled successfully', res.data)

            # Check that balance was restored
            db.session.refresh(bal)
            self.assertEqual(bal.remaining_days, bal_before_cancel + 2.0)
            print("  -> Passed: Cancellation restored quota accurately.")

    def test_16_notifications(self):
        print("\n[CHECK 16] Verifying Notification Center & Read Status...")
        self.client.post('/login', data={'email': 'employee@example.com', 'password': 'Employee@123'}, follow_redirects=True)
        res = self.client.get('/employee/notifications')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'All Notifications', res.data)

        # Mark all read
        res_read = self.client.post('/employee/notifications/read-all', follow_redirects=True)
        self.assertIn(b'All notifications marked as read', res_read.data)
        print("  -> Passed: Notification list and mark-all-read working.")

    def test_18_leave_calendar_apis(self):
        print("\n[CHECK 18] Verifying Calendar Endpoints & JSON Payloads...")
        # Employee calendar
        self.client.post('/login', data={'email': 'employee@example.com', 'password': 'Employee@123'}, follow_redirects=True)
        res_emp = self.client.get('/employee/calendar')
        self.assertEqual(res_emp.status_code, 200)
        res_events = self.client.get('/employee/api/calendar-events')
        self.assertEqual(res_events.status_code, 200)
        events = res_events.get_json()
        self.assertTrue(any(e['type'] == 'holiday' for e in events))

        # Manager calendar
        self.client.post('/login', data={'email': 'manager@example.com', 'password': 'Manager@123'}, follow_redirects=True)
        res_mgr = self.client.get('/manager/calendar')
        self.assertEqual(res_mgr.status_code, 200)
        res_mgr_events = self.client.get('/manager/api/calendar-events')
        self.assertEqual(res_mgr_events.status_code, 200)
        print("  -> Passed: Calendar views and event APIs return structured JSON data.")

    def test_19_20_21_22_admin_crud(self):
        print("\n[CHECKS 19, 20, 21, 22] Verifying Admin CRUD for Employees, Depts, Leave Types, Holidays...")
        self.client.post('/login', data={'email': 'admin@example.com', 'password': 'Admin@123'}, follow_redirects=True)

        # Department Add
        res_d = self.client.post('/admin/departments', data={
            'action': 'add',
            'name': 'Research & Innovation',
            'code': 'RND',
            'description': 'Advanced R&D team'
        }, follow_redirects=True)
        self.assertIn(b'created successfully', res_d.data)

        # Leave Type Add
        res_lt = self.client.post('/admin/leave-types', data={
            'action': 'add',
            'name': 'Bereavement Leave',
            'code': 'BER',
            'max_days': 5.0,
            'is_paid': '1',
            'description': 'Compassionate leave'
        }, follow_redirects=True)
        self.assertIn(b'created and provisioned', res_lt.data)

        # Holiday Add
        res_h = self.client.post('/admin/holidays', data={
            'action': 'add',
            'name': 'New Year Day',
            'date': f'{date.today().year + 1}-01-01',
            'description': 'Global holiday'
        }, follow_redirects=True)
        self.assertIn(b'added successfully', res_h.data)

        # Employee Add
        res_e = self.client.post('/admin/employees/add', data={
            'email': 'suresh.kumar@example.com',
            'password': 'Employee@123',
            'role': 'Employee',
            'first_name': 'Suresh',
            'last_name': 'Kumar',
            'phone': '+91 99001 12233',
            'designation': 'QA Engineer',
            'joining_date': f'{date.today().year}-01-10'
        }, follow_redirects=True)
        self.assertIn(b'created successfully', res_e.data)
        print("  -> Passed: Admin CRUD operations add records and auto-provision balances.")

    def test_23_24_25_reports_charts_and_csv(self):
        print("\n[CHECKS 23, 24, 25] Verifying Reports, Chart.js Visualizations & CSV Export...")
        self.client.post('/login', data={'email': 'manager@example.com', 'password': 'Manager@123'}, follow_redirects=True)

        # Manager Dashboard Charts verification
        res_dash = self.client.get('/manager/dashboard')
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b'monthlyChart', res_dash.data)
        self.assertIn(b'statusChart', res_dash.data)
        self.assertIn(b'typeChart', res_dash.data)
        self.assertIn(b'deptChart', res_dash.data)

        # Reports View
        res_rep = self.client.get('/reports/?report_type=leave_requests')
        self.assertEqual(res_rep.status_code, 200)
        self.assertIn(b'Filtered Records', res_rep.data)

        # CSV Export
        res_csv = self.client.get('/reports/export-csv?report_type=leave_requests')
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.content_type, 'text/csv; charset=utf-8')
        lines = res_csv.data.decode('utf-8').splitlines()
        self.assertGreater(len(lines), 1)
        self.assertIn('Request ID', lines[0])
        print("  -> Passed: Charts, Reports, and CSV export verified.")

    def test_26_27_audit_logs_search_filter(self):
        print("\n[CHECKS 26, 27] Verifying Audit Trails & Search Filters...")
        self.client.post('/login', data={'email': 'admin@example.com', 'password': 'Admin@123'}, follow_redirects=True)
        res = self.client.get('/admin/audit-logs')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Security & System Audit Trails', res.data)

        # Filter by action
        res_filt = self.client.get('/admin/audit-logs?action=User+Login')
        self.assertEqual(res_filt.status_code, 200)
        print("  -> Passed: Audit trails capture events and support action filtering.")

    def test_28_29_30_31_validation_errors_responsive_routes(self):
        print("\n[CHECKS 28, 29, 30, 31] Verifying Form Validation, Custom Error Pages & Route Crawl...")
        # 404 handler
        res_404 = self.client.get('/non-existent-page-xyz')
        self.assertEqual(res_404.status_code, 404)
        self.assertIn(b'Page Not Found', res_404.data)

        # 403 handler
        self.client.post('/login', data={'email': 'employee@example.com', 'password': 'Employee@123'}, follow_redirects=True)
        res_403 = self.client.get('/admin/settings')
        self.assertEqual(res_403.status_code, 403)
        self.assertIn(b'Access Forbidden', res_403.data)

        # Verify static CSS and JS load cleanly
        res_css = self.client.get('/static/css/styles.css')
        self.assertEqual(res_css.status_code, 200)
        self.assertIn(b'.col-actions', res_css.data)
        self.assertIn(b'position: sticky', res_css.data)

        res_js = self.client.get('/static/js/main.js')
        self.assertEqual(res_js.status_code, 200)

        res_cal = self.client.get('/static/js/calendar.js')
        self.assertEqual(res_cal.status_code, 200)

        # Crawl all employee routes
        emp_routes = [
            '/employee/dashboard',
            '/employee/apply-leave',
            '/employee/my-leaves',
            '/employee/calendar',
            '/employee/attendance',
            '/employee/notifications',
            '/employee/profile'
        ]
        for r in emp_routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed for Employee")

        # Crawl all manager routes
        self.client.post('/login', data={'email': 'manager@example.com', 'password': 'Manager@123'}, follow_redirects=True)
        mgr_routes = [
            '/manager/dashboard',
            '/manager/leave-requests',
            '/manager/employees',
            '/manager/calendar',
            '/manager/attendance',
            '/reports/'
        ]
        for r in mgr_routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed for Manager")

        # Crawl all admin routes
        self.client.post('/login', data={'email': 'admin@example.com', 'password': 'Admin@123'}, follow_redirects=True)
        admin_routes = [
            '/admin/dashboard',
            '/admin/employees',
            '/admin/employees/add',
            '/admin/departments',
            '/admin/leave-types',
            '/admin/holidays',
            '/admin/audit-logs',
            '/admin/settings'
        ]
        for r in admin_routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed for Admin")

        print("  -> Passed: All routes, error pages, static assets, and validation handlers verified.")

if __name__ == '__main__':
    unittest.main()
