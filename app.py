from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

DATABASE = "database/queue.db"


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

    # Find the highest token number that has ever been created
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

    connection.execute(
        """
        INSERT INTO queue (name, token, status)
        VALUES (?, ?, ?)
        """,
        (name, token, "Waiting")
    )

    connection.commit()

    # Find the newly created user's position
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
# ADMIN DASHBOARD
# -------------------------

@app.route("/admin")
def admin():

    connection = get_db_connection()

    queue = connection.execute(
        """
        SELECT *
        FROM queue
        ORDER BY id ASC
        """
    ).fetchall()

    # Find the person currently being served
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
# CALL NEXT
# -------------------------

@app.route("/admin/next", methods=["POST"])
def call_next():

    connection = get_db_connection()

    # Check whether someone is already being served
    current = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE status = 'Serving'
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()

    # If someone is currently being served,
    # mark them as Served first.
    if current:

        connection.execute(
            """
            UPDATE queue
            SET status = 'Served'
            WHERE id = ?
            """,
            (current["id"],)
        )

    # Find the next waiting person
    next_person = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE status = 'Waiting'
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()

    # Make the next person the current person
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

    # Get current person
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