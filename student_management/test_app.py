"""Automated tests.  Run:  python -m unittest -v"""
import os
import tempfile
import unittest

_tmp = tempfile.mkdtemp()
os.environ["STUDENT_DB"] = os.path.join(_tmp, "test.db")

import app as sms  # noqa: E402  (must come after STUDENT_DB is set)


class StudentAppTests(unittest.TestCase):
    def setUp(self):
        if os.path.exists(sms.DATABASE):
            os.remove(sms.DATABASE)
        sms.init_db()
        self.client = sms.app.test_client()

    # -- helpers ---------------------------------------------------------
    def token(self):
        self.client.get("/login")
        with self.client.session_transaction() as s:
            return s["_csrf"]

    def post(self, url, data=None, follow=True):
        data = dict(data or {})
        data["_csrf"] = self.token_value
        return self.client.post(url, data=data, follow_redirects=follow)

    def login(self, password="admin123"):
        self.token_value = self.token()
        return self.post("/login", {"username": "admin", "password": password})

    def refresh_token(self):
        with self.client.session_transaction() as s:
            self.token_value = s.get("_csrf") or self.token()
        self.client.get("/")  # make sure a token exists in the session
        with self.client.session_transaction() as s:
            self.token_value = s["_csrf"]

    def seed(self):
        self.login()
        self.refresh_token()
        self.post("/subjects", {"code": "py101", "name": "Python", "max_marks": "100"})
        self.post("/subjects", {"code": "db102", "name": "Database", "max_marks": "100"})
        for roll, name in (("R1", "Asha"), ("R2", "Bala"), ("R3", "Chitra")):
            self.post("/students/add", {"roll_no": roll, "name": name,
                                        "department": "BCA", "year": "2"})

    # -- tests -----------------------------------------------------------
    def test_pages_need_login(self):
        for url in ("/", "/students", "/subjects", "/ranklist", "/marks/add"):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 302, url)
            self.assertIn("/login", r.headers["Location"])

    def test_login_wrong_and_right_password(self):
        self.assertIn(b"Invalid username or password", self.login("nope").data)
        self.assertIn(b"Welcome back", self.login().data)

    def test_post_without_csrf_is_rejected(self):
        self.login()
        r = self.client.post("/students/add", data={"roll_no": "X", "name": "Y"})
        self.assertEqual(r.status_code, 400)

    def test_student_crud_and_validation(self):
        self.login()
        self.refresh_token()
        r = self.post("/students/add", {"roll_no": "", "name": "", "department": "", "year": "9"})
        self.assertIn(b"Roll number is required", r.data)
        self.assertIn(b"Year must be", r.data)

        r = self.post("/students/add", {"roll_no": "S1", "name": "Meena", "department": "BCA",
                                        "year": "2", "email": "m@x.com", "phone": "9876543210"})
        self.assertIn(b"Meena", r.data)
        r = self.post("/students/add", {"roll_no": "S1", "name": "Dup", "department": "BCA", "year": "1"})
        self.assertIn(b"roll number already exists", r.data)
        r = self.post("/students/add", {"roll_no": "S2", "name": "Bad", "department": "BCA",
                                        "year": "1", "phone": "123"})
        self.assertIn(b"exactly 10 digits", r.data)

        r = self.post("/students/1/edit", {"roll_no": "S1", "name": "Meenakshi", "department": "BCA", "year": "3"})
        self.assertIn(b"Meenakshi", r.data)
        r = self.client.get("/students?q=meenak")
        self.assertIn(b"Meenakshi", r.data)
        self.post("/students/1/delete")
        self.assertNotIn(b"Meenakshi", self.client.get("/students").data)

    def test_marks_ranking_grades_and_ties(self):
        self.seed()
        # Asha 95+85=180 (90%), Bala 60+60=120 (60%), Chitra 90+90 -> tie? make Chitra equal to Asha
        for sid, (m1, m2) in {1: (95, 85), 2: (60, 60), 3: (85, 95)}.items():
            self.post("/marks/add", {"student_id": sid, "subject_id": 1, "marks": m1})
            self.post("/marks/add", {"student_id": sid, "subject_id": 2, "marks": m2})
        results = sms.build_results(self._db())
        by_name = {r["name"]: r for r in results}
        self.assertEqual(by_name["Asha"]["percentage"], 90.0)
        self.assertEqual(by_name["Asha"]["grade"], "A+")
        self.assertEqual(by_name["Asha"]["rank"], 1)
        self.assertEqual(by_name["Chitra"]["rank"], 1)   # tie shares rank 1
        self.assertEqual(by_name["Bala"]["rank"], 3)     # next rank skips to 3
        self.assertEqual(by_name["Bala"]["grade"], "C")

    def test_fail_when_one_subject_below_35(self):
        self.seed()
        self.post("/marks/add", {"student_id": 1, "subject_id": 1, "marks": 100})
        self.post("/marks/add", {"student_id": 1, "subject_id": 2, "marks": 30})
        r = sms.build_results(self._db())[0]
        self.assertEqual((r["result"], r["grade"]), ("Fail", "F"))
        self.assertEqual(r["percentage"], 65.0)

    def test_marks_validation_and_update(self):
        self.seed()
        r = self.post("/marks/add", {"student_id": 1, "subject_id": 1, "marks": 150})
        self.assertIn(b"cannot be more than 100", r.data)
        r = self.post("/marks/add", {"student_id": 1, "subject_id": 1, "marks": "-5"})
        self.assertIn(b"whole number", r.data)
        self.post("/marks/add", {"student_id": 1, "subject_id": 1, "marks": 50})
        self.post("/marks/add", {"student_id": 1, "subject_id": 1, "marks": 70})  # update
        rows = self._db().execute("SELECT marks FROM marks WHERE student_id=1").fetchall()
        self.assertEqual([r["marks"] for r in rows], [70])

    def test_deleting_student_removes_marks(self):
        self.seed()
        self.post("/marks/add", {"student_id": 1, "subject_id": 1, "marks": 80})
        self.post("/students/1/delete")
        count = self._db().execute("SELECT COUNT(*) FROM marks").fetchone()[0]
        self.assertEqual(count, 0)

    def test_pages_render_and_csv_export(self):
        self.seed()
        self.post("/marks/add", {"student_id": 1, "subject_id": 1, "marks": 88})
        for url in ("/", "/students", "/students/1", "/students/1/edit", "/students/add",
                    "/subjects", "/marks/add", "/ranklist", "/account"):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertEqual(self.client.get("/students/999").status_code, 404)
        r = self.client.get("/ranklist/export")
        self.assertEqual(r.mimetype, "text/csv")
        self.assertIn(b"Rank,Roll No,Name", r.data)
        self.assertIn(b"Asha", r.data)

    def test_csv_injection_guard(self):
        self.assertEqual(sms.csv_safe("=SUM(A1)"), "'=SUM(A1)")
        self.assertEqual(sms.csv_safe("Arun"), "Arun")

    def test_change_password(self):
        self.login()
        self.refresh_token()
        r = self.post("/account", {"current_password": "wrong", "new_password": "abcdef",
                                   "confirm_password": "abcdef"})
        self.assertIn(b"Current password is wrong", r.data)
        r = self.post("/account", {"current_password": "admin123", "new_password": "abcdef",
                                   "confirm_password": "abcdef"})
        self.assertIn(b"Password changed", r.data)
        self.post("/logout")
        self.assertIn(b"Welcome back", self.login("abcdef").data)

    def _db(self):
        import sqlite3
        db = sqlite3.connect(sms.DATABASE)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        self.addCleanup(db.close)  # close it when the test finishes
        return db


if __name__ == "__main__":
    unittest.main()
