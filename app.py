from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)

# Secret key used for login sessions
app.secret_key = "smart-queue-secret-key"

DATABASE = "database/queue.db"

# Demo admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    os.makedirs("database", exist_ok=True)

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            token TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Waiting'
        )
    """)

    connection.commit()
    connection.close()


# -------------------------
# USER PAGE
# -------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -------------------------
# JOIN QUEUE
# -------------------------

@app.route("/join", methods=["POST"])
def join_queue():

    name = request.form["name"].strip()

    if not name:
        return render_template(
            "index.html",
            error="Please enter your name."
        )

    connection = get_db_connection()

    # Find the last token created
    last_token = connection.execute(
        """
        SELECT token
        FROM queue
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    if last_token:
        last_number = int(last_token["token"][1:])
        token_number = last_number + 1
    else:
        token_number = 1

    token = f"A{token_number:03d}"

    # Add user to queue
    connection.execute(
        """
        INSERT INTO queue (name, token, status)
        VALUES (?, ?, ?)
        """,
        (name, token, "Waiting")
    )

    connection.commit()

    # Calculate people ahead
    people_ahead = connection.execute(
        """
        SELECT COUNT(*)
        FROM queue
        WHERE status = 'Waiting'
        AND id < (
            SELECT id
            FROM queue
            WHERE token = ?
            ORDER BY id DESC
            LIMIT 1
        )
        """,
        (token,)
    ).fetchone()[0]

    connection.close()

    return render_template(
        "index.html",
        token=token,
        name=name,
        people_ahead=people_ahead
    )


# -------------------------
# ADMIN LOGIN
# -------------------------

@app.route("/admin")
def admin():

    # If not logged in, show login page
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    queue = connection.execute(
        """
        SELECT *
        FROM queue
        ORDER BY id ASC
        """
    ).fetchall()

    current = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE status = 'Serving'
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()

    connection.close()

    return render_template(
        "admin.html",
        queue=queue,
        current=current
    )


# -------------------------
# ADMIN LOGIN PAGE
# -------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    error = None

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):
            session["admin_logged_in"] = True

            return redirect(url_for("admin"))

        error = "Invalid username or password."

    return render_template(
        "login.html",
        error=error
    )


# -------------------------
# ADMIN LOGOUT
# -------------------------

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_logged_in", None)

    return redirect(url_for("admin_login"))


# -------------------------
# CALL NEXT
# -------------------------

@app.route("/admin/next", methods=["POST"])
def call_next():

    # Prevent unauthorized access
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    # Find current serving person
    current = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE status = 'Serving'
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()

    # Mark current person as served
    if current:

        connection.execute(
            """
            UPDATE queue
            SET status = 'Served'
            WHERE id = ?
            """,
            (current["id"],)
        )

    # Find next waiting person
    next_person = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE status = 'Waiting'
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()

    # Mark next person as serving
    if next_person:

        connection.execute(
            """
            UPDATE queue
            SET status = 'Serving'
            WHERE id = ?
            """,
            (next_person["id"],)
        )

    connection.commit()

    # Get updated queue
    queue = connection.execute(
        """
        SELECT *
        FROM queue
        ORDER BY id ASC
        """
    ).fetchall()

    # Get current serving person
    current = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE status = 'Serving'
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()

    connection.close()

    return render_template(
        "admin.html",
        queue=queue,
        current=current
    )


# -------------------------
# RUN APPLICATION
# -------------------------

if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)