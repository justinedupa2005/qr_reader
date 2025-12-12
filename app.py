import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from db.dbhelper import *
import sys
sys.path.insert(0, "db/")

app = Flask(__name__)

app.secret_key = "supersecretkey"

# Folder to store uploaded images
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Make sure folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Create admin table if it doesn't exist
createAdminTable()


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/signup")
def signup():
    return render_template('sign-up.html')


@app.route("/sign-in")
def signin():
    return render_template('sign-in.html')


@app.route("/attendance")
def attendance():
    """Attendance Records Page"""
    return render_template('attendance.html')


@app.route("/dashboard")
def dashboard():
    """Display all students in the table"""
    students = getAll('students')
    return render_template('studentMngt.html', studentlist=students, student=None)


@app.route('/api/get_students')
def get_students():
    try:
        students = getAll('students')
        student_list = []

        for student in students:
            image_path = None
            if student['image']:
                image_path = f"/static/uploads/{student['image']}"

            student_list.append({
                'idno': student['idno'],
                'firstname': student['firstname'],
                'lastname': student['lastname'],
                'course': student['course'],
                'level': student['level'],
                'image': image_path
            })

        return jsonify(student_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    # Check if fields are filled
    if not email or not password:
        flash("Please enter both email and password.", "error")
        return redirect(url_for('signin'))

    # Get admin from database
    admin = getRecord('admin', email=email)

    if not admin:
        # Account not found in database
        flash("Account not found.", "error")
        return redirect(url_for('signin'))

    admin = admin[0]

    # Check password (with hashing support)
    if check_password_hash(admin['password'], password):
        # Login successful - redirect to admin.html
        return redirect(url_for('admin'))
    else:
        # Wrong password
        flash("Incorrect email or password.", "error")
        return redirect(url_for('signin'))


@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    # Validate input
    if not email or not password or not confirm_password:
        flash("All fields are required.", "error")
        return redirect(url_for('signup'))

    # Check if passwords match
    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for('signup'))

    # Check if admin already exists
    existing_admin = getRecord('admin', email=email)
    if existing_admin:
        flash("Email is already registered.", "error")
        return redirect(url_for('signup'))

    # Hash password
    hashed_password = generate_password_hash(password)

    # Add admin to database
    addRecord('admin', email=email, password=hashed_password)

    # Redirect to login page
    flash("Registration successful. Please log in.", "success")
    return redirect(url_for('signin'))


@app.route("/admin")
def admin():
    admins = getAll('admin')
    return render_template('admin.html', adminlist=admins, admin=None)


@app.route('/add_admin', methods=['POST'])
def add_admin():
    email = request.form.get('email')
    password = request.form.get('password')

    # Validate input
    if not email or not password:
        flash("All fields are required.", "error")
        return redirect(url_for('admin'))

    # Check if admin already exists
    existing_admin = getRecord('admin', email=email)
    if existing_admin:
        flash("Admin with this email already exists.", "error")
        return redirect(url_for('admin'))

    # Hash password
    hashed_password = generate_password_hash(password)

    # Add admin to database
    addRecord('admin', email=email, password=hashed_password)
    flash("Admin added successfully!", "success")

    return redirect(url_for('admin'))


@app.route('/delete_admin/<int:id>')
def delete_admin(id):
    deleteRecord("admin", id=id)
    flash("Admin deleted successfully!", "success")
    return redirect(url_for('admin'))


@app.route("/update_admin/<int:id>", methods=['GET', 'POST'])
def update_admin(id):
    admin_record = getRecord("admin", id=id)
    if not admin_record:
        flash("Admin not found.", "error")
        return redirect(url_for('admin'))

    admin_record = admin_record[0]

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # If password is provided, hash it; otherwise keep the old password
        if password and password.strip():
            hashed_password = generate_password_hash(password)
            updateRecord("admin", id=id, email=email, password=hashed_password)
        else:
            updateRecord("admin", id=id, email=email,
                         password=admin_record['password'])

        flash("Admin updated successfully!", "success")
        return redirect(url_for('admin'))

    # GET request - show form with current admin data
    admins = getAll('admin')
    return render_template('admin.html', admin=admin_record, adminlist=admins)


@app.route('/view_student/<idno>')
def view_student(idno):
    """View student details in the left panel"""
    student = getRecord("students", idno=idno)
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for('dashboard'))

    student = student[0]
    students = getAll('students')
    return render_template('studentMngt.html', student=student, studentlist=students)


@app.route('/add_student_page')
def add_student_page():
    return render_template('student.html', student=None, is_edit=False)


@app.route('/add_student', methods=['POST'])
def add_student():
    """Add a new student to the database"""
    idno = request.form.get('idno')
    lastname = request.form.get('lastname')
    firstname = request.form.get('firstname')
    course = request.form.get('course')
    level = request.form.get('level')

    # Validate input
    if not all([idno, lastname, firstname, course, level]):
        flash("All fields are required.", "error")
        return redirect(url_for('add_student_page'))

    # Check if student with this ID already exists
    existing_student = getRecord('students', idno=idno)
    if existing_student:
        flash("Student with this ID already exists.", "error")
        return redirect(url_for('add_student_page'))

    # Handle image upload
    image_file = request.files.get('image')
    image_filename = None
    if image_file and image_file.filename != '':
        image_filename = secure_filename(f"{idno}_{image_file.filename}")
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image_file.save(image_path)

    # Add student record including image
    addRecord("students",
              idno=idno,
              lastname=lastname,
              firstname=firstname,
              course=course,
              level=level,
              image=image_filename)

    flash("Student added successfully!", "success")
    return redirect(url_for('dashboard'))


@app.route('/delete_student/<idno>')
def delete_student(idno):
    """Delete a student from the database"""
    student = getRecord("students", idno=idno)

    if student and student[0]['image']:
        # Delete the image file if it exists
        image_path = os.path.join(
            app.config['UPLOAD_FOLDER'], student[0]['image'])
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                print(f"Error deleting image: {e}")

    deleteRecord("students", idno=idno)
    flash("Student deleted successfully!", "success")
    return redirect(url_for('dashboard'))


@app.route('/update_student/<idno>', methods=['GET', 'POST'])
def update_student(idno):
    """Update student information"""
    student = getRecord("students", idno=idno)
    if not student:
        flash("Student not found.", "error")
        return redirect(url_for('dashboard'))

    student = student[0]

    if request.method == 'POST':
        lastname = request.form.get('lastname')
        firstname = request.form.get('firstname')
        course = request.form.get('course')
        level = request.form.get('level')

        # Handle image upload
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            # Delete old image if it exists
            if student['image']:
                old_image_path = os.path.join(
                    app.config['UPLOAD_FOLDER'], student['image'])
                if os.path.exists(old_image_path):
                    try:
                        os.remove(old_image_path)
                    except Exception as e:
                        print(f"Error deleting old image: {e}")

            # Save new image
            image_filename = secure_filename(f"{idno}_{image_file.filename}")
            image_path = os.path.join(
                app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)
        else:
            # Keep existing image
            image_filename = student['image']

        # Update student record
        updateRecord("students",
                     idno=idno,
                     lastname=lastname,
                     firstname=firstname,
                     course=course,
                     level=level,
                     image=image_filename)

        flash("Student updated successfully!", "success")
        return redirect(url_for('dashboard'))

    # GET request - show form with current student data
    return render_template('student.html', student=student, is_edit=True)


if __name__ == "__main__":
    app.run(debug=True)
