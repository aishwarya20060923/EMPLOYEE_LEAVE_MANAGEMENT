# Employee Leave Management System (ELMS)

A modern, full-stack, enterprise-grade **Employee Leave Management System (ELMS)** designed for corporate organizations and developed for academic project demonstration and CRT evaluation.

ELMS provides end-to-end management of organizational leaves with dynamic policy administration, multi-level role-based authorization (Admin, Manager/HR, Employee), smart working-day calculations (auto-excluding weekends and national holidays), conflict detection, audit logging, interactive leave calendars, attendance tracking, and comprehensive analytical reporting with CSV and print support.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Engine** | Python 3.11, Flask Framework |
| **Database & ORM** | SQLite 3, SQLAlchemy ORM |
| **Authentication & Security** | Werkzeug SHA-256 Hashing, Session Management, RBAC |
| **Frontend Templates** | HTML5, Jinja2 Template Engine |
| **Styling & Design System** | Modern Custom CSS3 (Corporate SaaS Design System) |
| **Client Scripting** | Vanilla ES6 JavaScript (No frameworks) |
| **Data Visualizations** | Chart.js 4.4 |

---

## 👥 User Roles & Access Control

1. **System Administrator (Admin)**
   - Manages organizational structure: Departments, Leave Policies, and Public Holidays.
   - Comprehensive Employee Directory Management (Add, Edit, Deactivate, Auto-provision Quotas).
   - Global review of all organization-wide leave applications.
   - Access to full security audit logs and system configuration diagnostics.
   - Organizational reporting and CSV export.

2. **HR / Team Manager**
   - Department and team leave dashboard with 4 real-time Chart.js visual analytics.
   - Pending Leave Requests Approval Queue with instant Approve/Reject (reason capture).
   - Organization-wide Leave & Holiday Calendar with department filtering.
   - Team attendance management and integration.
   - Detailed employee profile inspector with leave balances and history.

3. **Employee (Self-Service)**
   - Personal leave dashboard with KPI cards and progress bars for each leave type.
   - Interactive leave application with **smart live calculation**:
     - Auto-skips Saturdays and Sundays.
     - Auto-skips configured mandatory holidays.
     - Detects date overlaps with existing pending or approved requests.
     - Enforces available balance limits and blocks negative balances.
     - Supports Half-Day applications (0.5 days).
     - Allows optional file attachments (medical notes, tickets, documents).
   - Leave history tracking with search, status filtering, and cancellation (with balance restoration for future approved leaves).
   - Personal leave and holiday calendar.
   - Daily attendance clock-in/clock-out tracking.
   - Notification center with unread badges.
   - Profile management with contact editing and password change.

---

## 📋 Pre-configured Demo Accounts

| Role | Email Address | Password | Name & Designation |
|---|---|---|---|
| **Admin** | `admin@example.com` | `Admin@123` | Rajesh Sharma (IT Head & Admin) |
| **HR / Manager** | `manager@example.com` | `Manager@123` | Priya Patel (Senior HR Manager) |
| **Tech Manager** | `vikram.singh@example.com` | `Manager@123` | Vikram Singh (Engineering Manager) |
| **Employee** | `employee@example.com` | `Employee@123` | Rahul Verma (Senior Developer) |
| **Employee** | `neha.gupta@example.com` | `Employee@123` | Neha Gupta (Product Designer) |
| **Employee** | `amit.nair@example.com` | `Employee@123` | Amit Nair (Financial Analyst) |

> 💡 **Reviewer Tip:** The login page features **1-Click Quick Login** buttons that allow you to seamlessly log in and switch between roles during presentations.

---

## ⚙️ System Requirements & Installation

### Requirements
- **Python:** Version 3.9 or higher (tested on Python 3.11)
- **Web Browser:** Any modern web browser (Chrome, Edge, Firefox, Safari)

### Installation Steps

1. **Clone or Navigate to the Project Directory:**
   ```bash
   cd employee_leave_management
   ```

2. **(Optional) Create and Activate a Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize and Seed the Database:**
   ```bash
   python seed.py
   ```
   *This creates SQLite tables, departments, leave types, 2026 holidays, 12 staff accounts, leave balances, past and pending leave requests, attendance logs, and audit trails.*

5. **Start the Flask Application:**
   ```bash
   python app.py
   ```

6. **Access the Portal:**
   Open your browser and navigate to:
   [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 📁 Project Directory Structure

```text
employee_leave_management/
│
├── app.py                     # Application factory, blueprints, context processors, error handlers
├── config.py                  # Database URI, upload configuration, session keys
├── requirements.txt           # Python package requirements
├── README.md                  # Comprehensive documentation and viva presentation guide
├── seed.py                    # Database schema creator and demo data generator
│
├── models/
│   ├── __init__.py            # Model exports
│   └── models.py              # User, Employee, Department, LeaveType, LeaveBalance,
│                              # LeaveRequest, Holiday, Attendance, Notification, AuditLog
│
├── routes/
│   ├── __init__.py            # Blueprint registration
│   ├── auth.py                # Login, logout, quick demo logins, session handlers
│   ├── employee.py            # Employee dashboard, apply leave, history, cancel, profile
│   ├── manager.py             # Manager dashboard, pending queue, approve/reject, analytics
│   ├── admin.py               # Employee CRUD, departments, leave types, holidays, audit logs
│   └── reports.py             # Analytical reports, filtering, CSV export, print styling
│
├── utils/
│   ├── __init__.py            # Helper exports
│   └── helpers.py             # RBAC decorators, smart working-day calculator,
│                              # conflict detector, request code generator, audit logger
│
├── templates/
│   ├── base.html              # Role-based sidebar, navbar, flash alerts, responsive drawer
│   ├── auth/
│   │   └── login.html         # Professional sign-in with quick 1-click test fill
│   ├── employee/
│   │   ├── dashboard.html     # Employee KPIs, balance cards, upcoming leaves, attendance
│   │   ├── apply_leave.html   # Smart leave form with live days calculator & balance warnings
│   │   ├── my_leaves.html     # Leave requests table, search, filters, cancel modal
│   │   ├── calendar.html      # Personal monthly schedule & holiday calendar
│   │   ├── attendance.html    # Clock in/out widget & 60-day attendance history
│   │   ├── notifications.html # Internal notification center
│   │   └── profile.html       # Profile inspector, contact editor, password changer
│   ├── manager/
│   │   ├── dashboard.html     # Charts (Monthly, Status, Type, Dept), pending review queue
│   │   ├── leave_requests.html# Detailed requests queue, approval & rejection modal
│   │   ├── employees.html     # Team directory & search
│   │   ├── employee_detail.html# Employee 360-degree view (balances, leaves, attendance)
│   │   ├── calendar.html      # Organization-wide leave calendar
│   │   └── attendance.html    # Daily organization attendance sheet
│   ├── admin/
│   │   ├── dashboard.html     # System statistics, quick action shortcuts, recent audit logs
│   │   ├── employees.html     # Staff management directory & status toggle
│   │   ├── employee_form.html # Add/Edit employee with automatic quota provisioning
│   │   ├── departments.html   # Add/Edit departments & activation toggle
│   │   ├── leave_types.html   # Policy manager (Max entitlement, paid/unpaid, carry-forward)
│   │   ├── holidays.html      # Holiday schedule manager (Mandatory vs Optional)
│   │   ├── audit_logs.html    # Security audit trails with action filter & search
│   │   └── settings.html      # System architecture & parameters
│   ├── reports/
│   │   └── index.html         # Multi-criteria reports, summary cards, CSV export & print view
│   └── errors/
│       ├── 403.html           # Access Forbidden (Role-based restriction)
│       ├── 404.html           # Page Not Found
│       └── 500.html           # Internal Server Error
│
├── static/
│   ├── css/
│   │   └── styles.css         # Custom modern corporate CSS design system
│   ├── js/
│   │   ├── main.js            # Live days calculator, modals, alerts, demo filler
│   │   └── calendar.js        # Vanilla JS monthly interactive calendar
│   └── uploads/               # User attachments (medical certificates, documents)
│
└── instance/
    └── database.db            # SQLite relational database
```

---

## 🎯 Suggested Viva / CRT Presentation Demo Flow

Follow this structured 5-step sequence during your project evaluation:

1. **Step 1: Introduction & Login Demonstration**
   - Navigate to the login page (`/login`). Point out the clean UI and security features (passwords hashed with PBKDF2/SHA-256).
   - Click the **Quick Login: Employee** demo button to sign in as Rahul Verma (`employee@example.com`).

2. **Step 2: Employee Dashboard & Smart Leave Application**
   - Point out the 4 KPI cards: Total Entitlement, Leaves Used, Leaves Remaining, Pending Requests.
   - Show the **Leave Balance Breakdown** cards with color-coded progress bars for Casual, Sick, Annual, WFH, and Optional leaves.
   - Go to **Apply Leave** (`/employee/apply-leave`):
     - Pick **Annual Leave**.
     - Pick a date range that includes a weekend (e.g. Friday to Monday).
     - Notice the **Live Working Days Calculation**: it immediately calculates working days and shows note `(2 weekend day(s) excluded)`.
     - Try picking an overlapping date or a duration exceeding the remaining quota to showcase the backend validation safeguards.
     - Submit a valid application and verify the flash message and notification.

3. **Step 3: Leave History & Cancellation**
   - Navigate to **My Leaves** (`/employee/my-leaves`).
   - Demonstrate the filters (Status, Leave Type, Search).
   - Demonstrate cancelling an eligible request with the cancellation modal. Highlight that if an approved future leave is cancelled, the balance is restored automatically without negative balances.

4. **Step 4: HR / Manager Review & Analytical Dashboard**
   - Log out and log in as Manager (`manager@example.com`).
   - Highlight the **Manager Dashboard**:
     - 4 interactive **Chart.js** visualizations: Monthly Trends, Status Breakdown Doughnut, Leave Type Polar, and Department-wise usage.
     - Show the **Pending Requests Queue**.
     - Click **Approve** on a pending request: show that the balance is deducted, an audit record is created, the employee receives an in-app notification, and the attendance system records the leave date automatically!
     - Click **Reject** on another request: show the modal requesting a mandatory rejection reason.

5. **Step 5: Admin Control, Policy Configuration & Reports**
   - Log out and log in as Admin (`admin@example.com`).
   - Demonstrate **Leave Types Management** (`/admin/leave-types`): show how an admin can add or modify policies without hardcoding.
   - Demonstrate **Holiday Management** (`/admin/holidays`): holidays are automatically factored into working day calculations.
   - Demonstrate **Security Audit Logs** (`/admin/audit-logs`): show real-time audit trails of logins, approvals, cancellations, and profile edits.
   - Demonstrate **Reports & Analytics** (`/reports`): filter by department or date range, preview summary stats, and click **Export to CSV** to download a spreadsheet.

---

## 🔒 Security Best Practices Implemented

- **Password Hashing:** Stored with secure one-way salted hashes using Werkzeug (`scrypt`/`pbkdf2:sha256`).
- **Role-Based Access Control (RBAC):** Strict view decorators (`@login_required`, `@role_required`) protecting endpoints against direct URL manipulation.
- **Input Sanitization & Safe Handling:** Secure filename handling for uploaded documents with extension whitelisting (`png`, `jpg`, `pdf`, `doc`, `docx`).
- **Data Integrity:** Foreign keys, unique constraints, and transaction rollback protections against race conditions and negative balances.
- **Audit Logging:** Every critical transaction (login, apply, approve, reject, cancel, user edit) is persisted in the `AuditLog` table.

---

## 🚀 Future Enhancements

- Multi-factor authentication (MFA/OTP via Email/SMS).
- Automated email triggers using SMTP for instant manager notifications.
- Slack/Microsoft Teams webhook integration for leave approvals.
- Biometric hardware integration with biometric attendance machines.
- Employee document vault for digital contracts and payslips.

---

*Employee Leave Management System (ELMS) — Developed for CRT College Project Submission.*
