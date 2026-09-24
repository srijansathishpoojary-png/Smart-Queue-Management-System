from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)

app.secret_key = "smart-queue-secret-key"

DATABASE = "database/queue.db"

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

    cursor = connection.execute(
        """
        INSERT INTO queue (name, token, status)
        VALUES (?, ?, ?)
        """,
        (name, token, "Waiting")
    )

    user_id = cursor.lastrowid

    connection.commit()

    people_ahead = connection.execute(
        """
        SELECT COUNT(*)
        FROM queue
        WHERE status = 'Waiting'
        AND id < ?
        """,
        (user_id,)
    ).fetchone()[0]

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
        "index.html",
        token=token,
        name=name,
        people_ahead=people_ahead,
        current=current
    )


# -------------------------
# USER QUEUE STATUS
# -------------------------

@app.route("/status/<token>")
def queue_status(token):

    connection = get_db_connection()

    person = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE token = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (token,)
    ).fetchone()

    current = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE status = 'Serving'
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()

    people_ahead = 0

    if person and person["status"] == "Waiting":

        people_ahead = connection.execute(
            """
            SELECT COUNT(*)
            FROM queue
            WHERE status = 'Waiting'
            AND id < ?
            """,
            (person["id"],)
        ).fetchone()[0]

    connection.close()

    if not person:
        return "Token not found", 404

    return render_template(
        "status.html",
        person=person,
        current=current,
        people_ahead=people_ahead
    )


# -------------------------
# ADMIN LOGIN
# -------------------------

@app.route("/admin")
def admin():

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

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    connection = get_db_connection()

    current = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE status = 'Serving'
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()

    if current:

        connection.execute(
            """
            UPDATE queue
            SET status = 'Served'
            WHERE id = ?
            """,
            (current["id"],)
        )

    next_person = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE status = 'Waiting'
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()

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


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)