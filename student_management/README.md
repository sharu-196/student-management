# 🎓 Student Management System

A web-based application developed using **Python, Flask, SQLite, and Bootstrap 5** to simplify student record management and academic performance tracking.

## 📌 Objective

To develop a user-friendly web application that helps administrators manage student details, subjects, and marks efficiently. The system automatically calculates total marks, percentages, grades, pass/fail status, and class ranks, reducing manual calculations and improving accuracy.

## 🛠 Tools & Technologies Used

- **Programming Language:** Python
- **Backend Framework:** Flask
- **Frontend:** HTML, CSS, Bootstrap 5, JavaScript
- **Database:** SQLite
- **Data Visualization:** Chart.js
- **Development Environment:** Visual Studio Code
- **Testing:** Python unittest

## 📂 Project Contents

- 📄 `app.py` – Main Flask application with backend logic and routes
- 🗃️ `schema.sql` – Database table definitions
- 📊 `seed_demo.py` – Script to generate sample student data
- 🧪 `test_app.py` – Automated test cases
- 📋 `requirements.txt` – Required Python packages
- 🎨 `static/style.css` – Custom styling
- 📁 `templates/` – HTML templates for login, dashboard, students, subjects, marks, and reports

## ✨ Key Features

- **Admin Authentication:** Login, logout, and password management
- **Dashboard:** Overview of student count, average scores, pass rate, and top performers
- **Student Management:** Add, view, edit, delete, search, and filter student records
- **Subject Management:** Create and manage subjects with maximum marks
- **Marks Management:** Enter and update student marks with validation
- **Automatic Grade Calculation:** Calculate grades and pass/fail status
- **Report Cards:** View individual student marks, percentages, grades, and ranks
- **Rank List:** Generate class rankings with department filters
- **CSV Export:** Export rank lists for further analysis
- **Responsive Interface:** User-friendly design using Bootstrap 5

## 📈 Key Outcomes

- Simplifies student record management
- Reduces manual calculations and human errors
- Provides faster access to academic performance details
- Generates report cards and rank lists automatically
- Improves the organization of student and subject information

## 🗄️ Database Design

The application uses SQLite with four main tables:

- `students` – Stores student information
- `subjects` – Stores subject details and maximum marks
- `marks` – Stores student marks for each subject
- `users` – Stores administrator login details securely

The database uses primary keys, foreign keys, and constraints to maintain data consistency.

## ▶️ How to Run the Project

1. Install Python 3.9 or newer.
2. Clone or download this repository.
3. Open the project folder in a terminal.
4. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. (Optional) Add sample data:

   ```bash
   python seed_demo.py
   ```

6. Start the application:

   ```bash
   python app.py
   ```

7. Open the following URL in your browser:

   `http://127.0.0.1:5000`

**Note:** If demo data is added, use the default credentials configured by the project. Change the default password before using the application beyond local testing.

## 🔐 Security Features

- Password hashing for administrator credentials
- CSRF protection for forms
- Parameterized SQL queries to reduce SQL injection risks
- Automatic HTML escaping to help prevent cross-site scripting
- CSV export protection against spreadsheet formula injection

## 🚀 Future Enhancements

- Student login and personal academic dashboard
- Attendance management
- Multiple semesters and examination records
- PDF report card generation
- Email notifications for academic updates
- Deployment to a cloud hosting platform

## 👩‍💻 Author

**Sharu Latha**

🎓 Computer Science Graduate

💻 Interests: Python Development | Web Development | AI & Machine Learning

🔗 [GitHub](https://github.com/sharu-196)  
🔗 [LinkedIn](https://www.linkedin.com/in/sharu-latha19/)

---

*This project was developed for learning and portfolio purposes to demonstrate skills in Python, Flask, database management, and web application development.*
