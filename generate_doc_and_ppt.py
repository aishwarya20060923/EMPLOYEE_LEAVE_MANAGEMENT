import os
import sys
from datetime import datetime, date

# --- 1. DOCX GENERATION ---
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def add_code_callout(doc, text, bg_hex="F1F5F9"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    cell = tbl.rows[0].cells[0]
    cell.width = Inches(6.5)
    set_cell_background(cell, bg_hex)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.name = "Consolas"
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(15, 23, 42)
    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_after = Pt(4)

def create_styled_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Style Header
    hdr_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        hdr_cells[i].text = header_text
        set_cell_background(hdr_cells[i], "1E293B") # Dark slate
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in p.runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(10)
            run.font.name = "Calibri"

    # Style Rows
    for r_idx, row_data in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        bg_color = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, cell_value in enumerate(row_data):
            row_cells[c_idx].text = str(cell_value)
            set_cell_background(row_cells[c_idx], bg_color)
            p = row_cells[c_idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.size = Pt(9.5)
                run.font.name = "Calibri"
                run.font.color.rgb = RGBColor(51, 65, 85)

    # Set column widths if provided
    if col_widths:
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Inches(width)

    # Add spacing after table
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_after = Pt(8)
    return table

def build_docx(filename="Employee_Leave_Management_System_Documentation.docx"):
    doc = docx.Document()

    # Set page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Document Header Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("EMPLOYEE LEAVE MANAGEMENT SYSTEM\n")
    title_run.font.size = Pt(24)
    title_run.font.bold = True
    title_run.font.name = "Arial"
    title_run.font.color.rgb = RGBColor(15, 23, 42) # Slate-900

    sub_run = title_p.add_run("Project README / Technical Reference Document")
    sub_run.font.size = Pt(14)
    sub_run.font.bold = True
    sub_run.font.name = "Calibri"
    sub_run.font.color.rgb = RGBColor(37, 99, 235) # Blue-600
    title_p.paragraph_format.space_after = Pt(20)

    # Helper for Section Headings
    def add_heading(text, level=1):
        h = doc.add_paragraph()
        run = h.add_run(text)
        run.font.name = "Arial"
        run.font.bold = True
        if level == 1:
            run.font.size = Pt(16)
            run.font.color.rgb = RGBColor(30, 41, 59)
            h.paragraph_format.space_before = Pt(16)
            h.paragraph_format.space_after = Pt(6)
        elif level == 2:
            run.font.size = Pt(13)
            run.font.color.rgb = RGBColor(37, 99, 235)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(4)
        return h

    def add_bullet(text, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        if bold_prefix:
            b_run = p.add_run(bold_prefix)
            b_run.font.bold = True
            b_run.font.name = "Calibri"
            b_run.font.size = Pt(10.5)
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor(51, 65, 85)

    def add_body(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor(51, 65, 85)
        return p

    # --- 1. ABOUT ---
    add_heading("1. About Employee Leave Management System")
    add_body(
        "A web-based Employee Leave Management System developed using Flask, SQLite, SQLAlchemy, "
        "HTML5, CSS3, JavaScript, and Chart.js. The application helps organizations manage employee records, "
        "leave categories, automated working-day calculations (auto-excluding weekends and national holidays), "
        "leave quota balances, multi-tier approvals/rejections, attendance tracking, team calendars, and "
        "analytical reports through a modern, responsive corporate dashboard."
    )

    # --- 2. FEATURES ---
    add_heading("2. Features")
    add_heading("Core System Capabilities", level=2)
    features = [
        "Multi-Role Authentication (Admin, Manager/HR, Employee) with secure session handling",
        "1-Click Quick Demo Login for instant evaluation during presentations",
        "Smart Working-Day Calculation excluding Saturdays and Sundays automatically",
        "Mandatory Gazetted Public Holiday Exclusion during leave duration computation",
        "Half-Day Leave Application Support (First Half / Second Half = 0.5 days)",
        "Supporting Document & Medical Certificate Upload (PNG, JPG, PDF, DOC, DOCX)",
        "Leave Balance Limit Validation (prevents negative balances)",
        "Overlapping and Conflicting Leave Request Detection",
        "Manager Approval Workflow with Automatic Quota Deduction",
        "Manager Rejection Workflow with Mandatory Rejection Reason capture",
        "Employee Leave Cancellation with Automatic Quota Restoration for future approved leaves",
        "Real-Time In-App Notification Center with dynamic unread counter badge",
        "Daily Employee Attendance Clock In / Clock Out tracking with 60-day history",
        "Attendance Synchronization automatically marking approved leave dates as 'Leave'",
        "Monthly Interactive Team Schedule & Holiday Calendar in Vanilla JavaScript",
        "Staff Directory Management with auto-quota provisioning for new employees",
        "Department Management with code abbreviations and active toggles",
        "Leave Policy Management (Max entitlement days, paid vs. unpaid, carry-forward rules)",
        "Gazetted Public Holiday Management (Mandatory vs. Optional holidays)",
        "Security & System Audit Trails logging all state changes with timestamps and IP addresses",
        "Multi-Filter Reporting Engine by department, employee, leave type, and custom date range",
        "Chart.js Visual Analytics (Monthly trends line chart, status doughnut, polar area, department usage)",
        "RFC-Compliant Tabular CSV Data Export for leave records, balances, and attendance",
        "Custom Corporate Error Pages for HTTP 403 Forbidden, 404 Not Found, and 500 Internal Error"
    ]
    for feat in features:
        add_bullet(feat)

    # --- 3. TECH STACK ---
    add_heading("3. Tech Stack")
    add_heading("Frontend", level=2)
    add_bullet(" Semantic structure, forms, file inputs, accessible layout", "HTML5:")
    add_bullet(" Custom modern corporate SaaS design system (variables, flexbox, grid)", "CSS3:")
    add_bullet(" Vanilla ES6+ for live AJAX day calculation, modals, alerts, and calendar", "JavaScript:")
    add_bullet(" Responsive client-side charting (Monthly trend line, status doughnut, dept bar)", "Chart.js 4.4.1:")
    add_bullet(" Server-side template rendering and inheritance", "Jinja2:")

    add_heading("Backend", level=2)
    add_bullet(" Core programming language (v3.11)", "Python:")
    add_bullet(" Web framework, Application Factory pattern, and Blueprint routing", "Flask 3.1.3:")
    add_bullet(" Object-Relational Mapper (ORM) with cascading relationships", "Flask-SQLAlchemy 3.1.1:")
    add_bullet(" PBKDF2/SHA-256 password hashing and secure filename sanitization", "Werkzeug 3.1.3:")

    add_heading("Database", level=2)
    add_bullet(" Relational database engine stored at instance/database.db", "SQLite 3:")

    # --- 4. PROJECT STRUCTURE ---
    add_heading("4. Project Structure")
    struct_text = (
        "Employee-Leave-Management-System/\n"
        "├── app.py                     # Application factory, blueprints, context processors, error handlers\n"
        "├── config.py                  # Database URI, upload configuration, session secret keys\n"
        "├── requirements.txt           # Python dependency specifications\n"
        "├── README.md                  # Comprehensive project documentation & viva guide\n"
        "├── seed.py                    # Database schema creator and demo data generator\n"
        "├── test_app.py                # Core unit test suite (7 tests)\n"
        "├── verify_all.py              # Master 31-point end-to-end verification suite (15 tests)\n"
        "├── instance/\n"
        "│   └── database.db            # SQLite relational database file\n"
        "├── models/\n"
        "│   ├── __init__.py            # Model package initializer\n"
        "│   └── models.py              # 10 SQLAlchemy ORM models (User, Employee, LeaveRequest, etc.)\n"
        "├── routes/\n"
        "│   ├── __init__.py            # Blueprint package exports\n"
        "│   ├── auth.py                # Authentication, sessions, quick-login demo routes\n"
        "│   ├── employee.py            # Employee dashboard, apply leave, history, calendar, attendance\n"
        "│   ├── manager.py             # Review queue, approve/reject, analytics, team attendance\n"
        "│   ├── admin.py               # Staff directory, departments, policies, holidays, audit logs\n"
        "│   └── reports.py             # Report filtering, summary calculations, CSV export\n"
        "├── utils/\n"
        "│   ├── __init__.py            # Utility package exports\n"
        "│   └── helpers.py             # RBAC decorators, day calculation, conflict checking, audit logger\n"
        "├── templates/\n"
        "│   ├── base.html              # Shared corporate layout with sidebar, header, alerts, and modals\n"
        "│   ├── auth/login.html        # Login view with 1-click test fill\n"
        "│   ├── employee/              # 7 views: dashboard, apply_leave, my_leaves, calendar, attendance, etc.\n"
        "│   ├── manager/               # 6 views: dashboard, leave_requests, employees, calendar, attendance, etc.\n"
        "│   ├── admin/                 # 8 views: dashboard, employees, departments, leave_types, holidays, etc.\n"
        "│   ├── reports/index.html     # Report tables, summary KPI cards, CSV export\n"
        "│   └── errors/                # Custom 403.html, 404.html, 500.html error pages\n"
        "└── static/\n"
        "    ├── css/styles.css         # Modern corporate stylesheet, responsive drawer, sticky actions\n"
        "    ├── js/main.js             # Live days calculator, modal controller, alert dismiss, demo filler\n"
        "    ├── js/calendar.js         # Vanilla JS interactive monthly schedule calendar\n"
        "    └── uploads/               # Uploaded leave attachments (documents/certificates)"
    )
    add_code_callout(doc, struct_text, "F1F5F9")

    # --- 5. DATABASE TABLES ---
    add_heading("5. Database Tables")
    add_body("The system uses SQLite to store relational application data across 10 normalized tables.")

    tables_data = [
        ("Users Table (`users`)", [
            ("User ID (`id`)", "Unique primary key integer identifier"),
            ("Email (`email`)", "Unique official corporate email address (Indexed)"),
            ("Password Hash (`password_hash`)", "PBKDF2/SHA-256 salted password hash string"),
            ("Role (`role`)", "Authorization role: 'Admin', 'Manager', or 'Employee'"),
            ("Is Active (`is_active`)", "Boolean flag indicating account active status"),
            ("Created At (`created_at`)", "Account registration UTC timestamp")
        ]),
        ("Departments Table (`departments`)", [
            ("Department ID (`id`)", "Unique primary key integer identifier"),
            ("Name (`name`)", "Full department name (e.g., Engineering, Human Resources)"),
            ("Code (`code`)", "Unique short code abbreviation (e.g., ENG, HR, FIN)"),
            ("Description (`description`)", "Narrative scope of the department"),
            ("Is Active (`is_active`)", "Boolean status flag for the department"),
            ("Created At (`created_at`)", "Record creation UTC timestamp")
        ]),
        ("Employees Table (`employees`)", [
            ("Employee Record ID (`id`)", "Unique primary key integer identifier"),
            ("User ID (`user_id`)", "Foreign key referencing users.id (1-to-1 relationship)"),
            ("Employee ID (`employee_id`)", "Unique corporate employee code (e.g., EMP-101, EMP-004)"),
            ("First Name (`first_name`)", "Employee given name"),
            ("Last Name (`last_name`)", "Employee surname / family name"),
            ("Phone (`phone`)", "Employee contact phone number"),
            ("Department ID (`department_id`)", "Foreign key referencing departments.id"),
            ("Designation (`designation`)", "Official job position title"),
            ("Joining Date (`joining_date`)", "Date of official employment commencement"),
            ("Manager ID (`manager_id`)", "Self-referencing foreign key to employees.id (manager hierarchy)"),
            ("Gender (`gender`)", "Gender identity"),
            ("Address (`address`)", "Residential address"),
            ("Status (`status`)", "Employment status: 'Active' or 'Inactive'"),
            ("Created At (`created_at`)", "Employee profile creation UTC timestamp")
        ]),
        ("Leave Types Table (`leave_types`)", [
            ("Leave Type ID (`id`)", "Unique primary key integer identifier"),
            ("Name (`name`)", "Leave category title (e.g., Casual Leave, Sick Leave, Annual Leave)"),
            ("Code (`code`)", "Unique policy category abbreviation (e.g., CL, SL, AL, WFH)"),
            ("Description (`description`)", "Policy rules, documentation requirements, and conditions"),
            ("Max Days (`max_days`)", "Standard annual quota allotment (e.g., 12.0 days)"),
            ("Is Paid (`is_paid`)", "Boolean indicating paid leave vs. Loss of Pay (LOP)"),
            ("Carry Forward (`carry_forward`)", "Boolean eligibility for year-end carry-forward"),
            ("Is Active (`is_active`)", "Boolean policy activation status flag"),
            ("Created At (`created_at`)", "Policy definition UTC timestamp")
        ]),
        ("Leave Balances Table (`leave_balances`)", [
            ("Balance ID (`id`)", "Unique primary key integer identifier"),
            ("Employee ID (`employee_id`)", "Foreign key referencing employees.id"),
            ("Leave Type ID (`leave_type_id`)", "Foreign key referencing leave_types.id"),
            ("Year (`year`)", "Quota calendar year (e.g., 2026)"),
            ("Entitled Days (`entitled_days`)", "Total annual quota days assigned"),
            ("Used Days (`used_days`)", "Accumulated days deducted upon manager approval"),
            ("Remaining Days (`remaining_days`)", "Current available quota balance (entitled - used)")
        ]),
        ("Leave Requests Table (`leave_requests`)", [
            ("Request ID (`id`)", "Unique primary key integer identifier"),
            ("Request Number (`request_number`)", "Unique corporate reference code (e.g., LR-2026-0001)"),
            ("Employee ID (`employee_id`)", "Foreign key referencing applicant in employees.id"),
            ("Leave Type ID (`leave_type_id`)", "Foreign key referencing leave_types.id"),
            ("Start Date (`start_date`)", "Starting date of requested absence"),
            ("End Date (`end_date`)", "Concluding date of requested absence"),
            ("Is Half Day (`is_half_day`)", "Boolean flag indicating half-day request"),
            ("Half Day Type (`half_day_type`)", "Selected half-day slot ('First Half' or 'Second Half')"),
            ("Days Requested (`days_requested`)", "Calculated net working days excluding weekends/holidays"),
            ("Reason (`reason`)", "Detailed textual justification provided by employee"),
            ("Attachment (`attachment_filename`)", "Filename of uploaded proof document / medical certificate"),
            ("Status (`status`)", "Workflow lifecycle status ('Pending', 'Approved', 'Rejected', 'Cancelled')"),
            ("Reviewed By ID (`reviewed_by_id`)", "Foreign key referencing reviewer in employees.id"),
            ("Reviewed At (`reviewed_at`)", "UTC timestamp of manager approval/rejection"),
            ("Rejection Reason (`rejection_reason`)", "Mandatory justification recorded upon rejection"),
            ("Applied At (`applied_at`)", "Submission UTC timestamp"),
            ("Cancelled At (`cancelled_at`)", "Cancellation UTC timestamp (if cancelled)"),
            ("Cancellation Reason", "Justification recorded upon cancellation")
        ]),
        ("Holidays Table (`holidays`)", [
            ("Holiday ID (`id`)", "Unique primary key integer identifier"),
            ("Name (`name`)", "Gazetted public holiday name (e.g., Republic Day, Independence Day)"),
            ("Date (`date`)", "Calendar date of the holiday (Unique)"),
            ("Description (`description`)", "Observance description"),
            ("Is Optional (`is_optional`)", "Mandatory company shutdown (False) vs. optional restricted holiday (True)")
        ]),
        ("Attendance Table (`attendances`)", [
            ("Attendance ID (`id`)", "Unique primary key integer identifier"),
            ("Employee ID (`employee_id`)", "Foreign key referencing employees.id"),
            ("Date (`date`)", "Calendar date of attendance"),
            ("Status (`status`)", "Attendance state: 'Present', 'Absent', 'Leave', 'Half Day', 'Holiday'"),
            ("Check In (`check_in`)", "Recorded clock-in time string (e.g., '09:15')"),
            ("Check Out (`check_out`)", "Recorded clock-out time string (e.g., '18:00')"),
            ("Notes (`notes`)", "Automated system reference note (e.g., 'Approved AL (LR-2026-0001)')")
        ]),
        ("Notifications Table (`notifications`)", [
            ("Notification ID (`id`)", "Unique primary key integer identifier"),
            ("User ID (`user_id`)", "Foreign key referencing recipient in users.id"),
            ("Title (`title`)", "Short subject heading of the alert"),
            ("Message (`message`)", "Detailed explanatory notification message"),
            ("Category (`category`)", "UI color indicator ('info', 'success', 'warning', 'danger')"),
            ("Link (`link`)", "In-app URL target for 1-click navigation"),
            ("Is Read (`is_read`)", "Boolean flag indicating read status")
        ]),
        ("Audit Logs Table (`audit_logs`)", [
            ("Log ID (`id`)", "Unique primary key integer identifier"),
            ("User ID (`user_id`)", "Foreign key referencing actor in users.id (nullable)"),
            ("User Email (`user_email`)", "Email of actor who executed the transaction"),
            ("Action (`action`)", "Transaction name (e.g., 'Leave Approved', 'User Login')"),
            ("Record Type (`record_type`)", "Target entity type (e.g., 'LeaveRequest', 'Employee')"),
            ("Record ID (`record_id`)", "Identifier of the affected entity"),
            ("Details (`details`)", "Human-readable narrative summary of changes"),
            ("IP Address (`ip_address`)", "Client network IP address"),
            ("Timestamp (`timestamp`)", "Exact UTC timestamp of event")
        ])
    ]

    for title, rows in tables_data:
        add_heading(title, level=2)
        create_styled_table(doc, ["Field Name", "Description & Constraints"], rows, [2.5, 4.0])

    # --- 6. APPLICATION WORKFLOW ---
    add_heading("6. Application Workflow")
    workflow_steps = [
        "1. Authentication & Role Redirection: User logs into portal via /login; session stores credentials and directs user to their role-specific dashboard.",
        "2. Balance Inspection: Employee checks dashboard summary metric tiles (Total, Used, Remaining) and category progress bars.",
        "3. Leave Application: Employee navigates to /employee/apply-leave, picks leave category and calendar dates.",
        "4. Asynchronous Working-Day Math: System calls /employee/api/calculate-days; dynamically excludes Saturdays, Sundays, and gazetted holidays.",
        "5. Half-Day & Proof Attachment: Optional half-day slot toggle (0.5 days) and optional supporting medical document upload.",
        "6. Validation Safeguards: Server re-verifies date sequence, enforces positive balance checks, and validates absence of overlapping requests.",
        "7. Request Submission: LeaveRequest row is created with status 'Pending' and formatted reference code LR-YYYY-XXXX.",
        "8. In-App Notifications: Dispatched immediately to employee and reviewing manager.",
        "9. Security Audit Logging: State creation logged in AuditLog table with actor timestamp and client IP.",
        "10. Manager Review Queue: Manager accesses /manager/leave-requests featuring sticky Approve and Reject action buttons.",
        "11. Approval Execution: Quota is deducted (used_days += requested, remaining_days -= requested), status becomes 'Approved', and attendance is marked as 'Leave'.",
        "12. Rejection Execution: Manager enters mandatory justification in modal; status becomes 'Rejected', balances remain untouched.",
        "13. Employee Cancellation: Employee can cancel pending requests, or cancel future approved leaves with automatic quota restoration.",
        "14. Reporting & CSV Export: Managers/Admins filter leave, balance, and attendance records and export RFC-compliant CSV files."
    ]
    for step in workflow_steps:
        p_step = doc.add_paragraph()
        p_step.paragraph_format.space_after = Pt(4)
        run_step = p_step.add_run(step)
        run_step.font.name = "Calibri"
        run_step.font.size = Pt(10)
        run_step.font.color.rgb = RGBColor(51, 65, 85)

    # --- 7. API INTEGRATION ---
    add_heading("7. API Integration")
    add_body(
        "The application utilizes internal RESTful JSON endpoints to provide real-time, asynchronous UI updates "
        "without requiring full page reloads. The project is completely self-contained and does not rely on third-party cloud APIs."
    )
    api_flow = (
        "User Input (Date Selection / Button Click)\n"
        "       ↓\n"
        "JavaScript Event Listener (Fetch API)\n"
        "       ↓\n"
        "Flask Internal Route (/employee/api/calculate-days)\n"
        "       ↓\n"
        "Business Logic (Weekend & Holiday Exclusion Algorithm)\n"
        "       ↓\n"
        "JSON Response ({ days: 2.0, weekends_count: 2, holidays_count: 1 })\n"
        "       ↓\n"
        "Process & Update DOM Elements\n"
        "       ↓\n"
        "Display Calculated Days & Balance Warnings to User"
    )
    add_code_callout(doc, api_flow, "F8FAFC")

    api_rows = [
        ("POST /employee/api/calculate-days", "JSON endpoint calculating net working days excluding weekends/holidays"),
        ("GET /employee/api/calendar-events", "JSON feed supplying personal leave and holiday events to monthly calendar"),
        ("GET /manager/api/calendar-events", "JSON feed supplying organization leaves with optional department filtering"),
        ("POST /employee/notifications/read/<id>", "JSON endpoint marking an individual notification alert as read"),
        ("GET /reports/export-csv", "Streams RFC-compliant downloadable CSV report files")
    ]
    create_styled_table(doc, ["Endpoint Route", "Purpose & Response"], api_rows, [2.5, 4.0])

    # --- 8. USER INTERFACE ---
    add_heading("8. User Interface")
    ui_elements = [
        "Navigation Bar & Sidebar: Role-adaptive navigation sections (Self-Service, Team Management, Administration) with badge counters",
        "Top Header: Page title breadcrumb, current system date, and notification bell counter",
        "Dashboard Cards: Summary KPI tiles (Total Entitlement, Leaves Used, Remaining Quota, Pending Approvals)",
        "Progress Bars: Color-coded visual consumption bars for each individual leave category",
        "Interactive Forms: Form inputs with live calculation notes, half-day toggles, and drag-and-drop file upload zones",
        "Management Tables: Data tables with zebra striping, search filters, status pill badges, and sticky right-pinned action buttons",
        "Interactive Modals: Overlay dialogs for mandatory rejection reasons and cancellation confirmations",
        "Schedule Calendar: Vanilla JavaScript monthly grid with month controls, today jump, and colored event chips",
        "Analytics Charts: 4 responsive Chart.js dashboard charts (Monthly Trend Line, Status Doughnut, Type Polar, Department Bar)",
        "Responsive Mobile Drawer: Slide-over navigation panel with backdrop dismiss for mobile and tablet screens"
    ]
    for el in ui_elements:
        add_bullet(el)

    # --- 9. INSTALLATION ---
    add_heading("9. Installation")
    add_body("Follow these steps to set up and run the Employee Leave Management System locally:")
    add_heading("1. Clone or Download Project", level=2)
    p_c1 = doc.add_paragraph()
    r_c1 = p_c1.add_run("cd C:\\Users\\Lenovo\\.gemini\\antigravity\\scratch\\employee_leave_management")
    r_c1.font.name = "Consolas"
    r_c1.font.size = Pt(9.5)

    add_heading("2. Create Virtual Environment", level=2)
    p_c2 = doc.add_paragraph()
    r_c2 = p_c2.add_run("python -m venv venv")
    r_c2.font.name = "Consolas"
    r_c2.font.size = Pt(9.5)

    add_heading("3. Activate Virtual Environment", level=2)
    p_c3 = doc.add_paragraph()
    r_c3 = p_c3.add_run("# Windows (PowerShell):\n.\\venv\\Scripts\\Activate.ps1\n\n# Windows (CMD):\nvenv\\Scripts\\activate.bat\n\n# Linux / macOS:\nsource venv/bin/activate")
    r_c3.font.name = "Consolas"
    r_c3.font.size = Pt(9.5)

    # --- 10. INSTALL DEPENDENCIES ---
    add_heading("10. Install Dependencies")
    p_c4 = doc.add_paragraph()
    r_c4 = p_c4.add_run("pip install -r requirements.txt")
    r_c4.font.name = "Consolas"
    r_c4.font.size = Pt(9.5)

    add_body("Contents of requirements.txt:")
    p_req = doc.add_paragraph()
    r_req = p_req.add_run("Flask>=3.0.0\nFlask-SQLAlchemy>=3.1.0\nWerkzeug>=3.0.0")
    r_req.font.name = "Consolas"
    r_req.font.size = Pt(9.5)

    add_heading("Database Seeding", level=2)
    p_seed = doc.add_paragraph()
    r_seed = p_seed.add_run("python seed.py")
    r_seed.font.name = "Consolas"
    r_seed.font.size = Pt(9.5)
    add_body("This command creates all 10 SQLite database tables and seeds 12 demo accounts across all roles, departments, leave types, 2026 holidays, leave requests, attendance records, and audit logs.")

    # --- 11. RUN APPLICATION ---
    add_heading("11. Run the Application")
    p_run = doc.add_paragraph()
    r_run = p_run.add_run("python app.py")
    r_run.font.name = "Consolas"
    r_run.font.size = Pt(9.5)

    add_body("Open your web browser and navigate to: http://127.0.0.1:5000/")

    add_heading("Pre-configured Demo Credentials", level=2)
    creds_rows = [
        ("Admin", "admin@example.com", "Admin@123", "Rajesh Sharma (IT Head & Admin)"),
        ("HR / Manager", "manager@example.com", "Manager@123", "Priya Patel (Senior HR Manager)"),
        ("Tech Manager", "vikram.singh@example.com", "Manager@123", "Vikram Singh (Engineering Manager)"),
        ("Employee", "employee@example.com", "Employee@123", "Rahul Verma (Senior Developer)"),
        ("Employee", "neha.gupta@example.com", "Employee@123", "Neha Gupta (Product Designer)"),
        ("Employee", "amit.nair@example.com", "Employee@123", "Amit Nair (Financial Analyst)")
    ]
    create_styled_table(doc, ["Role", "Email Address", "Password", "Name & Designation"], creds_rows, [1.2, 1.8, 1.2, 2.3])

    # --- 12. SCREENSHOTS ---
    add_heading("12. Screenshots")
    add_body("Add your actual project screenshots here:")
    screenshots = [
        "Login Screen: ![Login](screenshots/login.png)",
        "Employee Dashboard: ![Employee Dashboard](screenshots/employee_dashboard.png)",
        "Apply Leave (Live Calculator): ![Apply Leave](screenshots/apply_leave.png)",
        "Leave History & Cancellation: ![My Leaves](screenshots/my_leaves.png)",
        "Manager Analytics Dashboard: ![Manager Dashboard](screenshots/manager_dashboard.png)",
        "Leave Review Queue: ![Leave Requests](screenshots/leave_requests.png)",
        "Rejection Reason Modal: ![Rejection Modal](screenshots/rejection_modal.png)",
        "Interactive Leave Calendar: ![Leave Calendar](screenshots/calendar.png)",
        "Admin Staff Directory: ![Staff Directory](screenshots/employees_admin.png)",
        "Security Audit Logs: ![Audit Logs](screenshots/audit_logs.png)",
        "Reports & CSV Export: ![Reports View](screenshots/reports.png)"
    ]
    for sc in screenshots:
        add_bullet(sc)

    # --- 13. FUTURE ENHANCEMENTS ---
    add_heading("13. Future Enhancements")
    enhancements = [
        "Two-Factor Authentication (2FA/OTP via Email or SMS) for privileged administrative actions",
        "Automated Email Notifications (SMTP integration) for real-time leave approval/rejection alerts",
        "Slack & Microsoft Teams Webhook Integration for 1-click approvals directly inside channels",
        "Hardware Biometric Device Integration directly synchronizing physical RFID/fingerprint scanners",
        "Multi-Tier Hierarchical Approval Routing (Team Lead → Department Manager → HR Director)",
        "Optical Character Recognition (OCR) for automated validation of uploaded medical certificates"
    ]
    for enh in enhancements:
        add_bullet(enh)

    # --- 14. LEARNING OUTCOMES ---
    add_heading("14. Learning Outcomes")
    outcomes = [
        "Modular full-stack web architecture using Python and Flask Application Factory pattern",
        "Implementing Role-Based Access Control (RBAC) via custom Python view decorators",
        "Relational schema modeling in SQLAlchemy with foreign keys, cascading deletions, and composite uniqueness",
        "Algorithmic business rules for working-day calculations with calendar holiday and weekend exclusions",
        "Concurrency-safe conflict detection to prevent overlapping leave date requests",
        "Asynchronous client-server communication using Vanilla JavaScript Fetch API without frontend frameworks",
        "Interactive data visualization and analytical dashboard design using Chart.js",
        "Enterprise security standards: PBKDF2/SHA-256 salted password hashing, input sanitization, and audit trails",
        "Automated testing and end-to-end verification using Python's built-in unittest framework"
    ]
    for out in outcomes:
        add_bullet(out)

    # --- 15. AUTHOR ---
    add_heading("15. Author")
    add_body("Student Name: Your Name\nUSN / Roll Number: Your USN\nCourse: BCA / B.Tech / MCA\nProject: Employee Leave Management System (ELMS)\nTechnologies: Python | Flask | SQLite | SQLAlchemy | HTML5 | CSS3 | JavaScript | Chart.js")

    # --- 16. GITHUB & LICENSE ---
    add_heading("16. GitHub")
    add_body("https://github.com/your-username/employee-leave-management-system")

    add_heading("License", level=2)
    add_body("This project is developed for educational, academic, CRT evaluation, and portfolio demonstration purposes under the MIT License.")

    doc.save(filename)
    print(f"Successfully generated Word document: {filename}")


# --- 2. PPTX GENERATION ---
from pptx import Presentation
from pptx.util import Inches as PptInches, Pt as PptPt
from pptx.dml.color import RGBColor as PptRGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def build_pptx(filename="Employee_Leave_Management_System_Presentation.pptx"):
    prs = Presentation()
    prs.slide_width = PptInches(13.333) # 16:9 widescreen
    prs.slide_height = PptInches(7.5)
    blank_layout = prs.slide_layouts[6] # Blank slide

    # Color Palette
    COLOR_BG_DARK = PptRGBColor(15, 23, 42)    # Slate 900
    COLOR_CARD = PptRGBColor(30, 41, 59)       # Slate 800
    COLOR_PRIMARY = PptRGBColor(37, 99, 235)   # Blue 600
    COLOR_ACCENT = PptRGBColor(16, 185, 129)   # Emerald 500
    COLOR_WHITE = PptRGBColor(255, 255, 255)
    COLOR_MUTED = PptRGBColor(148, 163, 184)   # Slate 400
    COLOR_LIGHT_BG = PptRGBColor(248, 250, 252)# Slate 50
    COLOR_LIGHT_CARD = PptRGBColor(255, 255, 255)
    COLOR_TEXT_DARK = PptRGBColor(30, 41, 59)

    def add_header(slide, title_text, category="EMPLOYEE LEAVE MANAGEMENT SYSTEM"):
        # Category label
        cat_box = slide.shapes.add_textbox(PptInches(0.8), PptInches(0.5), PptInches(11.7), PptInches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = PptPt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_PRIMARY
        p_cat.font.name = "Calibri"

        # Main Title
        title_box = slide.shapes.add_textbox(PptInches(0.8), PptInches(0.8), PptInches(11.7), PptInches(0.8))
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = PptPt(24)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_DARK
        p.font.name = "Arial"

        # Horizontal divider line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, PptInches(0.8), PptInches(1.6), PptInches(11.7), PptInches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = PptRGBColor(226, 232, 240)
        line.line.color.rgb = PptRGBColor(226, 232, 240)

    # --- SLIDE 1: TITLE SLIDE (Dark Background) ---
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = COLOR_BG_DARK
    bg1.line.color.rgb = COLOR_BG_DARK

    tbox1 = s1.shapes.add_textbox(PptInches(1.0), PptInches(1.8), PptInches(11.3), PptInches(3.8))
    tf1 = tbox1.text_frame
    tf1.word_wrap = True

    p_badge = tf1.paragraphs[0]
    p_badge.text = "CRT COLLEGE PROJECT SUBMISSION • 2026"
    p_badge.font.size = PptPt(12)
    p_badge.font.bold = True
    p_badge.font.color.rgb = COLOR_ACCENT
    p_badge.font.name = "Calibri"
    p_badge.space_after = PptPt(14)

    p_t = tf1.add_paragraph()
    p_t.text = "Employee Leave Management System"
    p_t.font.size = PptPt(36)
    p_t.font.bold = True
    p_t.font.color.rgb = COLOR_WHITE
    p_t.font.name = "Arial"
    p_t.space_after = PptPt(12)

    p_sub = tf1.add_paragraph()
    p_sub.text = "Full-Stack Web Portal with Role-Based Access Control, Smart Working-Day Calculation, & Attendance Integration"
    p_sub.font.size = PptPt(16)
    p_sub.font.color.rgb = COLOR_MUTED
    p_sub.font.name = "Calibri"
    p_sub.space_after = PptPt(24)

    p_meta = tf1.add_paragraph()
    p_meta.text = "Technologies: Python | Flask | SQLite | SQLAlchemy | Vanilla JS | HTML5 | CSS3 | Chart.js"
    p_meta.font.size = PptPt(12)
    p_meta.font.color.rgb = PptRGBColor(96, 165, 250) # Blue 400
    p_meta.font.bold = True

    # --- SLIDE 2: PROJECT OVERVIEW ---
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Project Overview & Problem Statement")

    # Left card: Problem
    c_prob = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(0.8), PptInches(1.9), PptInches(5.6), PptInches(5.0))
    c_prob.fill.solid()
    c_prob.fill.fore_color.rgb = PptRGBColor(254, 242, 242) # Light red
    c_prob.line.color.rgb = PptRGBColor(254, 202, 202)

    tf_p = c_prob.text_frame
    tf_p.word_wrap = True
    p1 = tf_p.paragraphs[0]
    p1.text = "Traditional Leave Management Challenges"
    p1.font.bold = True
    p1.font.size = PptPt(16)
    p1.font.color.rgb = PptRGBColor(185, 28, 28)
    p1.space_after = PptPt(14)

    probs = [
        "Manual paperwork & spreadsheet calculations prone to error",
        "Weekends & holidays manually counted or miscalculated",
        "No real-time balance tracking causing negative leave quotas",
        "Disjointed approval chains with no audit visibility",
        "Attendance records disconnected from approved leave days",
        "Lack of central reporting and visual analytics"
    ]
    for pr in probs:
        p = tf_p.add_paragraph()
        p.text = f"•  {pr}"
        p.font.size = PptPt(12)
        p.font.color.rgb = PptRGBColor(127, 29, 29)
        p.space_after = PptPt(8)

    # Right card: Solution
    c_sol = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(6.8), PptInches(1.9), PptInches(5.7), PptInches(5.0))
    c_sol.fill.solid()
    c_sol.fill.fore_color.rgb = PptRGBColor(240, 253, 244) # Light green
    c_sol.line.color.rgb = PptRGBColor(187, 247, 208)

    tf_s = c_sol.text_frame
    tf_s.word_wrap = True
    p2 = tf_s.paragraphs[0]
    p2.text = "The ELMS Solution"
    p2.font.bold = True
    p2.font.size = PptPt(16)
    p2.font.color.rgb = PptRGBColor(21, 128, 61)
    p2.space_after = PptPt(14)

    sols = [
        "100% automated web workflow from application to approval",
        "Smart algorithm automatically excluding weekends & gazetted holidays",
        "Strict quota validation & conflict detection preventing overlaps",
        "Transparent multi-role access (Admin, Manager/HR, Employee)",
        "Automated attendance synchronization on leave approval",
        "Real-time Chart.js interactive charts & RFC-compliant CSV export"
    ]
    for sl in sols:
        p = tf_s.add_paragraph()
        p.text = f"✔  {sl}"
        p.font.size = PptPt(12)
        p.font.color.rgb = PptRGBColor(20, 83, 45)
        p.space_after = PptPt(8)

    # --- SLIDE 3: TECH STACK ---
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Architecture & Technology Stack")

    layers = [
        ("Frontend Layer", "HTML5 • Custom CSS3 • Vanilla JavaScript • Chart.js", [
            "Semantic corporate interface without heavy JS frameworks",
            "Responsive drawer navigation & mobile optimization",
            "Live AJAX day calculation via Fetch API",
            "Interactive monthly calendar component",
            "4 interactive Chart.js visualizations"
        ], PptRGBColor(239, 246, 255), PptRGBColor(37, 99, 235)),
        ("Backend Layer", "Python 3.11 • Flask 3.1.3 • Werkzeug 3.1.3", [
            "Application Factory pattern & modular Blueprints",
            "Custom RBAC decorators (@login_required, @role_required)",
            "Centralized business logic algorithms",
            "PBKDF2/SHA-256 cryptographic password hashing",
            "Dynamic CSV streaming and error handling"
        ], PptRGBColor(245, 243, 255), PptRGBColor(124, 58, 237)),
        ("Database Layer", "SQLite 3 • Flask-SQLAlchemy 3.1.1 ORM", [
            "10 normalized relational models with cascade rules",
            "Foreign keys & composite unique constraints",
            "Self-referential manager-subordinate hierarchy",
            "Transactional integrity with automatic rollback",
            "Comprehensive seed data (12 accounts, 2026 holidays)"
        ], PptRGBColor(240, 253, 250), PptRGBColor(13, 148, 136))
    ]

    for idx, (title, sub, bullets, bg_c, border_c) in enumerate(layers):
        x = PptInches(0.8 + idx * 4.0)
        c = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, PptInches(1.9), PptInches(3.7), PptInches(5.0))
        c.fill.solid()
        c.fill.fore_color.rgb = bg_c
        c.line.color.rgb = border_c
        c.line.width = PptPt(1.5)

        tf = c.text_frame
        tf.word_wrap = True
        pt = tf.paragraphs[0]
        pt.text = title
        pt.font.bold = True
        pt.font.size = PptPt(16)
        pt.font.color.rgb = border_c

        ps = tf.add_paragraph()
        ps.text = sub
        ps.font.size = PptPt(10)
        ps.font.color.rgb = PptRGBColor(100, 116, 139)
        ps.space_after = PptPt(12)

        for b in bullets:
            pb = tf.add_paragraph()
            pb.text = f"• {b}"
            pb.font.size = PptPt(11)
            pb.font.color.rgb = COLOR_TEXT_DARK
            pb.space_after = PptPt(6)

    # --- SLIDE 4: USER ROLES ---
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Role-Based Access Control (RBAC)")

    roles = [
        ("Employee (Self-Service)", "Rahul Verma / employee@example.com", [
            "Personal dashboard with KPI metric cards & balances",
            "Apply for leave with live working-day computation",
            "Option for Half-Day slots (0.5 days) & document uploads",
            "Track leave history and cancel eligible future requests",
            "Personal interactive leave & holiday calendar",
            "Daily clock-in/out attendance with 60-day history",
            "Profile management and password changer"
        ], PptRGBColor(59, 130, 246)),
        ("Manager / HR", "Priya Patel / manager@example.com", [
            "Review queue of all pending leave requests",
            "One-click Approve with automatic balance deduction",
            "Reject with mandatory explanation reason capture",
            "4 real-time Chart.js visual analytics & department usage",
            "Organization attendance sheet by department and date",
            "Employee 360-degree profile & balance inspector",
            "Multi-filter reports & CSV spreadsheet export"
        ], PptRGBColor(16, 185, 129)),
        ("Administrator", "Rajesh Sharma / admin@example.com", [
            "Global system oversight & quick-action shortcuts",
            "Staff management: Add, edit, toggle Active/Inactive",
            "Auto-provisioning of leave balances for new hires",
            "Department CRUD & code configuration",
            "Leave policy manager (Entitlement, paid flag, carry-over)",
            "Gazetted holiday schedule manager (Mandatory vs. Optional)",
            "System security audit trail inspector with action filters"
        ], PptRGBColor(245, 158, 11))
    ]

    for idx, (rtitle, demo_u, items, accent_c) in enumerate(roles):
        x = PptInches(0.8 + idx * 4.0)
        c = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, PptInches(1.9), PptInches(3.7), PptInches(5.0))
        c.fill.solid()
        c.fill.fore_color.rgb = PptRGBColor(255, 255, 255)
        c.line.color.rgb = accent_c
        c.line.width = PptPt(2)

        tf = c.text_frame
        tf.word_wrap = True
        pt = tf.paragraphs[0]
        pt.text = rtitle
        pt.font.bold = True
        pt.font.size = PptPt(16)
        pt.font.color.rgb = accent_c

        pu = tf.add_paragraph()
        pu.text = demo_u
        pu.font.size = PptPt(9.5)
        pu.font.color.rgb = PptRGBColor(100, 116, 139)
        pu.space_after = PptPt(12)

        for it in items:
            p = tf.add_paragraph()
            p.text = f"✔ {it}"
            p.font.size = PptPt(10.5)
            p.font.color.rgb = COLOR_TEXT_DARK
            p.space_after = PptPt(6)

    # --- SLIDE 5: CORE BUSINESS LOGIC ---
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Core Business Logic & Automated Calculations")

    logic_blocks = [
        ("1. Smart Working-Day Calculation", "Iterates date span. Automatically detects and skips Saturdays (weekday=5) and Sundays (weekday=6), plus any matching mandatory gazetted public holidays in the Holiday table. Half-day requests evaluate to exactly 0.5 days."),
        ("2. Balance Limits & Conflict Detection", "Validates that remaining balance >= requested working days. Performs range collision detection: checks for any existing Pending or Approved requests overlapping start_date <= end_date AND end_date >= start_date."),
        ("3. Approval & Attendance Synchronization", "Upon manager approval, balance used_days increases and remaining_days updates. Simultaneously loops through all non-weekend dates and creates or updates Attendance records as 'Leave'."),
        ("4. Safe Cancellation & Quota Restoration", "Pending requests can be cancelled anytime. Approved requests can be cancelled only if start_date >= today (future leave). Automatically restores deducted days back to available balance.")
    ]

    for idx, (ltitle, ldesc) in enumerate(logic_blocks):
        y = PptInches(1.9 + idx * 1.25)
        box = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(0.8), y, PptInches(11.7), PptInches(1.1))
        box.fill.solid()
        box.fill.fore_color.rgb = PptRGBColor(248, 250, 252)
        box.line.color.rgb = PptRGBColor(203, 213, 225)

        tf = box.text_frame
        tf.word_wrap = True
        pt = tf.paragraphs[0]
        pt.text = ltitle
        pt.font.bold = True
        pt.font.size = PptPt(13)
        pt.font.color.rgb = COLOR_PRIMARY
        pt.space_after = PptPt(3)

        pd = tf.add_paragraph()
        pd.text = ldesc
        pd.font.size = PptPt(10.5)
        pd.font.color.rgb = COLOR_TEXT_DARK

    # --- SLIDE 6: DATABASE SCHEMA ---
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Database Architecture (10 Relational Models)")

    models_summary = [
        ("users", "User credentials, role, status, password hash"),
        ("departments", "Organizational units (Engineering, HR, etc.)"),
        ("employees", "Staff directory, manager hierarchy, user mapping"),
        ("leave_types", "Policies: Casual, Sick, Annual, LOP, WFH"),
        ("leave_balances", "Yearly entitled, used, and remaining quota"),
        ("leave_requests", "Applications, dates, reason, status, review"),
        ("holidays", "2026 gazetted public holidays (mandatory/opt)"),
        ("attendances", "Daily clock in/out and synchronized leaves"),
        ("notifications", "In-app alerts with unread counter badges"),
        ("audit_logs", "Immutable security audit trails & IP logging")
    ]

    for idx, (mname, mdesc) in enumerate(models_summary):
        row = idx // 2
        col = idx % 2
        x = PptInches(0.8 + col * 6.0)
        y = PptInches(1.9 + row * 1.0)

        card = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, PptInches(5.7), PptInches(0.85))
        card.fill.solid()
        card.fill.fore_color.rgb = PptRGBColor(255, 255, 255)
        card.line.color.rgb = PptRGBColor(226, 232, 240)

        tf = card.text_frame
        tf.word_wrap = True
        pt = tf.paragraphs[0]
        pt.text = mname.upper()
        pt.font.bold = True
        pt.font.size = PptPt(12)
        pt.font.color.rgb = COLOR_PRIMARY

        pd = tf.add_paragraph()
        pd.text = mdesc
        pd.font.size = PptPt(10)
        pd.font.color.rgb = PptRGBColor(100, 116, 139)

    # --- SLIDE 7: VERIFICATION & TESTING ---
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Testing & Verification Results")

    # Big Badge 100%
    badge = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(0.8), PptInches(1.9), PptInches(3.5), PptInches(5.0))
    badge.fill.solid()
    badge.fill.fore_color.rgb = PptRGBColor(240, 253, 244)
    badge.line.color.rgb = PptRGBColor(74, 222, 128)

    tf_b = badge.text_frame
    tf_b.word_wrap = True
    p1 = tf_b.paragraphs[0]
    p1.text = "100%"
    p1.font.bold = True
    p1.font.size = PptPt(44)
    p1.font.color.rgb = PptRGBColor(22, 163, 74)
    p1.alignment = PP_ALIGN.CENTER

    p2 = tf_b.add_paragraph()
    p2.text = "TEST PASS RATE"
    p2.font.bold = True
    p2.font.size = PptPt(14)
    p2.font.color.rgb = PptRGBColor(21, 128, 61)
    p2.alignment = PP_ALIGN.CENTER
    p2.space_after = PptPt(16)

    p3 = tf_b.add_paragraph()
    p3.text = "• 22 / 22 Tests Passed\n• 0 Failures\n• 0 Errors\n• 31 / 31 Requirements Verified"
    p3.font.size = PptPt(12)
    p3.font.color.rgb = PptRGBColor(20, 83, 45)
    p3.alignment = PP_ALIGN.CENTER

    # Right test suite breakdown
    c_tests = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(4.6), PptInches(1.9), PptInches(7.9), PptInches(5.0))
    c_tests.fill.solid()
    c_tests.fill.fore_color.rgb = PptRGBColor(255, 255, 255)
    c_tests.line.color.rgb = PptRGBColor(226, 232, 240)

    tf_t = c_tests.text_frame
    tf_t.word_wrap = True
    pt = tf_t.paragraphs[0]
    pt.text = "Automated Verification Breakdown"
    pt.font.bold = True
    pt.font.size = PptPt(16)
    pt.font.color.rgb = COLOR_TEXT_DARK
    pt.space_after = PptPt(10)

    checks = [
        "Flask Application Startup & Blueprint Registration",
        "Database Connection & All 10 Relational SQLAlchemy Models",
        "Authentication for Admin, Manager, and Employee Roles",
        "Role-Based Access Control (RBAC 403 Forbidden Enforcement)",
        "Live Working-Day Calculation (Weekend & Holiday Exclusion)",
        "Balance Limitation Checks & Overlapping Conflict Detection",
        "Manager Approval Workflow with Quota Deduction & Attendance Sync",
        "Manager Rejection Workflow with Mandatory Reason Capture",
        "Leave Cancellation with Automatic Quota Restoration",
        "In-App Notification Center & Read State Updates",
        "Interactive Calendar JSON Endpoints & Feed Validation",
        "Admin CRUD for Staff, Departments, Policies & Holidays",
        "Chart.js Visual Dashboards & RFC-compliant CSV Streaming Export"
    ]
    for ch in checks:
        p = tf_t.add_paragraph()
        p.text = f"✔  {ch}"
        p.font.size = PptPt(10)
        p.font.color.rgb = COLOR_TEXT_DARK
        p.space_after = PptPt(3)

    # --- SLIDE 8: DEMO & CONCLUSION (Dark Background) ---
    s8 = prs.slides.add_slide(blank_layout)
    bg8 = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg8.fill.solid()
    bg8.fill.fore_color.rgb = COLOR_BG_DARK
    bg8.line.color.rgb = COLOR_BG_DARK

    tbox8 = s8.shapes.add_textbox(PptInches(1.0), PptInches(1.5), PptInches(11.3), PptInches(4.5))
    tf8 = tbox8.text_frame
    tf8.word_wrap = True

    p_badge8 = tf8.paragraphs[0]
    p_badge8.text = "LIVE SYSTEM DEMONSTRATION"
    p_badge8.font.size = PptPt(12)
    p_badge8.font.bold = True
    p_badge8.font.color.rgb = COLOR_ACCENT
    p_badge8.space_after = PptPt(12)

    p_th = tf8.add_paragraph()
    p_th.text = "Ready for Viva / Evaluation"
    p_th.font.size = PptPt(34)
    p_th.font.bold = True
    p_th.font.color.rgb = COLOR_WHITE
    p_th.space_after = PptPt(16)

    p_demo = tf8.add_paragraph()
    p_demo.text = (
        "Application URL: http://127.0.0.1:5000\n\n"
        "• Admin: admin@example.com | Admin@123\n"
        "• Manager: manager@example.com | Manager@123\n"
        "• Employee: employee@example.com | Employee@123\n\n"
        "(Features 1-Click Quick Login for seamless role-switching during demonstration)"
    )
    p_demo.font.size = PptPt(15)
    p_demo.font.color.rgb = PptRGBColor(203, 213, 225)
    p_demo.space_after = PptPt(24)

    p_end = tf8.add_paragraph()
    p_end.text = "Thank You! • Questions & Answers"
    p_end.font.size = PptPt(18)
    p_end.font.bold = True
    p_end.font.color.rgb = PptRGBColor(96, 165, 250)

    prs.save(filename)
    print(f"Successfully generated PowerPoint presentation: {filename}")


if __name__ == "__main__":
    docx_path = os.path.join(os.path.dirname(__file__), "Employee_Leave_Management_System_Documentation.docx")
    pptx_path = os.path.join(os.path.dirname(__file__), "Employee_Leave_Management_System_Presentation.pptx")
    build_docx(docx_path)
    build_pptx(pptx_path)
    print("ALL DONE!")
