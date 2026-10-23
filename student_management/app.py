"""Student Management System - Flask + SQLite + Bootstrap.

Run:  python app.py      then open http://127.0.0.1:5000
Default login:  admin / admin123   (change it from the Account page)
"""
import csv
import io
import os
import re
import secrets
import sqlite3
from functools import wraps

from flask import (Flask, Response, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("STUDENT_DB", os.path.join(BASE_DIR, "students.db"))
PASS_PERCENT = 35  # minimum % needed in EVERY subject to pass
GRADES = ["A+", "A", "B", "C", "D", "E", "F"]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "change-this-secret-key-before-deploying")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and the default admin user (only if missing)."""
    db = sqlite3.connect(DATABASE)
    with open(os.path.join(BASE_DIR, "schema.sql"), encoding="utf-8") as f:
        db.executescript(f.read())
    if not db.execute("SELECT 1 FROM users LIMIT 1").fetchone():
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                   ("admin", generate_password_hash("admin123")))
    db.commit()
    db.close()


# --------------------------------------------------------------------------
# Security: login check + CSRF protection
# --------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get("_csrf")
        if not token or not secrets.compare_digest(
                token, request.form.get("_csrf", "")):
            abort(400, "Your session expired. Please go back and try again.")


@app.errorhandler(400)
@app.errorhandler(404)
def show_error(err):
    return render_template("error.html", error=err), err.code


# --------------------------------------------------------------------------
# Grade / result / rank logic
# --------------------------------------------------------------------------
def grade_for(percentage, passed=True):
    if not passed:
        return "F"
    for limit, grade in ((90, "A+"), (80, "A"), (70, "B"), (60, "C"),
                         (50, "D")):
        if percentage >= limit:
            return grade
    return "E"


def build_results(db):
    """Total, percentage, grade, pass/fail and rank for every student
    who has at least one mark. Returned best-first."""
    rows = db.execute("""
        SELECT s.id, s.roll_no, s.name, s.department, s.year,
               COUNT(m.id)                       AS subject_count,
               SUM(m.marks)                      AS total,
               SUM(sub.max_marks)                AS max_total,
               MIN(m.marks * 100.0 / sub.max_marks) AS lowest_pct
        FROM students s
        JOIN marks    m   ON m.student_id = s.id
        JOIN subjects sub ON sub.id = m.subject_id
        GROUP BY s.id
    """).fetchall()

    results = []
    for r in rows:
        pct = round(r["total"] * 100.0 / r["max_total"], 2)
        passed = r["lowest_pct"] >= PASS_PERCENT
        results.append({
            "id": r["id"], "roll_no": r["roll_no"], "name": r["name"],
            "department": r["department"], "year": r["year"],
            "subject_count": r["subject_count"], "total": r["total"],
            "max_total": r["max_total"], "percentage": pct,
            "grade": grade_for(pct, passed),
            "result": "Pass" if passed else "Fail",
        })

    results.sort(key=lambda x: (-x["percentage"], x["name"].lower()))
    rank, previous = 0, None
    for position, item in enumerate(results, start=1):
        if item["percentage"] != previous:  # same percentage = same rank
            rank, previous = position, item["percentage"]
        item["rank"] = rank
    return results


# --------------------------------------------------------------------------
# Auth routes
# --------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = ?",
                          (session["user_id"],)).fetchone()
        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        if not check_password_hash(user["password_hash"], current):
            flash("Current password is wrong.", "danger")
        elif len(new) < 6:
            flash("New password must be at least 6 characters.", "danger")
        elif new != confirm:
            flash("New password and confirmation do not match.", "danger")
        else:
            db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                       (generate_password_hash(new), user["id"]))
            db.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for("account"))
    return render_template("account.html")


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
@app.route("/")
@login_required
def dashboard():
    db = get_db()
    results = build_results(db)
    total_students = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_subjects = db.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]

    passed = sum(1 for r in results if r["result"] == "Pass")
    average = (round(sum(r["percentage"] for r in results) / len(results), 1)
               if results else 0)
    pass_rate = round(passed * 100 / len(results), 1) if results else 0

    dept_rows = db.execute(
        "SELECT department, COUNT(*) AS c FROM students "
        "GROUP BY department ORDER BY department").fetchall()
    grade_counts = {grade: 0 for grade in GRADES}
    for r in results:
        grade_counts[r["grade"]] += 1

    return render_template(
        "dashboard.html", total_students=total_students,
        total_subjects=total_subjects, average=average, pass_rate=pass_rate,
        topper=results[0] if results else None, top5=results[:5],
        dept_labels=[r["department"] for r in dept_rows],
        dept_values=[r["c"] for r in dept_rows],
        grade_labels=GRADES, grade_values=[grade_counts[x] for x in GRADES])


# --------------------------------------------------------------------------
# Students (CRUD)
# --------------------------------------------------------------------------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\d{10}$")


def validate_student(form, student_id=None):
    db = get_db()
    data = {k: form.get(k, "").strip()
            for k in ("roll_no", "name", "department", "year", "email",
                      "phone")}
    errors = []
    if not data["roll_no"]:
        errors.append("Roll number is required.")
    if not data["name"]:
        errors.append("Name is required.")
    if not data["department"]:
        errors.append("Department is required.")
    if not data["year"].isdigit() or not 1 <= int(data["year"]) <= 5:
        errors.append("Year must be a number from 1 to 5.")
    if data["email"] and not EMAIL_RE.match(data["email"]):
        errors.append("Email address is not valid.")
    if data["phone"] and not PHONE_RE.match(data["phone"]):
        errors.append("Phone number must be exactly 10 digits.")
    if data["roll_no"]:
        if student_id is None:
            clash = db.execute("SELECT id FROM students WHERE roll_no = ?",
                               (data["roll_no"],)).fetchone()
        else:
            clash = db.execute(
                "SELECT id FROM students WHERE roll_no = ? AND id != ?",
                (data["roll_no"], student_id)).fetchone()
        if clash:
            errors.append("That roll number already exists.")
    return data, errors


def department_choices(db):
    return [r[0] for r in db.execute(
        "SELECT DISTINCT department FROM students ORDER BY department")]


@app.route("/students")
@login_required
def students():
    db = get_db()
    q = request.args.get("q", "").strip()
    dept = request.args.get("department", "").strip()
    sql, params = "SELECT * FROM students WHERE 1=1", []
    if q:
        sql += " AND (name LIKE ? OR roll_no LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if dept:
        sql += " AND department = ?"
        params.append(dept)
    sql += " ORDER BY roll_no"
    return render_template("students.html",
                           students=db.execute(sql, params).fetchall(),
                           departments=department_choices(db), q=q, dept=dept)


@app.route("/students/add", methods=["GET", "POST"])
@login_required
def add_student():
    db = get_db()
    data, errors = {"year": "1"}, []
    if request.method == "POST":
        data, errors = validate_student(request.form)
        if not errors:
            db.execute(
                "INSERT INTO students (roll_no, name, department, year, "
                "email, phone) VALUES (?, ?, ?, ?, ?, ?)",
                (data["roll_no"], data["name"], data["department"],
                 int(data["year"]), data["email"], data["phone"]))
            db.commit()
            flash(f"Student {data['name']} added.", "success")
            return redirect(url_for("students"))
    return render_template("student_form.html", student=data, errors=errors,
                           editing=False, departments=department_choices(db))


@app.route("/students/<int:student_id>")
@login_required
def student_detail(student_id):
    db = get_db()
    student = db.execute("SELECT * FROM students WHERE id = ?",
                         (student_id,)).fetchone()
    if student is None:
        abort(404)
    rows = []
    for m in db.execute("""
            SELECT m.id, m.marks, sub.code, sub.name, sub.max_marks
            FROM marks m JOIN subjects sub ON sub.id = m.subject_id
            WHERE m.student_id = ? ORDER BY sub.code""", (student_id,)):
        pct = m["marks"] * 100.0 / m["max_marks"]
        rows.append({**dict(m), "pct": round(pct, 1),
                     "grade": grade_for(pct, pct >= PASS_PERCENT)})
    summary = next((r for r in build_results(db) if r["id"] == student_id),
                   None)
    return render_template("student_detail.html", student=student, marks=rows,
                           summary=summary)


@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    db = get_db()
    student = db.execute("SELECT * FROM students WHERE id = ?",
                         (student_id,)).fetchone()
    if student is None:
        abort(404)
    data, errors = dict(student), []
    if request.method == "POST":
        data, errors = validate_student(request.form, student_id)
        if not errors:
            db.execute(
                "UPDATE students SET roll_no=?, name=?, department=?, "
                "year=?, email=?, phone=? WHERE id=?",
                (data["roll_no"], data["name"], data["department"],
                 int(data["year"]), data["email"], data["phone"],
                 student_id))
            db.commit()
            flash("Student details updated.", "success")
            return redirect(url_for("student_detail", student_id=student_id))
    return render_template("student_form.html", student=data, errors=errors,
                           editing=True, student_id=student_id,
                           departments=department_choices(db))


@app.route("/students/<int:student_id>/delete", methods=["POST"])
@login_required
def delete_student(student_id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    flash("Student deleted.", "info")
    return redirect(url_for("students"))


# --------------------------------------------------------------------------
# Subjects
# --------------------------------------------------------------------------
@app.route("/subjects", methods=["GET", "POST"])
@login_required
def subjects():
    db = get_db()
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        name = request.form.get("name", "").strip()
        max_raw = request.form.get("max_marks", "100").strip()
        if not code or not name:
            flash("Subject code and name are required.", "danger")
        elif not max_raw.isdigit() or not 1 <= int(max_raw) <= 1000:
            flash("Maximum marks must be a number from 1 to 1000.", "danger")
        elif db.execute("SELECT 1 FROM subjects WHERE code = ?",
                        (code,)).fetchone():
            flash("That subject code already exists.", "danger")
        else:
            db.execute("INSERT INTO subjects (code, name, max_marks) "
                       "VALUES (?, ?, ?)", (code, name, int(max_raw)))
            db.commit()
            flash(f"Subject {name} added.", "success")
            return redirect(url_for("subjects"))
    rows = db.execute("SELECT * FROM subjects ORDER BY code").fetchall()
    return render_template("subjects.html", subjects=rows)


@app.route("/subjects/<int:subject_id>/delete", methods=["POST"])
@login_required
def delete_subject(subject_id):
    db = get_db()
    db.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    db.commit()
    flash("Subject (and its marks) deleted.", "info")
    return redirect(url_for("subjects"))


# --------------------------------------------------------------------------
# Marks
# --------------------------------------------------------------------------
@app.route("/marks/add", methods=["GET", "POST"])
@login_required
def add_marks():
    db = get_db()
    student_id = request.values.get("student_id", type=int)
    if request.method == "POST":
        subject_id = request.form.get("subject_id", type=int)
        raw = request.form.get("marks", "").strip()
        student = db.execute("SELECT id FROM students WHERE id = ?",
                             (student_id,)).fetchone() if student_id else None
        subject = db.execute("SELECT * FROM subjects WHERE id = ?",
                             (subject_id,)).fetchone() if subject_id else None
        error = None
        if student is None:
            error = "Please choose a student."
        elif subject is None:
            error = "Please choose a subject."
        elif not raw.isdigit():
            error = "Marks must be a whole number (0 or more)."
        elif int(raw) > subject["max_marks"]:
            error = f"Marks cannot be more than {subject['max_marks']}."
        if error:
            flash(error, "danger")
        else:
            db.execute(
                "INSERT INTO marks (student_id, subject_id, marks) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT (student_id, subject_id) "
                "DO UPDATE SET marks = excluded.marks",
                (student_id, subject_id, int(raw)))
            db.commit()
            flash("Marks saved.", "success")
            return redirect(url_for("student_detail", student_id=student_id))
    return render_template(
        "marks_form.html", selected=student_id,
        students=db.execute("SELECT id, roll_no, name FROM students "
                            "ORDER BY roll_no").fetchall(),
        subjects=db.execute("SELECT * FROM subjects ORDER BY code").fetchall())


@app.route("/marks/<int:mark_id>/delete", methods=["POST"])
@login_required
def delete_marks(mark_id):
    db = get_db()
    row = db.execute("SELECT student_id FROM marks WHERE id = ?",
                     (mark_id,)).fetchone()
    if row is None:
        abort(404)
    db.execute("DELETE FROM marks WHERE id = ?", (mark_id,))
    db.commit()
    flash("Marks entry removed.", "info")
    return redirect(url_for("student_detail", student_id=row["student_id"]))


# --------------------------------------------------------------------------
# Rank list (+ CSV export)
# --------------------------------------------------------------------------
def filtered_results(db, dept):
    results = build_results(db)
    if dept:
        results = [r for r in results if r["department"] == dept]
    return results


@app.route("/ranklist")
@login_required
def ranklist():
    db = get_db()
    dept = request.args.get("department", "").strip()
    return render_template("ranklist.html",
                           results=filtered_results(db, dept), dept=dept,
                           departments=department_choices(db))


def csv_safe(value):
    """Stop spreadsheet apps from running text that starts with = + - @."""
    text = str(value)
    return "'" + text if text and text[0] in "=+-@" else text


@app.route("/ranklist/export")
@login_required
def export_ranklist():
    dept = request.args.get("department", "").strip()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Rank", "Roll No", "Name", "Department", "Year",
                     "Total", "Out of", "Percentage", "Grade", "Result"])
    for r in filtered_results(get_db(), dept):
        writer.writerow([r["rank"], csv_safe(r["roll_no"]),
                         csv_safe(r["name"]), csv_safe(r["department"]),
                         r["year"], r["total"], r["max_total"],
                         r["percentage"], r["grade"], r["result"]])
    return Response(
        buffer.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=ranklist.csv"})


init_db()

if __name__ == "__main__":
    app.run(debug=True)  # set debug=False before putting it online
