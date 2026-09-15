from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)


# Create database and table
def create_database():
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# Home page
@app.route("/")
def home():
    return render_template("reglogin.html")


# Registration
@app.route("/register", methods=["POST"])
def register():

    fullname = request.form["fullname"]
    username = request.form["username"]
    password = request.form["password"]

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (fullname, username, password)
            VALUES (?, ?, ?)
        """, (fullname, username, password))

        connection.commit()

    except sqlite3.IntegrityError:
        connection.close()
        return "<h2>Registration failed</h2><p>Username already exists.</p>"

    connection.close()

    return redirect("/login")


# Login page - GET
@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


# Login - POST
@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM users
        WHERE username = ? AND password = ?
    """, (username, password))

    user = cursor.fetchone()

    connection.close()

    if user:
        return f"""
        <h2>Login Successful</h2>
        <p>Welcome, {username}!</p>
        """

    else:
        return """
        <h2>Login Failed</h2>
        <p>Username or password is incorrect.</p>
        """


if __name__ == "__main__":
    create_database()
    app.run(debug=True)
