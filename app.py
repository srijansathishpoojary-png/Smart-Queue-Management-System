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


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/join", methods=["POST"])
def join_queue():
    name = request.form["name"].strip()

    connection = get_db_connection()

    # Get the number of people currently waiting
    waiting_count = connection.execute(
        "SELECT COUNT(*) FROM queue WHERE status = 'Waiting'"
    ).fetchone()[0]

    # Generate the next token
    token_number = waiting_count + 1
    token = f"A{token_number:03d}"

    # Save the user
    connection.execute(
        "INSERT INTO queue (name, token, status) VALUES (?, ?, ?)",
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


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)