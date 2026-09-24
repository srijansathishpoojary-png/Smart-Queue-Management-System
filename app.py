from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3

app = Flask(__name__)

# Secret key for admin login sessions
app.secret_key = "smart_queue_secret_key"


# =========================================
# DATABASE
# =========================================

DATABASE = "database/queue.db"


def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# =========================================
# HOME PAGE
# =========================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================
# JOIN QUEUE
# =========================================

@app.route("/join", methods=["POST"])
def join_queue():

    name = request.form.get("name")

    if not name or not name.strip():

        return render_template(
            "index.html",
            error="Please enter your name."
        )

    name = name.strip()

    connection = get_db_connection()

    # Get the last token number
    last_person = connection.execute(
        """
        SELECT token
        FROM queue
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    if last_person:

        last_token = last_person["token"]

        try:
            last_number = int(
                last_token.replace("A", "")
            )

        except ValueError:

            last_number = 0

    else:

        last_number = 0

    new_number = last_number + 1

    token = f"A{new_number:03d}"

    connection.execute(
        """
        INSERT INTO queue
        (token, name, status)
        VALUES (?, ?, ?)
        """,
        (token, name, "Waiting")
    )

    connection.commit()

    connection.close()

    return redirect(
        url_for(
            "queue_status",
            token=token
        )
    )


# =========================================
# USER QUEUE STATUS
# =========================================

@app.route("/status/<token>")
def queue_status(token):

    connection = get_db_connection()

    person = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE token = ?
        """,
        (token,)
    ).fetchone()

    if not person:

        connection.close()

        return "Token not found", 404


    # Count people ahead
    people_ahead = connection.execute(
        """
        SELECT COUNT(*)
        FROM queue
        WHERE status = 'Waiting'
        AND id < ?
        """,
        (person["id"],)
    ).fetchone()[0]


    # Average service time in minutes
    average_service_time = 5


    # Estimated waiting time
    estimated_wait = (
        people_ahead * average_service_time
    )


    # Currently serving
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
        "status.html",
        person=person,
        people_ahead=people_ahead,
        current=current,
        estimated_wait=estimated_wait
    )


# =========================================
# ADMIN LOGIN
# =========================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username")

        password = request.form.get("password")


        if username == "admin" and password == "admin123":

            session["admin_logged_in"] = True

            return redirect(
                url_for("admin")
            )


        return render_template(
            "admin_login.html",
            error="Invalid username or password."
        )


    return render_template(
        "admin_login.html"
    )


# =========================================
# ADMIN DASHBOARD
# =========================================

@app.route("/admin")
def admin():

    if not session.get("admin_logged_in"):

        return redirect(
            url_for("admin_login")
        )


    connection = get_db_connection()


    # Get complete queue
    queue = connection.execute(
        """
        SELECT *
        FROM queue
        ORDER BY id ASC
        """
    ).fetchall()


    # Currently serving
    current = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE status = 'Serving'
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()


    # Total people
    total_people = connection.execute(
        """
        SELECT COUNT(*)
        FROM queue
        """
    ).fetchone()[0]


    # Waiting people
    waiting_people = connection.execute(
        """
        SELECT COUNT(*)
        FROM queue
        WHERE status = 'Waiting'
        """
    ).fetchone()[0]


    # Serving people
    serving_people = connection.execute(
        """
        SELECT COUNT(*)
        FROM queue
        WHERE status = 'Serving'
        """
    ).fetchone()[0]


    # Served people
    served_people = connection.execute(
        """
        SELECT COUNT(*)
        FROM queue
        WHERE status = 'Served'
        """
    ).fetchone()[0]


    connection.close()


    return render_template(
        "admin.html",
        queue=queue,
        current=current,
        total_people=total_people,
        waiting_people=waiting_people,
        serving_people=serving_people,
        served_people=served_people
    )


# =========================================
# CALL NEXT
# =========================================

@app.route("/admin/next", methods=["POST"])
def admin_next():

    if not session.get("admin_logged_in"):

        return redirect(
            url_for("admin_login")
        )


    connection = get_db_connection()


    # Mark currently serving person as served
    connection.execute(
        """
        UPDATE queue
        SET status = 'Served'
        WHERE status = 'Serving'
        """
    )


    # Find next waiting person
    next_person = connection.execute(
        """
        SELECT id
        FROM queue
        WHERE status = 'Waiting'
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()


    # Make next person the serving person
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

    connection.close()


    return redirect(
        url_for("admin")
    )


# =========================================
# ADMIN LOGOUT
# =========================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


# =========================================
# PUBLIC QUEUE DISPLAY
# =========================================

@app.route("/display")
def public_display():

    return render_template(
        "display.html"
    )


# =========================================
# PUBLIC DISPLAY API
# =========================================

@app.route("/api/display")
def display_status():

    connection = get_db_connection()


    # Currently serving
    current = connection.execute(
        """
        SELECT token, name
        FROM queue
        WHERE status = 'Serving'
        ORDER BY id ASC
        LIMIT 1
        """
    ).fetchone()


    # Number of people waiting
    waiting_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM queue
        WHERE status = 'Waiting'
        """
    ).fetchone()[0]


    connection.close()


    return jsonify({

        "current_token":
            current["token"]
            if current
            else None,

        "current_name":
            current["name"]
            if current
            else None,

        "waiting_count":
            waiting_count

    })


# =========================================
# QUEUE HISTORY
# =========================================

@app.route("/admin/history")
def admin_history():

    if not session.get("admin_logged_in"):

        return redirect(
            url_for("admin_login")
        )


    connection = get_db_connection()


    history = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE status = 'Served'
        ORDER BY id DESC
        """
    ).fetchall()


    connection.close()


    return render_template(
        "history.html",
        history=history
    )


# =========================================
# CANCEL QUEUE
# =========================================

@app.route("/cancel/<token>", methods=["POST"])
def cancel_queue(token):

    connection = get_db_connection()


    person = connection.execute(
        """
        SELECT *
        FROM queue
        WHERE token = ?
        """,
        (token,)
    ).fetchone()


    if not person:

        connection.close()

        return "Token not found", 404


    # Only waiting users can cancel
    if person["status"] == "Waiting":

        connection.execute(
            """
            UPDATE queue
            SET status = 'Cancelled'
            WHERE token = ?
            """,
            (token,)
        )

        connection.commit()


    connection.close()


    return redirect(
        url_for(
            "queue_status",
            token=token
        )
    )


# =========================================
# RUN APPLICATION
# =========================================

if __name__ == "__main__":

    app.run(
        debug=True
    )