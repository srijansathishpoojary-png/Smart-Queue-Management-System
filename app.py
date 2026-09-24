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
    name = request.form["name"]

    connection = get_db_connection()

    # Count people already in the queue
    count = connection.execute(
        "SELECT COUNT(*) FROM queue"
    ).fetchone()[0]

    # Generate token
    token_number = count + 1
    token = f"A{token_number:03d}"

    # Save user to database
    connection.execute(
        "INSERT INTO queue (name, token) VALUES (?, ?)",
        (name, token)
    )

    connection.commit()
    connection.close()

    return render_template(
        "index.html",
        token=token,
        name=name
    )


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)