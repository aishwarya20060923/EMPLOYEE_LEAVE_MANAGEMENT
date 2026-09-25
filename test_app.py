import unittest
from datetime import date, datetime, timedelta
from app import create_app
from seed import seed_database
from models.models import db, User, Employee, Department, LeaveType, LeaveBalance, LeaveRequest, Holiday, Attendance, Notification, AuditLog

class ELMSTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database()

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    # --- 1. AUTH & RBAC TESTS ---
    def test_01_login_logout(self):
        print("\n[TEST 1] Testing Auth & RBAC...")
        # Invalid login
        res = self.client.post('/login', data={'email': 'wrong@example.com', 'password': 'WrongPassword'}, follow_redirects=True)
        self.assertIn(b'Invalid email or password', res.data)

        # Valid Employee Login
        res = self.client.post('/login', data={'email': 'employee@example.com', 'password': 'Employee@123'}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Employee Dashboard', res.data)

        # RBAC Check: Employee attempting to access Admin route should get 403
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 403)
        self.assertIn(b'Access Forbidden', res.data)

        # Logout
        res = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'logged out', res.data)

    def test_02_manager_access(self):
        print("[TEST 2] Testing Manager Dashboard & RBAC...")
        self.client.post('/login', data={'email': 'manager@example.com', 'password': 'Manager@123'}, follow_redirects=True)
        res = self.client.get('/manager/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'HR & Manager Dashboard', res.data)

        # RBAC Check: Manager attempting to access Admin audit logs should get 403
        res = self.client.get('/admin/audit-logs')
        self.assertEqual(res.status_code, 403)

    def test_03_admin_access(self):
        print("[TEST 3] Testing Admin Dashboard & Actions...")
        self.client.post('/login', data={'email': 'admin@example.com', 'password': 'Admin@123'}, follow_redirects=True)
        res = self.client.get('/admin/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'System Administration', res.data)

    # --- 2. LEAVE CALCULATION & CONFLICT DETECTION ---
    def test_04_leave_days_calculation(self):
        print("[TEST 4] Testing Smart Working Days Calculation (Weekend & Holiday exclusion)...")
        # Log in first
        self.client.post('/login', data={'email': 'employee@example.com', 'password': 'Employee@123'}, follow_redirects=True)
        
        with self.app.app_context():
            # Seeded holiday Republic Day is Jan 26, 2026 (Monday)
            # Jan 23, 2026 (Friday) to Jan 27, 2026 (Tuesday) has 5 calendar days:
            # Friday (work), Saturday (weekend), Sunday (weekend), Monday (holiday), Tuesday (work)
            # Working days should be exactly 2.0!
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
            print(f"  Working days calculated: {data['days']} days (Weekends skipped: {data['weekends_count']}, Holidays skipped: {data['holidays_count']})")

    # --- 3. LEAVE APPLICATION & VALIDATIONS ---
    def test_05_apply_leave_flow(self):
        print("[TEST 5] Testing Leave Application, Balance Check & Conflict Detection...")
        with self.app.app_context():
            # Login as employee
            self.client.post('/login', data={'email': 'employee@example.com', 'password': 'Employee@123'}, follow_redirects=True)
            emp = Employee.query.filter_by(employee_id='EMP-004').first()
            cl_type = LeaveType.query.filter_by(code='CL').first()

            # 1. Apply a valid leave in November
            start_d = f'{date.today().year}-11-16' # Monday
            end_d = f'{date.today().year}-11-17'   # Tuesday
            res = self.client.post('/employee/apply-leave', data={
                'leave_type_id': cl_type.id,
                'start_date': start_d,
                'end_date': end_d,
                'reason': 'Personal family celebration in home town'
            }, follow_redirects=True)
            self.assertIn(b'submitted successfully', res.data)

            # 2. Overlap Conflict Check: Try applying for overlapping dates (Nov 17 - Nov 18)
            res_conflict = self.client.post('/employee/apply-leave', data={
                'leave_type_id': cl_type.id,
                'start_date': f'{date.today().year}-11-17',
                'end_date': f'{date.today().year}-11-18',
                'reason': 'Trying to create conflicting leave'
            }, follow_redirects=True)
            self.assertIn(b'overlaps with an existing', res_conflict.data)
            print("  Verified: Overlapping request blocked by conflict detection!")

            # 3. Insufficient balance test: Try applying for 30 days of Casual Leave (balance is ~10)
            res_insufficient = self.client.post('/employee/apply-leave', data={
                'leave_type_id': cl_type.id,
                'start_date': f'{date.today().year}-12-01',
                'end_date': f'{date.today().year}-12-30',
                'reason': 'Excessive leave request'
            }, follow_redirects=True)
            self.assertIn(b'Insufficient leave balance', res_insufficient.data)
            print("  Verified: Insufficient balance request blocked!")

    # --- 4. MANAGER APPROVAL & ATTENDANCE INTEGRATION ---
    def test_06_manager_approve_and_attendance(self):
        print("[TEST 6] Testing Manager Approval, Quota Deduction, Attendance Integration & Notification...")
        with self.app.app_context():
            # Find a pending request
            pending_req = LeaveRequest.query.filter_by(status='Pending').first()
            req_id = pending_req.id
            emp_id = pending_req.employee_id
            lt_id = pending_req.leave_type_id
            days = pending_req.days_requested

            bal_before = LeaveBalance.query.filter_by(employee_id=emp_id, leave_type_id=lt_id, year=pending_req.start_date.year).first().remaining_days

            # Manager logs in and approves
            self.client.post('/login', data={'email': 'manager@example.com', 'password': 'Manager@123'}, follow_redirects=True)
            res = self.client.post(f'/manager/approve-leave/{req_id}', follow_redirects=True)
            self.assertIn(b'approved successfully', res.data)

            # Verify balance updated
            bal_after = LeaveBalance.query.filter_by(employee_id=emp_id, leave_type_id=lt_id, year=pending_req.start_date.year).first().remaining_days
            self.assertEqual(bal_after, bal_before - days)
            print(f"  Verified: Quota deducted correctly from {bal_before} to {bal_after}!")

            # Verify Attendance record was automatically populated for leave date
            att = Attendance.query.filter_by(employee_id=emp_id, date=pending_req.start_date).first()
            self.assertIsNotNone(att)
            self.assertEqual(att.status, 'Leave')
            print(f"  Verified: Attendance integrated on {pending_req.start_date} as 'Leave'!")

            # Verify notification created for employee
            notif = Notification.query.filter_by(user_id=pending_req.employee.user_id).order_by(Notification.id.desc()).first()
            self.assertIn('Approved', notif.title)
            print(f"  Verified: Employee notified: '{notif.title}'!")

    # --- 5. REPORTS & CSV EXPORT ---
    def test_07_reports_and_csv_export(self):
        print("[TEST 7] Testing Reports View & CSV Export...")
        self.client.post('/login', data={'email': 'manager@example.com', 'password': 'Manager@123'}, follow_redirects=True)
        res = self.client.get('/reports/?report_type=leave_requests')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Leave Requests Report', res.data)

        # CSV Download endpoint
        res_csv = self.client.get('/reports/export-csv?report_type=leave_requests')
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.content_type, 'text/csv; charset=utf-8')
        self.assertIn(b'Request ID,Employee ID,Employee Name', res_csv.data)
        print("  Verified: CSV file generated with correct MIME type and headers!")

if __name__ == '__main__':
    unittest.main()
