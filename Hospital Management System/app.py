from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = "hospital_secret_key_2026"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    connection = sqlite3.connect("hospital.db")

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# CREATE DATABASE AND TABLES
# =========================================================

def create_database():

    connection = get_db_connection()


    # -----------------------------------------------------
    # USERS TABLE
    # -----------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            fullname TEXT NOT NULL,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL
        )
    """)


    # -----------------------------------------------------
    # PATIENTS TABLE
    # -----------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS patients (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            fullname TEXT NOT NULL,

            age INTEGER NOT NULL,

            gender TEXT NOT NULL,

            phone TEXT NOT NULL,

            email TEXT,

            address TEXT,

            disease TEXT NOT NULL,

            doctor TEXT NOT NULL
        )
    """)


    # -----------------------------------------------------
    # DOCTORS TABLE
    # -----------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS doctors (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            fullname TEXT NOT NULL,

            specialization TEXT NOT NULL,

            department TEXT NOT NULL,

            phone TEXT NOT NULL,

            email TEXT,

            experience INTEGER NOT NULL
        )
    """)


    # -----------------------------------------------------
    # APPOINTMENTS TABLE
    # -----------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS appointments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_id INTEGER NOT NULL,

            doctor_id INTEGER NOT NULL,

            department TEXT NOT NULL,

            appointment_date TEXT NOT NULL,

            appointment_time TEXT NOT NULL,

            reason TEXT,

            status TEXT NOT NULL DEFAULT 'Scheduled',

            FOREIGN KEY (patient_id)
            REFERENCES patients(id),

            FOREIGN KEY (doctor_id)
            REFERENCES doctors(id)
        )
    """)


    # -----------------------------------------------------
    # MEDICINES TABLE
    # -----------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS medicines (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            category TEXT NOT NULL,

            manufacturer TEXT,

            quantity INTEGER NOT NULL,

            price REAL NOT NULL,

            expiry_date TEXT NOT NULL,

            supplier TEXT
        )
    """)


    # -----------------------------------------------------
    # LABORATORY TABLE
    # -----------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS lab_tests (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_id INTEGER NOT NULL,

            test_name TEXT NOT NULL,

            test_date TEXT NOT NULL,

            result TEXT,

            normal_range TEXT,

            doctor TEXT,

            status TEXT NOT NULL DEFAULT 'Pending',

            FOREIGN KEY (patient_id)
            REFERENCES patients(id)
        )
    """)


        # -----------------------------------------------------
    # BILLING TABLE
    # -----------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS bills (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_id INTEGER NOT NULL,

            bill_number TEXT NOT NULL UNIQUE,

            bill_date TEXT NOT NULL,

            consultation_fee REAL NOT NULL DEFAULT 0,

            medicine_charges REAL NOT NULL DEFAULT 0,

            laboratory_charges REAL NOT NULL DEFAULT 0,

            other_charges REAL NOT NULL DEFAULT 0,

            total_amount REAL NOT NULL DEFAULT 0,

            payment_status TEXT NOT NULL DEFAULT 'Pending',

            FOREIGN KEY (patient_id)
            REFERENCES patients(id)
        )
    """)


    connection.commit()

    connection.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return redirect("/login")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]

        username = request.form["username"]

        password = request.form["password"]


        hashed_password = generate_password_hash(password)


        connection = get_db_connection()


        try:

            connection.execute("""
                INSERT INTO users
                (
                    fullname,
                    username,
                    password
                )
                VALUES (?, ?, ?)
            """, (
                fullname,
                username,
                hashed_password
            ))

            connection.commit()


        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "register.html",
                error="Username already exists"
            )


        connection.close()


        return redirect("/login")


    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]


        connection = get_db_connection()


        user = connection.execute("""
            SELECT *
            FROM users
            WHERE username = ?
        """, (
            username,
        )).fetchone()


        connection.close()


        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            session["fullname"] = user["fullname"]


            return redirect("/dashboard")


        return render_template(
            "login.html",
            error="Invalid username or password"
        )


    return render_template("login.html")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    patient_count = connection.execute("""
        SELECT COUNT(*) AS total
        FROM patients
    """).fetchone()["total"]


    doctor_count = connection.execute("""
        SELECT COUNT(*) AS total
        FROM doctors
    """).fetchone()["total"]


    appointment_count = connection.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
    """).fetchone()["total"]


    medicine_count = connection.execute("""
        SELECT COUNT(*) AS total
        FROM medicines
    """).fetchone()["total"]


    lab_count = connection.execute("""
        SELECT COUNT(*) AS total
        FROM lab_tests
    """).fetchone()["total"]

    bill_count = connection.execute("""
        SELECT COUNT(*) AS total
        FROM bills
    """).fetchone()["total"]

    recent_appointments = connection.execute("""
       SELECT
           appointments.*,
           patients.fullname AS patient_name,
            doctors.fullname AS doctor_name
        FROM appointments
        JOIN patients
            ON appointments.patient_id = patients.id
        JOIN doctors
            ON appointments.doctor_id = doctors.id
        ORDER BY
            appointments.appointment_date DESC,
            appointments.appointment_time DESC
        LIMIT 5
    """).fetchall()


    connection.close()


    return render_template(
        "dashboard.html",

        fullname=session["fullname"],

        username=session["username"],

        patient_count=patient_count,

        doctor_count=doctor_count,

        appointment_count=appointment_count,

        medicine_count=medicine_count,

        lab_count=lab_count,

        bill_count=bill_count,

        recent_appointments=recent_appointments
    )


# =========================================================
# PATIENTS
# =========================================================

@app.route("/patients")
def patients():

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    search = request.args.get("search", "").strip()


    if search:

         patients_list = connection.execute("""
             SELECT *
            FROM patients
            WHERE fullname LIKE ?
            OR phone LIKE ?
            ORDER BY id DESC
        """, (
        f"%{search}%",
        f"%{search}%"
  )).fetchall()

    else:

         patients_list = connection.execute("""
        SELECT *
        FROM patients
        ORDER BY id DESC
    """).fetchall()

    connection.close()


    return render_template(
        "patients.html",
        patients=patients_list,
        search=search
    )


# =========================================================
# ADD PATIENT
# =========================================================

@app.route("/add-patient", methods=["GET", "POST"])
def add_patient():

    if "user_id" not in session:

        return redirect("/login")


    if request.method == "POST":

        fullname = request.form["fullname"]

        age = request.form["age"]

        gender = request.form["gender"]

        phone = request.form["phone"]

        email = request.form["email"]

        address = request.form["address"]

        disease = request.form["disease"]

        doctor = request.form["doctor"]


        connection = get_db_connection()


        connection.execute("""
            INSERT INTO patients
            (
                fullname,
                age,
                gender,
                phone,
                email,
                address,
                disease,
                doctor
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fullname,
            age,
            gender,
            phone,
            email,
            address,
            disease,
            doctor
        ))


        connection.commit()

        connection.close()


        return redirect("/patients")


    return render_template("add_patient.html")

# =========================================================
# VIEW PATIENT
# =========================================================

@app.route("/view-patient/<int:patient_id>")
def view_patient(patient_id):

    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    # PATIENT DETAILS
    patient = connection.execute("""
        SELECT *
        FROM patients
        WHERE id = ?
    """, (
        patient_id,
    )).fetchone()

    # APPOINTMENT HISTORY
    appointments_list = connection.execute("""
        SELECT
            appointments.*,
            doctors.fullname AS doctor_name
        FROM appointments
        JOIN doctors
            ON appointments.doctor_id = doctors.id
        WHERE appointments.patient_id = ?
        ORDER BY
            appointments.appointment_date DESC,
            appointments.appointment_time DESC
    """, (
        patient_id,
    )).fetchall()

    bills_list = connection.execute("""
        SELECT *
        FROM bills
        WHERE patient_id = ?
        ORDER BY bill_date DESC, id DESC
    """, (
        patient_id,
    )).fetchall()

    # ================= LAB HISTORY =================

    lab_tests_list = connection.execute("""
    SELECT *
    FROM lab_tests
    WHERE patient_id = ?
    ORDER BY test_date DESC, id DESC
""", (
    patient_id,
)).fetchall()

    connection.close()

    if patient is None:
        return "Patient not found", 404

    return render_template(
        "view_patient.html",
        patient=patient,
        appointments=appointments_list,
        bills=bills_list,
        lab_tests=lab_tests_list
    )

# =========================================================
# EDIT PATIENT
# =========================================================

@app.route(
    "/edit-patient/<int:patient_id>",
    methods=["GET", "POST"]
)
def edit_patient(patient_id):

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    patient = connection.execute("""
        SELECT *
        FROM patients
        WHERE id = ?
    """, (
        patient_id,
    )).fetchone()


    connection.close()


    if patient is None:

        return "Patient not found", 404


    if request.method == "POST":

        fullname = request.form["fullname"]

        age = request.form["age"]

        gender = request.form["gender"]

        phone = request.form["phone"]

        email = request.form["email"]

        address = request.form["address"]

        disease = request.form["disease"]

        doctor = request.form["doctor"]


        connection = get_db_connection()


        connection.execute("""
            UPDATE patients
            SET

                fullname = ?,

                age = ?,

                gender = ?,

                phone = ?,

                email = ?,

                address = ?,

                disease = ?,

                doctor = ?

            WHERE id = ?
        """, (
            fullname,
            age,
            gender,
            phone,
            email,
            address,
            disease,
            doctor,
            patient_id
        ))


        connection.commit()

        connection.close()


        return redirect("/patients")


    return render_template(
        "edit_patient.html",
        patient=patient
    )


# =========================================================
# DELETE PATIENT
# =========================================================

@app.route("/delete-patient/<int:patient_id>")
def delete_patient(patient_id):

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    connection.execute("""
        DELETE FROM patients
        WHERE id = ?
    """, (
        patient_id,
    ))


    connection.commit()

    connection.close()


    return redirect("/patients")


# =========================================================
# DOCTORS
# =========================================================

@app.route("/doctors")
def doctors():

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    doctors_list = connection.execute("""
        SELECT *
        FROM doctors
        ORDER BY id DESC
    """).fetchall()


    connection.close()


    return render_template(
        "doctors.html",
        doctors=doctors_list
    )


# =========================================================
# ADD DOCTOR
# =========================================================

@app.route("/add-doctor", methods=["GET", "POST"])
def add_doctor():

    if "user_id" not in session:

        return redirect("/login")


    if request.method == "POST":

        fullname = request.form["fullname"]

        specialization = request.form["specialization"]

        department = request.form["department"]

        phone = request.form["phone"]

        email = request.form["email"]

        experience = request.form["experience"]


        connection = get_db_connection()


        connection.execute("""
            INSERT INTO doctors
            (
                fullname,
                specialization,
                department,
                phone,
                email,
                experience
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            fullname,
            specialization,
            department,
            phone,
            email,
            experience
        ))


        connection.commit()

        connection.close()


        return redirect("/doctors")


    return render_template("add_doctor.html")


# =========================================================
# EDIT DOCTOR
# =========================================================

@app.route(
    "/edit-doctor/<int:doctor_id>",
    methods=["GET", "POST"]
)
def edit_doctor(doctor_id):

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    doctor = connection.execute("""
        SELECT *
        FROM doctors
        WHERE id = ?
    """, (
        doctor_id,
    )).fetchone()


    connection.close()


    if doctor is None:

        return "Doctor not found", 404


    if request.method == "POST":

        fullname = request.form["fullname"]

        specialization = request.form["specialization"]

        department = request.form["department"]

        phone = request.form["phone"]

        email = request.form["email"]

        experience = request.form["experience"]


        connection = get_db_connection()


        connection.execute("""
            UPDATE doctors
            SET

                fullname = ?,

                specialization = ?,

                department = ?,

                phone = ?,

                email = ?,

                experience = ?

            WHERE id = ?
        """, (
            fullname,
            specialization,
            department,
            phone,
            email,
            experience,
            doctor_id
        ))


        connection.commit()

        connection.close()


        return redirect("/doctors")


    return render_template(
        "edit_doctor.html",
        doctor=doctor
    )


# =========================================================
# DELETE DOCTOR
# =========================================================

@app.route("/delete-doctor/<int:doctor_id>")
def delete_doctor(doctor_id):

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    connection.execute("""
        DELETE FROM doctors
        WHERE id = ?
    """, (
        doctor_id,
    ))


    connection.commit()

    connection.close()


    return redirect("/doctors")


# =========================================================
# APPOINTMENTS
# =========================================================

@app.route("/appointments")
def appointments():

    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    # SEARCH
    search = request.args.get("search", "").strip()

    # STATUS FILTER
    status = request.args.get("status", "").strip()

    query = """
        SELECT
            appointments.*,
            patients.fullname AS patient_name,
            doctors.fullname AS doctor_name
        FROM appointments
        JOIN patients
            ON appointments.patient_id = patients.id
        JOIN doctors
            ON appointments.doctor_id = doctors.id
        WHERE 1=1
    """

    parameters = []

    # Search by patient name or doctor name
    if search:

        query += """
            AND (
                patients.fullname LIKE ?
                OR doctors.fullname LIKE ?
            )
        """

        parameters.append(f"%{search}%")
        parameters.append(f"%{search}%")

    # Filter by status
    if status:

        query += """
            AND appointments.status = ?
        """

        parameters.append(status)

    # Latest appointments first
    query += """
        ORDER BY
            appointments.appointment_date DESC,
            appointments.appointment_time DESC
    """

    appointments_list = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return render_template(
        "appointments.html",
        appointments=appointments_list,
        search=search,
        status=status
    )
# =========================================================
# ADD APPOINTMENT
# =========================================================

@app.route(
    "/add-appointment",
    methods=["GET", "POST"]
)
def add_appointment():

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    patients_list = connection.execute("""
        SELECT id, fullname
        FROM patients
        ORDER BY fullname
    """).fetchall()


    doctors_list = connection.execute("""
        SELECT id, fullname, department
        FROM doctors
        ORDER BY fullname
    """).fetchall()


    connection.close()


    if request.method == "POST":

        patient_id = request.form["patient_id"]

        doctor_id = request.form["doctor_id"]

        department = request.form["department"]

        appointment_date = request.form["appointment_date"]

        appointment_time = request.form["appointment_time"]

        reason = request.form["reason"]

        status = request.form["status"]


        connection = get_db_connection()


        connection.execute("""
            INSERT INTO appointments
            (
                patient_id,
                doctor_id,
                department,
                appointment_date,
                appointment_time,
                reason,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            doctor_id,
            department,
            appointment_date,
            appointment_time,
            reason,
            status
        ))


        connection.commit()

        connection.close()


        return redirect("/appointments")


    return render_template(
        "add_appointment.html",

        patients=patients_list,

        doctors=doctors_list
    )


# =========================================================
# EDIT APPOINTMENT
# =========================================================

@app.route(
    "/edit-appointment/<int:appointment_id>",
    methods=["GET", "POST"]
)
def edit_appointment(appointment_id):

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    appointment = connection.execute("""
        SELECT *
        FROM appointments
        WHERE id = ?
    """, (
        appointment_id,
    )).fetchone()


    if appointment is None:

        connection.close()

        return "Appointment not found", 404


    patients_list = connection.execute("""
        SELECT id, fullname
        FROM patients
        ORDER BY fullname
    """).fetchall()


    doctors_list = connection.execute("""
        SELECT id, fullname, department
        FROM doctors
        ORDER BY fullname
    """).fetchall()


    connection.close()


    if request.method == "POST":

        patient_id = request.form["patient_id"]

        doctor_id = request.form["doctor_id"]

        department = request.form["department"]

        appointment_date = request.form["appointment_date"]

        appointment_time = request.form["appointment_time"]

        reason = request.form["reason"]

        status = request.form["status"]


        connection = get_db_connection()


        connection.execute("""
            UPDATE appointments
            SET

                patient_id = ?,

                doctor_id = ?,

                department = ?,

                appointment_date = ?,

                appointment_time = ?,

                reason = ?,

                status = ?

            WHERE id = ?
        """, (
            patient_id,
            doctor_id,
            department,
            appointment_date,
            appointment_time,
            reason,
            status,
            appointment_id
        ))


        connection.commit()

        connection.close()


        return redirect("/appointments")


    return render_template(
        "edit_appointment.html",

        appointment=appointment,

        patients=patients_list,

        doctors=doctors_list
    )


# =========================================================
# DELETE APPOINTMENT
# =========================================================

@app.route(
    "/delete-appointment/<int:appointment_id>"
)
def delete_appointment(appointment_id):

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    connection.execute("""
        DELETE FROM appointments
        WHERE id = ?
    """, (
        appointment_id,
    ))


    connection.commit()

    connection.close()


    return redirect("/appointments")


# =========================================================
# PHARMACY
# =========================================================

@app.route("/pharmacy")
def pharmacy():

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    medicines_list = connection.execute("""
        SELECT *
        FROM medicines
        ORDER BY id DESC
    """).fetchall()


    connection.close()


    return render_template(
        "pharmacy.html",
        medicines=medicines_list
    )


# =========================================================
# ADD MEDICINE
# =========================================================

@app.route(
    "/add-medicine",
    methods=["GET", "POST"]
)
def add_medicine():

    if "user_id" not in session:

        return redirect("/login")


    if request.method == "POST":

        name = request.form["name"]

        category = request.form["category"]

        manufacturer = request.form["manufacturer"]

        quantity = request.form["quantity"]

        price = request.form["price"]

        expiry_date = request.form["expiry_date"]

        supplier = request.form["supplier"]


        connection = get_db_connection()


        connection.execute("""
            INSERT INTO medicines
            (
                name,
                category,
                manufacturer,
                quantity,
                price,
                expiry_date,
                supplier
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            category,
            manufacturer,
            quantity,
            price,
            expiry_date,
            supplier
        ))


        connection.commit()

        connection.close()


        return redirect("/pharmacy")


    return render_template("add_medicine.html")


# =========================================================
# EDIT MEDICINE
# =========================================================

@app.route(
    "/edit-medicine/<int:medicine_id>",
    methods=["GET", "POST"]
)
def edit_medicine(medicine_id):

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    medicine = connection.execute("""
        SELECT *
        FROM medicines
        WHERE id = ?
    """, (
        medicine_id,
    )).fetchone()


    connection.close()


    if medicine is None:

        return "Medicine not found", 404


    if request.method == "POST":

        name = request.form["name"]

        category = request.form["category"]

        manufacturer = request.form["manufacturer"]

        quantity = request.form["quantity"]

        price = request.form["price"]

        expiry_date = request.form["expiry_date"]

        supplier = request.form["supplier"]


        connection = get_db_connection()


        connection.execute("""
            UPDATE medicines
            SET

                name = ?,

                category = ?,

                manufacturer = ?,

                quantity = ?,

                price = ?,

                expiry_date = ?,

                supplier = ?

            WHERE id = ?
        """, (
            name,
            category,
            manufacturer,
            quantity,
            price,
            expiry_date,
            supplier,
            medicine_id
        ))


        connection.commit()

        connection.close()


        return redirect("/pharmacy")


    return render_template(
        "edit_medicine.html",
        medicine=medicine
    )


# =========================================================
# DELETE MEDICINE
# =========================================================

@app.route(
    "/delete-medicine/<int:medicine_id>"
)
def delete_medicine(medicine_id):

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    connection.execute("""
        DELETE FROM medicines
        WHERE id = ?
    """, (
        medicine_id,
    ))


    connection.commit()

    connection.close()


    return redirect("/pharmacy")


# =========================================================
# LABORATORY
# =========================================================

@app.route("/laboratory")
def laboratory():

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    lab_tests_list = connection.execute("""
        SELECT

            lab_tests.*,

            patients.fullname AS patient_name

        FROM lab_tests

        JOIN patients

        ON lab_tests.patient_id = patients.id

        ORDER BY

            lab_tests.test_date DESC,

            lab_tests.id DESC

    """).fetchall()


    connection.close()


    return render_template(
        "laboratory.html",
        lab_tests=lab_tests_list
    )


# =========================================================
# ADD LAB TEST
# =========================================================

@app.route(
    "/add-lab-test",
    methods=["GET", "POST"]
)
def add_lab_test():

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    patients_list = connection.execute("""
        SELECT

            id,

            fullname

        FROM patients

        ORDER BY fullname

    """).fetchall()


    connection.close()


    if request.method == "POST":

        patient_id = request.form["patient_id"]

        test_name = request.form["test_name"]

        test_date = request.form["test_date"]

        result = request.form["result"]

        normal_range = request.form["normal_range"]

        doctor = request.form["doctor"]

        status = request.form["status"]


        connection = get_db_connection()


        connection.execute("""
            INSERT INTO lab_tests
            (
                patient_id,

                test_name,

                test_date,

                result,

                normal_range,

                doctor,

                status
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)

        """, (
            patient_id,

            test_name,

            test_date,

            result,

            normal_range,

            doctor,

            status
        ))


        connection.commit()

        connection.close()


        return redirect("/laboratory")


    return render_template(
        "add_lab_test.html",

        patients=patients_list
    )


# =========================================================
# EDIT LAB TEST
# =========================================================

@app.route(
    "/edit-lab-test/<int:lab_test_id>",
    methods=["GET", "POST"]
)
def edit_lab_test(lab_test_id):

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    lab_test = connection.execute("""
        SELECT *

        FROM lab_tests

        WHERE id = ?

    """, (
        lab_test_id,
    )).fetchone()


    if lab_test is None:

        connection.close()

        return "Laboratory test not found", 404


    patients_list = connection.execute("""
        SELECT

            id,

            fullname

        FROM patients

        ORDER BY fullname

    """).fetchall()


    connection.close()


    if request.method == "POST":

        patient_id = request.form["patient_id"]

        test_name = request.form["test_name"]

        test_date = request.form["test_date"]

        result = request.form["result"]

        normal_range = request.form["normal_range"]

        doctor = request.form["doctor"]

        status = request.form["status"]


        connection = get_db_connection()


        connection.execute("""
            UPDATE lab_tests

            SET

                patient_id = ?,

                test_name = ?,

                test_date = ?,

                result = ?,

                normal_range = ?,

                doctor = ?,

                status = ?

            WHERE id = ?

        """, (
            patient_id,

            test_name,

            test_date,

            result,

            normal_range,

            doctor,

            status,

            lab_test_id
        ))


        connection.commit()

        connection.close()


        return redirect("/laboratory")


    return render_template(
        "edit_lab_test.html",

        lab_test=lab_test,

        patients=patients_list
    )


# =========================================================
# DELETE LAB TEST
# =========================================================

@app.route(
    "/delete-lab-test/<int:lab_test_id>"
)
def delete_lab_test(lab_test_id):

    if "user_id" not in session:

        return redirect("/login")


    connection = get_db_connection()


    connection.execute("""
        DELETE FROM lab_tests

        WHERE id = ?

    """, (
        lab_test_id,
    ))


    connection.commit()

    connection.close()


    return redirect("/laboratory")


# =========================================================
# BILLING
# =========================================================

@app.route("/billing")
def billing():

    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    bills_list = connection.execute("""
        SELECT
            bills.*,
            patients.fullname AS patient_name
        FROM bills
        JOIN patients
        ON bills.patient_id = patients.id
        ORDER BY bills.bill_date DESC, bills.id DESC
    """).fetchall()

    connection.close()

    return render_template(
        "billing.html",
        bills=bills_list
    )


# =========================================================
# ADD BILL
# =========================================================

@app.route("/add-bill", methods=["GET", "POST"])
def add_bill():

    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    patients_list = connection.execute("""
        SELECT
            id,
            fullname
        FROM patients
        ORDER BY fullname
    """).fetchall()

    connection.close()

    if request.method == "POST":

        patient_id = request.form["patient_id"]
        bill_number = request.form["bill_number"]
        bill_date = request.form["bill_date"]

        consultation_fee = float(
            request.form.get("consultation_fee") or 0
        )

        medicine_charges = float(
            request.form.get("medicine_charges") or 0
        )

        laboratory_charges = float(
            request.form.get("laboratory_charges") or 0
        )

        other_charges = float(
            request.form.get("other_charges") or 0
        )

        payment_status = request.form["payment_status"]

        total_amount = (
            consultation_fee
            + medicine_charges
            + laboratory_charges
            + other_charges
        )

        connection = get_db_connection()

        try:

            connection.execute("""
                INSERT INTO bills
                (
                    patient_id,
                    bill_number,
                    bill_date,
                    consultation_fee,
                    medicine_charges,
                    laboratory_charges,
                    other_charges,
                    total_amount,
                    payment_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id,
                bill_number,
                bill_date,
                consultation_fee,
                medicine_charges,
                laboratory_charges,
                other_charges,
                total_amount,
                payment_status
            ))

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "add_bill.html",
                patients=patients_list,
                error="Bill number already exists"
            )

        connection.close()

        return redirect("/billing")

    return render_template(
        "add_bill.html",
        patients=patients_list
    )


# =========================================================
# EDIT BILL
# =========================================================

@app.route(
    "/edit-bill/<int:bill_id>",
    methods=["GET", "POST"]
)
def edit_bill(bill_id):

    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    bill = connection.execute("""
        SELECT *
        FROM bills
        WHERE id = ?
    """, (
        bill_id,
    )).fetchone()

    if bill is None:

        connection.close()

        return "Bill not found", 404

    patients_list = connection.execute("""
        SELECT
            id,
            fullname
        FROM patients
        ORDER BY fullname
    """).fetchall()

    connection.close()

    if request.method == "POST":

        patient_id = request.form["patient_id"]
        bill_number = request.form["bill_number"]
        bill_date = request.form["bill_date"]

        consultation_fee = float(
            request.form.get("consultation_fee") or 0
        )

        medicine_charges = float(
            request.form.get("medicine_charges") or 0
        )

        laboratory_charges = float(
            request.form.get("laboratory_charges") or 0
        )

        other_charges = float(
            request.form.get("other_charges") or 0
        )

        payment_status = request.form["payment_status"]

        total_amount = (
            consultation_fee
            + medicine_charges
            + laboratory_charges
            + other_charges
        )

        connection = get_db_connection()

        try:

            connection.execute("""
                UPDATE bills
                SET
                    patient_id = ?,
                    bill_number = ?,
                    bill_date = ?,
                    consultation_fee = ?,
                    medicine_charges = ?,
                    laboratory_charges = ?,
                    other_charges = ?,
                    total_amount = ?,
                    payment_status = ?
                WHERE id = ?
            """, (
                patient_id,
                bill_number,
                bill_date,
                consultation_fee,
                medicine_charges,
                laboratory_charges,
                other_charges,
                total_amount,
                payment_status,
                bill_id
            ))

            connection.commit()

        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "edit_bill.html",
                bill=bill,
                patients=patients_list,
                error="Bill number already exists"
            )

        connection.close()

        return redirect("/billing")

    return render_template(
        "edit_bill.html",
        bill=bill,
        patients=patients_list
    )


# =========================================================
# DELETE BILL
# =========================================================

@app.route("/delete-bill/<int:bill_id>")
def delete_bill(bill_id):

    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    connection.execute("""
        DELETE FROM bills
        WHERE id = ?
    """, (
        bill_id,
    ))

    connection.commit()

    connection.close()

    return redirect("/billing")

# =========================================================
# PRINT BILL
# =========================================================

@app.route("/print-bill/<int:bill_id>")
def print_bill(bill_id):

    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    bill = connection.execute("""
        SELECT
            bills.*,
            patients.fullname AS patient_name,
            patients.phone AS patient_phone,
            patients.email AS patient_email,
            patients.address AS patient_address
        FROM bills
        JOIN patients
            ON bills.patient_id = patients.id
        WHERE bills.id = ?
    """, (bill_id,)).fetchone()

    connection.close()

    if bill is None:
        return "Bill not found", 404

    return render_template(
        "print_bill.html",
        bill=bill
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    create_database()

    app.run(debug=True)
