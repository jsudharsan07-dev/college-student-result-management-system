from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os
import io
import csv

app = Flask(__name__)
app.secret_key = 'crms_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///college_result.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── MODELS ────────────────────────────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, faculty, student
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    batch_year = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(15))
    user = db.relationship('User', backref='student_profile')

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100))
    user = db.relationship('User', backref='faculty_profile')

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'))
    faculty = db.relationship('Faculty', backref='subjects')

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)  # internal, external, midterm, final
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    max_marks = db.Column(db.Integer, nullable=False, default=100)
    date = db.Column(db.DateTime)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(5))
    grade_points = db.Column(db.Float)
    remarks = db.Column(db.String(200))
    entered_by = db.Column(db.Integer, db.ForeignKey('faculty.id'))
    entered_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student', backref='results')
    subject = db.relationship('Subject', backref='results')
    exam = db.relationship('Exam', backref='results')

# ─── HELPERS ───────────────────────────────────────────────────────────────────

def calculate_grade(marks, max_marks=100):
    percentage = (marks / max_marks) * 100
    if percentage >= 90:
        return 'O', 10.0
    elif percentage >= 80:
        return 'A+', 9.0
    elif percentage >= 70:
        return 'A', 8.0
    elif percentage >= 60:
        return 'B+', 7.0
    elif percentage >= 50:
        return 'B', 6.0
    elif percentage >= 40:
        return 'C', 5.0
    else:
        return 'F', 0.0

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# ─── AUTH ROUTES ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            flash(f'Welcome, {user.full_name}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    stats = {}
    if role == 'admin':
        stats['students'] = Student.query.count()
        stats['faculty'] = Faculty.query.count()
        stats['subjects'] = Subject.query.count()
        stats['exams'] = Exam.query.count()
        stats['results'] = Result.query.count()
        recent_exams = Exam.query.order_by(Exam.created_at.desc()).limit(5).all()
        return render_template('admin/dashboard.html', stats=stats, recent_exams=recent_exams)
    elif role == 'faculty':
        faculty = Faculty.query.filter_by(user_id=session['user_id']).first()
        if faculty:
            stats['subjects'] = Subject.query.filter_by(faculty_id=faculty.id).count()
            stats['results_entered'] = Result.query.filter_by(entered_by=faculty.id).count()
            my_subjects = Subject.query.filter_by(faculty_id=faculty.id).all()
        return render_template('faculty/dashboard.html', stats=stats, faculty=faculty, subjects=my_subjects if faculty else [])
    elif role == 'student':
        student = Student.query.filter_by(user_id=session['user_id']).first()
        if student:
            results = Result.query.filter_by(student_id=student.id).join(Exam).filter(Exam.is_published==True).all()
            stats['results'] = len(results)
            if results:
                total_gp = sum(r.grade_points for r in results if r.grade_points)
                stats['cgpa'] = round(total_gp / len(results), 2) if results else 0
            else:
                stats['cgpa'] = 0
        return render_template('student/dashboard.html', stats=stats, student=student)
    return render_template('dashboard.html', stats=stats)

# ─── ADMIN ROUTES ──────────────────────────────────────────────────────────────

@app.route('/admin/students')
@login_required
@role_required('admin')
def admin_students():
    students = db.session.query(Student, User).join(User, Student.user_id == User.id).all()
    return render_template('admin/students.html', students=students)

@app.route('/admin/students/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_student():
    if request.method == 'POST':
        try:
            user = User(
                username=request.form['username'],
                password=generate_password_hash(request.form['password']),
                role='student',
                full_name=request.form['full_name'],
                email=request.form['email']
            )
            db.session.add(user)
            db.session.flush()
            student = Student(
                user_id=user.id,
                roll_number=request.form['roll_number'],
                department=request.form['department'],
                semester=int(request.form['semester']),
                batch_year=int(request.form['batch_year']),
                phone=request.form.get('phone', '')
            )
            db.session.add(student)
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('admin_students'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('admin/add_student.html')

@app.route('/admin/students/delete/<int:id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_student(id):
    student = Student.query.get_or_404(id)
    user = User.query.get(student.user_id)
    Result.query.filter_by(student_id=student.id).delete()
    db.session.delete(student)
    if user:
        db.session.delete(user)
    db.session.commit()
    flash('Student deleted.', 'info')
    return redirect(url_for('admin_students'))

@app.route('/admin/faculty')
@login_required
@role_required('admin')
def admin_faculty():
    faculty_list = db.session.query(Faculty, User).join(User, Faculty.user_id == User.id).all()
    return render_template('admin/faculty.html', faculty_list=faculty_list)

@app.route('/admin/faculty/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_faculty():
    if request.method == 'POST':
        try:
            user = User(
                username=request.form['username'],
                password=generate_password_hash(request.form['password']),
                role='faculty',
                full_name=request.form['full_name'],
                email=request.form['email']
            )
            db.session.add(user)
            db.session.flush()
            faculty = Faculty(
                user_id=user.id,
                employee_id=request.form['employee_id'],
                department=request.form['department'],
                designation=request.form.get('designation', '')
            )
            db.session.add(faculty)
            db.session.commit()
            flash('Faculty added successfully!', 'success')
            return redirect(url_for('admin_faculty'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('admin/add_faculty.html')

@app.route('/admin/subjects')
@login_required
@role_required('admin')
def admin_subjects():
    subjects = Subject.query.join(Faculty, Subject.faculty_id == Faculty.id, isouter=True).all()
    return render_template('admin/subjects.html', subjects=subjects)

@app.route('/admin/subjects/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_subject():
    faculty_list = Faculty.query.join(User).all()
    if request.method == 'POST':
        try:
            subject = Subject(
                code=request.form['code'],
                name=request.form['name'],
                department=request.form['department'],
                semester=int(request.form['semester']),
                credits=int(request.form['credits']),
                faculty_id=request.form.get('faculty_id') or None
            )
            db.session.add(subject)
            db.session.commit()
            flash('Subject added!', 'success')
            return redirect(url_for('admin_subjects'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('admin/add_subject.html', faculty_list=faculty_list)

@app.route('/admin/exams')
@login_required
@role_required('admin')
def admin_exams():
    exams = Exam.query.order_by(Exam.created_at.desc()).all()
    return render_template('admin/exams.html', exams=exams)

@app.route('/admin/exams/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_add_exam():
    if request.method == 'POST':
        try:
            exam = Exam(
                name=request.form['name'],
                exam_type=request.form['exam_type'],
                department=request.form['department'],
                semester=int(request.form['semester']),
                year=int(request.form['year']),
                max_marks=int(request.form['max_marks'])
            )
            db.session.add(exam)
            db.session.commit()
            flash('Exam schedule added!', 'success')
            return redirect(url_for('admin_exams'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('admin/add_exam.html')

@app.route('/admin/exams/publish/<int:id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_publish_exam(id):
    exam = Exam.query.get_or_404(id)
    exam.is_published = not exam.is_published
    db.session.commit()
    status = 'published' if exam.is_published else 'unpublished'
    flash(f'Exam {status} successfully!', 'success')
    return redirect(url_for('admin_exams'))

@app.route('/admin/reports')
@login_required
@role_required('admin')
def admin_reports():
    departments = db.session.query(Student.department).distinct().all()
    dept_stats = []
    for (dept,) in departments:
        students = Student.query.filter_by(department=dept).count()
        results = db.session.query(Result).join(Student).filter(Student.department==dept).count()
        dept_stats.append({'name': dept, 'students': students, 'results': results})
    return render_template('admin/reports.html', dept_stats=dept_stats)

# ─── FACULTY ROUTES ────────────────────────────────────────────────────────────

@app.route('/faculty/enter-marks', methods=['GET', 'POST'])
@login_required
@role_required('faculty')
def faculty_enter_marks():
    faculty = Faculty.query.filter_by(user_id=session['user_id']).first()
    subjects = Subject.query.filter_by(faculty_id=faculty.id).all() if faculty else []
    exams = Exam.query.all()
    
    selected_subject = request.args.get('subject_id')
    selected_exam = request.args.get('exam_id')
    students_data = []
    
    if selected_subject and selected_exam:
        subject = Subject.query.get(selected_subject)
        exam = Exam.query.get(selected_exam)
        if subject:
            students = Student.query.filter_by(department=subject.department, semester=subject.semester).all()
            for s in students:
                existing = Result.query.filter_by(student_id=s.id, subject_id=subject.id, exam_id=exam.id).first()
                students_data.append({'student': s, 'result': existing})
    
    if request.method == 'POST':
        sub_id = request.form.get('subject_id')
        exam_id = request.form.get('exam_id')
        exam = Exam.query.get(exam_id)
        try:
            for key, value in request.form.items():
                if key.startswith('marks_'):
                    student_id = int(key.split('_')[1])
                    marks = float(value) if value else 0
                    grade, gp = calculate_grade(marks, exam.max_marks)
                    existing = Result.query.filter_by(student_id=student_id, subject_id=sub_id, exam_id=exam_id).first()
                    if existing:
                        existing.marks_obtained = marks
                        existing.grade = grade
                        existing.grade_points = gp
                        existing.entered_by = faculty.id
                    else:
                        result = Result(student_id=student_id, subject_id=sub_id, exam_id=exam_id,
                                        marks_obtained=marks, grade=grade, grade_points=gp, entered_by=faculty.id)
                        db.session.add(result)
            db.session.commit()
            flash('Marks saved successfully!', 'success')
            return redirect(url_for('faculty_enter_marks', subject_id=sub_id, exam_id=exam_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving marks: {str(e)}', 'danger')
    
    return render_template('faculty/enter_marks.html', subjects=subjects, exams=exams,
                           students_data=students_data, selected_subject=selected_subject, selected_exam=selected_exam)

@app.route('/faculty/grade-sheet')
@login_required
@role_required('faculty')
def faculty_grade_sheet():
    faculty = Faculty.query.filter_by(user_id=session['user_id']).first()
    subjects = Subject.query.filter_by(faculty_id=faculty.id).all() if faculty else []
    exams = Exam.query.all()
    
    selected_subject = request.args.get('subject_id')
    selected_exam = request.args.get('exam_id')
    grade_data = []
    subject_obj = None
    exam_obj = None
    
    if selected_subject and selected_exam:
        subject_obj = Subject.query.get(selected_subject)
        exam_obj = Exam.query.get(selected_exam)
        if subject_obj:
            results = Result.query.filter_by(subject_id=subject_obj.id, exam_id=exam_obj.id).join(Student).order_by(Student.roll_number).all()
            grade_data = results
    
    return render_template('faculty/grade_sheet.html', subjects=subjects, exams=exams,
                           grade_data=grade_data, selected_subject=selected_subject, selected_exam=selected_exam,
                           subject_obj=subject_obj, exam_obj=exam_obj)

# ─── STUDENT ROUTES ────────────────────────────────────────────────────────────

@app.route('/student/results')
@login_required
@role_required('student')
def student_results():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    results = []
    exams = []
    if student:
        results = Result.query.filter_by(student_id=student.id).join(Exam).filter(Exam.is_published==True).all()
        exam_ids = list(set(r.exam_id for r in results))
        exams = Exam.query.filter(Exam.id.in_(exam_ids)).all()
    return render_template('student/results.html', student=student, results=results, exams=exams)

@app.route('/student/download-result')
@login_required
@role_required('student')
def student_download_result():
    student = Student.query.filter_by(user_id=session['user_id']).first()
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('student_results'))
    
    results = Result.query.filter_by(student_id=student.id).join(Exam).filter(Exam.is_published==True).all()
    user = User.query.get(student.user_id)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['COLLEGE RESULT MANAGEMENT SYSTEM'])
    writer.writerow(['Student Result Sheet'])
    writer.writerow([])
    writer.writerow(['Name:', user.full_name, 'Roll No:', student.roll_number])
    writer.writerow(['Department:', student.department, 'Semester:', student.semester])
    writer.writerow(['Batch Year:', student.batch_year])
    writer.writerow([])
    writer.writerow(['Subject Code', 'Subject Name', 'Exam', 'Max Marks', 'Marks Obtained', 'Grade', 'Grade Points'])
    
    total_gp = 0
    for r in results:
        writer.writerow([r.subject.code, r.subject.name, r.exam.name, r.exam.max_marks,
                         r.marks_obtained, r.grade, r.grade_points])
        total_gp += r.grade_points or 0
    
    if results:
        cgpa = round(total_gp / len(results), 2)
        writer.writerow([])
        writer.writerow(['CGPA:', cgpa])
    
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv',
                     download_name=f'result_{student.roll_number}.csv', as_attachment=True)

# ─── API ROUTES ────────────────────────────────────────────────────────────────

@app.route('/api/stats')
@login_required
@role_required('admin')
def api_stats():
    dept_data = []
    departments = db.session.query(Student.department).distinct().all()
    for (dept,) in departments:
        count = Student.query.filter_by(department=dept).count()
        dept_data.append({'dept': dept, 'count': count})
    
    grade_dist = {'O': 0, 'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'F': 0}
    all_results = Result.query.all()
    for r in all_results:
        if r.grade in grade_dist:
            grade_dist[r.grade] += 1
    
    return jsonify({'departments': dept_data, 'grade_distribution': grade_dist})

# ─── INIT DB ───────────────────────────────────────────────────────────────────

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password=generate_password_hash('admin123'),
                         role='admin', full_name='System Administrator', email='admin@college.edu')
            db.session.add(admin)

            fuser = User(username='faculty1', password=generate_password_hash('faculty123'),
                         role='faculty', full_name='Dr. Priya Sharma', email='priya@college.edu')
            db.session.add(fuser)
            db.session.flush()

            faculty = Faculty(user_id=fuser.id, employee_id='FAC001', department='Computer Science', designation='Associate Professor')
            db.session.add(faculty)
            db.session.flush()

            suser = User(username='student1', password=generate_password_hash('student123'),
                         role='student', full_name='Arjun Kumar', email='arjun@college.edu')
            db.session.add(suser)
            db.session.flush()

            student = Student(user_id=suser.id, roll_number='CS2024001', department='Computer Science',
                              semester=3, batch_year=2024, phone='9876543210')
            db.session.add(student)
            db.session.flush()

            sub1 = Subject(code='CS301', name='Data Structures', department='Computer Science',
                           semester=3, credits=4, faculty_id=faculty.id)
            sub2 = Subject(code='CS302', name='Database Management Systems', department='Computer Science',
                           semester=3, credits=3, faculty_id=faculty.id)
            sub3 = Subject(code='CS303', name='Operating Systems', department='Computer Science',
                           semester=3, credits=4, faculty_id=faculty.id)
            db.session.add_all([sub1, sub2, sub3])
            db.session.flush()

            exam = Exam(name='Mid Semester Exam 2024', exam_type='midterm', department='Computer Science',
                        semester=3, year=2024, max_marks=100, is_published=True)
            db.session.add(exam)
            db.session.flush()

            r1 = Result(student_id=student.id, subject_id=sub1.id, exam_id=exam.id,
                        marks_obtained=85, grade='A+', grade_points=9.0, entered_by=faculty.id)
            r2 = Result(student_id=student.id, subject_id=sub2.id, exam_id=exam.id,
                        marks_obtained=78, grade='A', grade_points=8.0, entered_by=faculty.id)
            r3 = Result(student_id=student.id, subject_id=sub3.id, exam_id=exam.id,
                        marks_obtained=91, grade='O', grade_points=10.0, entered_by=faculty.id)
            db.session.add_all([r1, r2, r3])
            db.session.commit()
            print("✅ Database initialized with sample data.")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
