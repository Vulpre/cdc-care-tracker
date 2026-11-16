# CDC Care Tracker

A Django-based **Child Development Center (CDC) Care Tracker** for managing child records, daily attendance, health/behavioral flags, and generating Barangay-ready ECCD attendance reports.

Built with **Django 6.1** and **MariaDB/MySQL**, designed for day care teachers and child development workers.

---

## Features

### 🔐 Authentication
- **Login** — Username or email sign-in with case-insensitive matching
- **Registration** — Full sign-up flow with real-time password validation, duplicate detection, and Django's built-in password hashing (PBKDF2)
- **Password Reset** — Email-based reset flow (console backend in development)
- **Session Management** — All app pages require login; new accounts are standard users (no admin privileges)

### 👶 Child Records (Full CRUD)
- **Directory** — Searchable list of all enrolled children with flag status badges
- **Create** — Add a new child with name, date of birth, gender, and address
- **View** — Detailed profile showing personal info, recent attendance, active and resolved flags
- **Edit / Delete** — Update or remove child records with confirmation

### 📋 Daily Attendance
- **Date Picker** — Select any past or current date to record attendance (future dates blocked)
- **Previous / Next Navigation** — Quick day-by-day browsing
- **Overwrite Protection** — Warns before overwriting existing records for a date
- **Past-Date Indicator** — Clear visual notice when recording attendance for a past date
- **Status Tracking** — Mark each child as Present or Absent per day (enforced unique per child per date)

### 🚩 Flags & Alerts
- **Flag Types** — Absence streak, Underweight, Illness, Behavioral
- **Create Flags** — Attach flags to any child with optional notes
- **Resolve Flags** — In-app confirmation modal (no browser `alert()`/`confirm()`) with AJAX resolution, animated removal, and toast feedback
- **Status Badges** — Children with active flags show "Flagged" status; fully resolved children show "In Good Standing"

### 📊 Reports & Exports
- **Monthly Attendance Report** — Select month and year to view a full attendance grid
- **Print Preview** — Formatted HTML page with print controls
- **Excel Export (.xlsx)** — Styled workbook formatted for Barangay ECCD reporting, includes header, metadata, attendance grid, daily totals, legend, and signature block
- **PDF Export** — Landscape A4 report with color-coded attendance cells (P = green, A = red, — = no session), summary statistics, legend, and signature block

### 🔍 Search
- Full-text search across children's first name, last name, and address
- Results include flag status badges and quick-access links

### 👤 Profile
- **About Me** page showing developer/teacher information
- Desktop and mobile profile views

---

## Tech Stack

| Component       | Technology                  |
|-----------------|-----------------------------|
| Framework       | Django 6.1                  |
| Language        | Python 3.14                 |
| Database        | MariaDB / MySQL             |
| PDF Generation  | ReportLab                   |
| Excel Export    | OpenPyXL                    |
| Frontend        | HTML, CSS, Vanilla JS       |
| Fonts           | Fraunces (headings), IBM Plex Sans (body) |
| Auth            | Django built-in (`django.contrib.auth`) |

---

## Project Structure

```
new_project/
├── manage.py
├── README.md
├── new_project/               # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── MyNewApp/                  # Main application
│   ├── models.py              # Child, Attendance, Flag, AboutMe models
│   ├── views.py               # All view functions (login, CRUD, reports)
│   ├── forms.py               # RegistrationForm, ChildForm, FlagForm
│   ├── reports.py             # Excel & PDF report generation
│   ├── urls.py                # URL routing
│   ├── admin.py               # Admin site configuration
│   ├── tests.py               # 19 automated tests
│   └── migrations/            # Database migrations
└── templates/                 # HTML templates
    ├── index.html             # Login page
    ├── register.html          # Registration page
    ├── base.html              # Shared layout with sidebar navigation
    ├── dashboard.html         # Dashboard overview
    ├── attendance.html        # Daily attendance form with date picker
    ├── attendance-saved.html  # Attendance confirmation
    ├── attendance-monthly-preview.html  # Print-ready monthly report
    ├── child-record.html      # Child directory + create form
    ├── record-detail.html     # Child detail view with flags
    ├── edit-child.html        # Edit child form
    ├── delete-child.html      # Delete confirmation
    ├── add-flag.html          # Create a new flag
    ├── flag-saved.html        # Flag confirmation
    ├── report.html            # Reports page with export options
    ├── search.html            # Search results
    ├── profile.html           # Mobile profile view
    ├── desk-profile.html      # Desktop profile view
    ├── about-me.html          # About Me page
    ├── select-cdc.html        # Center selection page
    ├── password-reset.html    # Password reset request
    ├── password-reset-done.html
    ├── password-reset-confirm.html
    ├── password-reset-complete.html
    └── registration/
        └── password_reset_email.html
```

---

## Data Models

### Child
| Field           | Type          | Description                  |
|-----------------|---------------|------------------------------|
| `first_name`    | CharField     | Child's first name           |
| `last_name`     | CharField     | Child's last name            |
| `date_of_birth` | DateField     | Date of birth                |
| `gender`        | CharField     | Male / Female                |
| `address`       | CharField     | Home address                 |

**Properties:** `has_active_flags`, `active_flags_list`, `active_flags_count`

### Attendance
| Field       | Type        | Description                              |
|-------------|-------------|------------------------------------------|
| `child`     | ForeignKey  | Link to Child                            |
| `date`      | DateField   | Attendance date                          |
| `status`    | CharField   | `Present` or `Absent`                    |

**Constraint:** `unique_together = ('child', 'date')` — one record per child per day.

### Flag
| Field         | Type         | Description                             |
|---------------|--------------|-----------------------------------------|
| `child`       | ForeignKey   | Link to Child                           |
| `flag_type`   | CharField    | Absence streak, Underweight, Illness, Behavioral |
| `note`        | TextField    | Optional notes                          |
| `is_resolved` | BooleanField | Whether the flag has been resolved      |

---

## Prerequisites

- **Python** 3.10+
- **MariaDB** or **MySQL** (e.g., via XAMPP)
- **pip** packages: `django`, `mysqlclient`, `reportlab`, `openpyxl`

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd new_project
```

### 2. Create a Virtual Environment (recommended)

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install django mysqlclient reportlab openpyxl python-dotenv
```

### 4. Configure Environment Variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=my_django_db
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

> **Note:** The `.env` file is listed in `.gitignore` and will not be pushed to GitHub. Never commit it.

### 5. Configure the Database

Make sure MariaDB/MySQL is running (e.g., start XAMPP's MySQL service).

Create the database:

```sql
CREATE DATABASE my_django_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create a Superuser (for admin access)

```bash
python manage.py createsuperuser
```

### 7. Start the Development Server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** in your browser.

---

## Running Tests

```bash
python manage.py test MyNewApp --verbosity 2
```

The test suite includes **19 tests** covering:

| Test Area              | Tests |
|------------------------|-------|
| Dashboard              | 1     |
| Child CRUD             | 2     |
| Attendance (today)     | 1     |
| Attendance (past date) | 1     |
| Attendance (future block) | 1  |
| Monthly preview        | 1     |
| Excel export           | 1     |
| PDF export             | 1     |
| Flag create & resolve  | 1     |
| Flag AJAX resolve      | 1     |
| Registration           | 5     |
| Search                 | 1     |
| **Total**              | **19** |

---

## URL Routes

| URL                              | View                      | Description                     |
|----------------------------------|---------------------------|---------------------------------|
| `/`                              | `index`                   | Login page                      |
| `/register/`                     | `register_view`           | Create account                  |
| `/logout/`                       | `logout_view`             | Log out                         |
| `/password-reset/`               | `password_reset_request`  | Password reset                  |
| `/dashboard/`                    | `dashboard`               | Dashboard overview              |
| `/attendance/`                   | `attendance`              | Daily attendance (with date picker) |
| `/attendance-saved/`             | `attendance_saved`        | Confirmation page               |
| `/child-record/`                 | `child_record`            | Child directory + create        |
| `/child/<id>/`                   | `view_child`              | Child detail                    |
| `/child/<id>/edit/`              | `edit_child`              | Edit child                      |
| `/child/<id>/delete/`            | `delete_child`            | Delete child                    |
| `/add-flag/`                     | `add_flag`                | Create a flag                   |
| `/flag/<id>/resolve/`            | `resolve_flag`            | Resolve a flag (AJAX/redirect)  |
| `/report/`                       | `report`                  | Reports page                    |
| `/report/attendance/excel/`      | `export_attendance_excel` | Download Excel report           |
| `/report/attendance/pdf/`        | `export_attendance_pdf`   | Download PDF report             |
| `/report/attendance/preview/`    | `attendance_monthly_preview` | Print-ready HTML preview     |
| `/search/`                       | `search`                  | Search children                 |
| `/profile/`                      | `profile`                 | Mobile profile                  |
| `/desk-profile/`                 | `desk_profile`            | Desktop profile                 |
| `/about-me/`                     | `about_me`                | About Me page                   |
| `/admin/`                        | Django Admin              | Admin panel                     |

---

## Design System

The app follows a consistent design language:

- **Primary Color:** Forest Green `#1C4F40`
- **Accent Color:** Mustard `#E8A33D`
- **Background:** Warm Cream `#FAF8F3`
- **Headings Font:** [Fraunces](https://fonts.google.com/specimen/Fraunces) (serif)
- **Body Font:** [IBM Plex Sans](https://fonts.google.com/specimen/IBM+Plex+Sans) (sans-serif)
- **Cards:** Rounded corners, subtle shadows, cream backgrounds
- **Status Badges:** Green for "Good Standing", red/amber for "Flagged"

---

## Security Notes

- Passwords are hashed using Django's PBKDF2 algorithm — never stored in plain text
- All four Django password validators are enabled (similarity, minimum length, common passwords, numeric)
- New accounts are created with `is_staff=False` and `is_superuser=False`
- All app views (except login, register, and password reset) require authentication via `@login_required`
- CSRF protection is enabled on all forms
- The `SECRET_KEY` in `settings.py` is for development only — **replace it for production**

---

## Report Formats

### Excel (.xlsx)
- Styled with CDC green color palette
- Includes: header with center name, metadata block, full attendance grid (P/A/— per day), daily totals, legend, and signature block
- Color-coded cells: green for Present, red for Absent

### PDF
- Landscape A4 layout
- Same data as Excel: attendance grid, daily totals, statistics, legend, and signature block
- Formatted for direct printing and Barangay submission

### Attendance Legend
| Code | Meaning                                  |
|------|------------------------------------------|
| **P** | Present                                 |
| **A** | Absent                                  |
| **—** | No Session Recorded / Weekend / Holiday |

---

## Development Notes

- Email backend is set to **console** (`django.core.mail.backends.console.EmailBackend`) — password reset emails print to the terminal
- `DEBUG = True` — set to `False` for production
- `ALLOWED_HOSTS` includes `127.0.0.1`, `localhost`, and `testserver`
- The `select-cdc.html` page is a static placeholder with no backend center-selection logic

---

## License

This project was developed as a course requirement for **BS Information Technology — 3rd Year, Section IT3A**.
