-- Student Management System : database schema (SQLite)

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no    TEXT    NOT NULL UNIQUE,
    name       TEXT    NOT NULL,
    department TEXT    NOT NULL,
    year       INTEGER NOT NULL CHECK (year BETWEEN 1 AND 5),
    email      TEXT,
    phone      TEXT,
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subjects (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    code      TEXT    NOT NULL UNIQUE,
    name      TEXT    NOT NULL,
    max_marks INTEGER NOT NULL DEFAULT 100 CHECK (max_marks > 0)
);

CREATE TABLE IF NOT EXISTS marks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students (id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects (id) ON DELETE CASCADE,
    marks      INTEGER NOT NULL CHECK (marks >= 0),
    UNIQUE (student_id, subject_id)
);
