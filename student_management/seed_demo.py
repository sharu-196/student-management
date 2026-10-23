"""Fill the database with demo students, subjects and marks.

Run once:  python seed_demo.py
(It does nothing if students already exist, so it never overwrites real data.)
"""
import random
import sqlite3

from app import DATABASE, init_db

SUBJECTS = [
    ("PY101", "Python Programming", 100),
    ("DB102", "Database Management", 100),
    ("WT103", "Web Technology", 100),
    ("MA104", "Discrete Mathematics", 100),
    ("EN105", "Communication English", 100),
]

STUDENTS = [
    ("CS2301", "Arun Kumar", "B.Sc Computer Science", 3),
    ("CS2302", "Divya Bharathi", "B.Sc Computer Science", 3),
    ("CS2303", "Karthik Raja", "B.Sc Computer Science", 3),
    ("CS2304", "Meenakshi Sundaram", "B.Sc Computer Science", 3),
    ("CS2305", "Priya Dharshini", "B.Sc Computer Science", 3),
    ("CS2306", "Suresh Balaji", "B.Sc Computer Science", 3),
    ("CA2301", "Lakshmi Narayanan", "BCA", 2),
    ("CA2302", "Naveen Prasath", "BCA", 2),
    ("CA2303", "Revathi Selvam", "BCA", 2),
    ("CA2304", "Vignesh Mohan", "BCA", 2),
    ("BC2301", "Anitha Rajan", "B.Com", 1),
    ("BC2302", "Ganesh Murugan", "B.Com", 1),
]


def main():
    init_db()
    db = sqlite3.connect(DATABASE)
    if db.execute("SELECT 1 FROM students LIMIT 1").fetchone():
        print("Students already exist - demo data not added.")
        db.close()
        return

    rng = random.Random(2026)  # same demo data every time
    db.executemany("INSERT OR IGNORE INTO subjects (code, name, max_marks) "
                   "VALUES (?, ?, ?)", SUBJECTS)
    for roll, name, dept, year in STUDENTS:
        email = name.split()[0].lower() + "@example.com"
        phone = "9" + "".join(str(rng.randint(0, 9)) for _ in range(9))
        db.execute("INSERT INTO students (roll_no, name, department, year, "
                   "email, phone) VALUES (?, ?, ?, ?, ?, ?)",
                   (roll, name, dept, year, email, phone))
    db.commit()

    student_ids = [r[0] for r in db.execute("SELECT id FROM students")]
    subject_ids = [r[0] for r in db.execute("SELECT id FROM subjects")]
    for sid in student_ids:
        ability = rng.randint(45, 92)
        for subid in subject_ids:
            mark = max(0, min(100, ability + rng.randint(-15, 12)))
            db.execute("INSERT INTO marks (student_id, subject_id, marks) "
                       "VALUES (?, ?, ?)", (sid, subid, mark))
    db.commit()
    db.close()
    print(f"Added {len(STUDENTS)} students, {len(SUBJECTS)} subjects and marks.")


if __name__ == "__main__":
    main()
