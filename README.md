# 🎓 College Student Result Management System (CRMS)

A complete web-based academic result management system built with **Python Flask** and **SQLite**.

---

## 📋 Features

### Modules
| Module | Description |
|--------|-------------|
| **Admin** | Manage students, faculty, subjects, exam schedules; publish results |
| **Faculty** | Enter/update marks; generate grade sheets |
| **Student** | View published results; download CSV report |
| **Result Processing** | Auto grade calculation (O/A+/A/B+/B/C/F) + CGPA |
| **Authentication** | Secure login with role-based access control |

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the application
```bash
python app.py
```

### 3. Open browser
```
http://localhost:5000
```

---

## 🔐 Default Login Credentials

| Role    | Username  | Password     |
|---------|-----------|--------------|
| Admin   | admin     | admin123     |
| Faculty | faculty1  | faculty123   |
| Student | student1  | student123   |

---

## 📁 Project Structure

```
college_result_system/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── README.md
├── instance/
│   └── college_result.db     # SQLite database (auto-created)
└── templates/
    ├── base.html             # Base layout with sidebar
    ├── login.html            # Login page
    ├── admin/
    │   ├── dashboard.html
    │   ├── students.html
    │   ├── add_student.html
    │   ├── faculty.html
    │   ├── add_faculty.html
    │   ├── subjects.html
    │   ├── add_subject.html
    │   ├── exams.html
    │   ├── add_exam.html
    │   └── reports.html
    ├── faculty/
    │   ├── dashboard.html
    │   ├── enter_marks.html
    │   └── grade_sheet.html
    └── student/
        ├── dashboard.html
        └── results.html
```

---

## 🏗️ Database Models

- **User** — Authentication (admin/faculty/student)
- **Student** — Roll number, department, semester, batch
- **Faculty** — Employee ID, department, designation
- **Subject** — Code, name, credits, assigned faculty
- **Exam** — Name, type, max marks, publish status
- **Result** — Marks, auto-calculated grade & grade points

---

## 📊 Grading System (10-Point Scale)

| Marks % | Grade | Points |
|---------|-------|--------|
| ≥ 90%   | O     | 10.0   |
| ≥ 80%   | A+    | 9.0    |
| ≥ 70%   | A     | 8.0    |
| ≥ 60%   | B+    | 7.0    |
| ≥ 50%   | B     | 6.0    |
| ≥ 40%   | C     | 5.0    |
| < 40%   | F     | 0.0    |

---

## 🛠️ Technology Stack

- **Backend**: Python 3.x, Flask, Flask-SQLAlchemy
- **Database**: SQLite (easily switchable to MySQL/PostgreSQL)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Auth**: Werkzeug password hashing, Flask sessions

---

## 💡 Workflow

1. **Admin** → Add students, faculty, subjects → Schedule exam
2. **Faculty** → Select subject + exam → Enter marks → Grades auto-calculated
3. **Admin** → Publish exam results
4. **Student** → Login → View published results → Download CSV

---

## 🔄 Extending to MySQL

Change in `app.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:password@localhost/crms_db'
```
Install: `pip install PyMySQL`
