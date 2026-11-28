# 🏥 CDC Care Tracker

A Django web application for managing Child Development Center (CDC) records — tracking children, attendance, health flags, and generating reports.

> Built for **IT3A** | BS Information Technology — 3rd Year

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Authentication** | Login, registration, logout, and password reset via email |
| 👶 **Child Records** | Full CRUD — add, view, edit, and delete child profiles |
| 📋 **Attendance Tracking** | Record daily attendance (Present/Absent) per child with date navigation |
| 🚩 **Health Flags** | Flag children for absence streaks, underweight, illness, or behavioral concerns |
| 🔍 **Search** | Search children by name, barangay, or address |
| 📊 **Reports** | Monthly attendance reports with Excel (.xlsx) and PDF export |
| 🖨️ **Print View** | Print-ready monthly attendance sheet |

---

## 🗂️ Project Structure

```
DJangoIT3A/
├── manage.py
├── requirements.txt
├── .gitignore
├── MyNewApp/               # Main Django app
│   ├── models.py           # Child, Attendance, Flag, AboutMe models
│   ├── views.py            # All view logic
│   ├── urls.py             # URL routing
│   ├── forms.py            # ChildForm, RegistrationForm
│   ├── reports.py          # Excel & PDF report generation
│   ├── admin.py
│   └── migrations/
├── new_project/            # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py / asgi.py
└── templates/              # HTML templates
    ├── base.html
    ├── dashboard.html
    ├── attendance.html
    ├── child-record.html
    ├── report.html
    └── ...
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### 1. Clone the repository
```bash
git clone https://github.com/Vulpre/cdc-care-tracker.git
cd cdc-care-tracker
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Windows (PowerShell)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Copy the example env file and fill in your values:
```bash
cp new_project/.env.example new_project/.env
```

### 5. Apply migrations
```bash
python manage.py migrate
```

### 6. Create a superuser (admin)
```bash
python manage.py createsuperuser
```

### 7. Run the development server
```bash
python manage.py runserver
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `Django` | Web framework |
| `openpyxl` | Excel report export |
| `reportlab` | PDF report export |
| `python-dotenv` | Environment variable management |
| `PyMySQL` | MySQL database connector |
| `Pillow` | Image handling |
| `asgiref` | ASGI support |
| `tzdata` | Timezone data |

---

## 📄 License

This project is for academic purposes — IT3A, BS Information Technology.
