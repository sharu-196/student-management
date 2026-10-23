# Student Management System

A complete web application built with **Python (Flask)**, **SQLite** and **Bootstrap 5**.
Admins can manage students, subjects and marks, and the system automatically calculates
totals, percentages, grades, pass/fail and class ranks.

## Features

| Module | What it does |
|---|---|
| Login / Logout | Secure admin login (passwords are hashed), change-password page |
| Dashboard | Student count, average score, pass rate, class topper, department chart, grade chart, top 5 |
| Students | Add, view, edit, delete, search by name / roll number, filter by department |
| Subjects | Add and delete subjects with their maximum marks |
| Marks | Enter or update marks per student and subject (validated against maximum marks) |
| Report card | Per-student marks, percentage, grade, rank (printable) |
| Rank list | Sorted by percentage, ties share a rank, filter by department, export to CSV, print |

**Grading rules:** A+ (90+), A (80+), B (70+), C (60+), D (50+), E (35+), F (fail).
A student fails if any subject is below 35%.

## Technologies

- **Frontend:** HTML, CSS, Bootstrap 5, JavaScript, Chart.js (loaded from a CDN, so the browser needs internet)
- **Backend:** Python 3 + Flask
- **Database:** SQLite (a single file, `students.db`, created automatically)

## How to run

1. Install Python 3.9 or newer.
2. Open a terminal in this folder and install Flask:
   ```
   pip install -r requirements.txt
   ```
3. (Optional) Add demo data: 12 students, 5 subjects and marks:
   ```
   python seed_demo.py
   ```
4. Start the website:
   ```
   python app.py
   ```
5. Open **http://127.0.0.1:5000** in your browser.

**Default login:** username `admin`, password `admin123`. Change it from the *Account* page after logging in.

## Folder structure

```
student_management/
├── app.py              # Flask backend: routes, validation, grade and rank logic
├── schema.sql          # Database tables
├── seed_demo.py        # Optional demo data
├── test_app.py         # Automated tests (python -m unittest -v)
├── requirements.txt
├── static/
│   └── style.css       # Custom styling
└── templates/          # HTML pages (Jinja2)
    ├── base.html       # Common layout and navbar
    ├── login.html
    ├── dashboard.html
    ├── students.html
    ├── student_form.html    # Used for both Add and Edit
    ├── student_detail.html  # Profile and report card
    ├── subjects.html
    ├── marks_form.html
    ├── ranklist.html
    ├── account.html
    └── error.html
```

## Database design (ER diagram)

```
 ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
 │   students   │ 1        * │    marks     │ *        1 │   subjects   │
 ├──────────────┤────────────├──────────────┤────────────├──────────────┤
 │ id (PK)      │            │ id (PK)      │            │ id (PK)      │
 │ roll_no (UQ) │            │ student_id FK│            │ code (UQ)    │
 │ name         │            │ subject_id FK│            │ name         │
 │ department   │            │ marks        │            │ max_marks    │
 │ year         │            │ UNIQUE(student_id, subject_id)           │
 │ email, phone │            └──────────────┘            └──────────────┘
 │ created_at   │
 └──────────────┘            ┌──────────────┐
                             │    users     │   (admin login, separate table)
                             ├──────────────┤
                             │ id (PK)      │
                             │ username (UQ)│
                             │ password_hash│
                             └──────────────┘
```

One student has many marks (one per subject). One subject appears in many students' marks.
Deleting a student or subject also deletes the related marks (`ON DELETE CASCADE`).

## Security built in

- Passwords stored as hashes, never as plain text
- CSRF token on every form
- SQL queries use parameters, which prevents SQL injection
- Jinja2 escapes output automatically, which prevents XSS
- CSV export guards against spreadsheet formula injection

## Run the tests

```
python -m unittest -v
```

## Ideas to extend

- Attendance module (new `attendance` table)
- Multiple semesters or exams (add an `exam` column to `marks`)
- Student login to view their own marks
- Switch SQLite to MySQL (change the connection code in `app.py`)

## Before putting it online

Set a long random secret key and turn off debug mode:

```
set SECRET_KEY=your-long-random-text        (Windows)
export SECRET_KEY=your-long-random-text     (Mac / Linux)
```

and change `app.run(debug=True)` to `app.run(debug=False)` at the bottom of `app.py`.
