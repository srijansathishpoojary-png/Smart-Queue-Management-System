import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from supabase import create_client, Client


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

# Use an environment variable in production.
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "smart_queue_secret_key"
)


# =========================================================
# SUPABASE CONFIGURATION
# =========================================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SECRET_KEY")

if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL environment variable is not configured."
    )

if not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_SECRET_KEY environment variable is not configured."
    )


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_queue():
    """
    Return the complete queue ordered by ID.
    """

    response = (
        supabase
        .table("queue")
        .select("*")
        .order("id", desc=False)
        .execute()
    )

    return response.data or []


def get_person_by_token(token):
    """
    Find a queue person by token.
    """

    response = (
        supabase
        .table("queue")
        .select("*")
        .eq("token", token)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def get_current_serving():
    """
    Return the first currently serving person.
    """

    response = (
        supabase
        .table("queue")
        .select("*")
        .eq("status", "Serving")
        .order("id", desc=False)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def get_waiting_people():
    """
    Return all waiting people in queue order.
    """

    response = (
        supabase
        .table("queue")
        .select("*")
        .eq("status", "Waiting")
        .order("id", desc=False)
        .execute()
    )

    return response.data or []


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# JOIN QUEUE
# =========================================================

@app.route("/join", methods=["POST"])
def join_queue():

    name = request.form.get("name", "").strip()

    if not name:

        return render_template(
            "index.html",
            error="Please enter your name."
        )


    try:

        # -------------------------------------------------
        # Insert first so Postgres generates the ID.
        # -------------------------------------------------

        insert_response = (
            supabase
            .table("queue")
            .insert({
                "name": name,
                "status": "Waiting"
            })
            .select("id")
            .execute()
        )

        if not insert_response.data:

            return render_template(
                "index.html",
                error="Unable to join the queue. Please try again."
            )


        row_id = insert_response.data[0]["id"]


        # -------------------------------------------------
        # Generate token from the database ID.
        #
        # Example:
        # 1  -> A001
        # 12 -> A012
        # 105 -> A105
        # -------------------------------------------------

        token = f"A{int(row_id):03d}"


        # -------------------------------------------------
        # Save token.
        # -------------------------------------------------

        supabase \
            .table("queue") \
            .update({
                "token": token
            }) \
            .eq("id", row_id) \
            .execute()


        return redirect(
            url_for(
                "queue_status",
                token=token
            )
        )


    except Exception as error:

        print(
            "JOIN QUEUE ERROR:",
            error
        )

        return render_template(
            "index.html",
            error="Unable to join the queue. Please try again."
        )


# =========================================================
# USER QUEUE STATUS
# =========================================================

@app.route("/status/<token>")
def queue_status(token):

    try:

        person = get_person_by_token(token)

        if not person:

            return "Token not found", 404


        # -------------------------------------------------
        # People ahead of this person
        # -------------------------------------------------

        response = (
            supabase
            .table("queue")
            .select("id")
            .eq("status", "Waiting")
            .lt("id", person["id"])
            .execute()
        )

        people_ahead = len(
            response.data or []
        )


        # -------------------------------------------------
        # Average service time
        # -------------------------------------------------

        average_service_time = 5


        # -------------------------------------------------
        # Estimated waiting time
        # -------------------------------------------------

        estimated_wait = (
            people_ahead *
            average_service_time
        )


        # -------------------------------------------------
        # Currently serving
        # -------------------------------------------------

        current = get_current_serving()


        return render_template(
            "status.html",
            person=person,
            people_ahead=people_ahead,
            current=current,
            estimated_wait=estimated_wait
        )


    except Exception as error:

        print(
            "STATUS ERROR:",
            error
        )

        return "Unable to load queue status.", 500


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        # -------------------------------------------------
        # Current project admin credentials
        # -------------------------------------------------

        admin_username = os.environ.get(
            "ADMIN_USERNAME",
            "admin"
        )

        admin_password = os.environ.get(
            "ADMIN_PASSWORD",
            "admin123"
        )


        if (
            username == admin_username
            and password == admin_password
        ):

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


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    try:

        # -------------------------------------------------
        # Complete queue
        # -------------------------------------------------

        queue = get_queue()


        # -------------------------------------------------
        # Currently serving
        # -------------------------------------------------

        current = get_current_serving()


        # -------------------------------------------------
        # Statistics
        # -------------------------------------------------

        total_people = len(queue)

        waiting_people = len([
            person
            for person in queue
            if person["status"] == "Waiting"
        ])

        serving_people = len([
            person
            for person in queue
            if person["status"] == "Serving"
        ])

        served_people = len([
            person
            for person in queue
            if person["status"] == "Served"
        ])


        return render_template(
            "admin.html",
            queue=queue,
            current=current,
            total_people=total_people,
            waiting_people=waiting_people,
            serving_people=serving_people,
            served_people=served_people
        )


    except Exception as error:

        print(
            "ADMIN ERROR:",
            error
        )

        return (
            "Unable to load admin dashboard.",
            500
        )


# =========================================================
# CALL NEXT
# =========================================================

@app.route(
    "/admin/next",
    methods=["POST"]
)
def admin_next():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    try:

        # -------------------------------------------------
        # Mark current serving person as served.
        # -------------------------------------------------

        supabase \
            .table("queue") \
            .update({
                "status": "Served"
            }) \
            .eq("status", "Serving") \
            .execute()


        # -------------------------------------------------
        # Find next waiting person.
        # -------------------------------------------------

        response = (
            supabase
            .table("queue")
            .select("id")
            .eq("status", "Waiting")
            .order("id", desc=False)
            .limit(1)
            .execute()
        )


        if response.data:

            next_id = response.data[0]["id"]


            # -------------------------------------------------
            # Make next person the serving person.
            # -------------------------------------------------

            supabase \
                .table("queue") \
                .update({
                    "status": "Serving"
                }) \
                .eq("id", next_id) \
                .execute()


        return redirect(
            url_for("admin")
        )


    except Exception as error:

        print(
            "CALL NEXT ERROR:",
            error
        )

        return (
            "Unable to call next person.",
            500
        )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(
        url_for("admin_login")
    )


# =========================================================
# PUBLIC QUEUE DISPLAY
# =========================================================

@app.route("/display")
def public_display():

    return render_template(
        "display.html"
    )


# =========================================================
# PUBLIC DISPLAY API
# =========================================================

@app.route("/api/display")
def display_status():

    try:

        # -------------------------------------------------
        # Currently serving
        # -------------------------------------------------

        current = get_current_serving()


        # -------------------------------------------------
        # Waiting count
        # -------------------------------------------------

        waiting_response = (
            supabase
            .table("queue")
            .select("id")
            .eq("status", "Waiting")
            .execute()
        )

        waiting_count = len(
            waiting_response.data or []
        )


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


    except Exception as error:

        print(
            "DISPLAY API ERROR:",
            error
        )

        return jsonify({

            "current_token": None,
            "current_name": None,
            "waiting_count": 0,
            "error": "Unable to load queue."
        }), 500


# =========================================================
# QUEUE HISTORY
# =========================================================

@app.route("/admin/history")
def admin_history():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    try:

        response = (
            supabase
            .table("queue")
            .select("*")
            .eq("status", "Served")
            .order("id", desc=True)
            .execute()
        )

        history = response.data or []


        return render_template(
            "history.html",
            history=history
        )


    except Exception as error:

        print(
            "HISTORY ERROR:",
            error
        )

        return (
            "Unable to load queue history.",
            500
        )


# =========================================================
# CANCEL QUEUE
# =========================================================

@app.route(
    "/cancel/<token>",
    methods=["POST"]
)
def cancel_queue(token):

    try:

        person = get_person_by_token(token)


        if not person:

            return "Token not found", 404


        # -------------------------------------------------
        # Only waiting users can cancel.
        # -------------------------------------------------

        if person["status"] == "Waiting":

            (
                supabase
                .table("queue")
                .update({
                    "status": "Cancelled"
                })
                .eq("token", token)
                .execute()
            )


        return redirect(
            url_for(
                "queue_status",
                token=token
            )
        )


    except Exception as error:

        print(
            "CANCEL ERROR:",
            error
        )

        return (
            "Unable to cancel queue.",
            500
        )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    try:

        response = (
            supabase
            .table("queue")
            .select("id")
            .limit(1)
            .execute()
        )

        return jsonify({
            "status": "ok",
            "database": "supabase"
        })


    except Exception as error:

        print(
            "HEALTH CHECK ERROR:",
            error
        )

        return jsonify({
            "status": "error",
            "database": "supabase"
        }), 500


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )