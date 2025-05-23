import ast
from datetime import datetime, timezone
from flask import Flask, redirect, render_template, request, session
from supabase import create_client, Client
import dotenv
import secrets
from collections import Counter


# Load environment variables from .env file

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


# Configuration for Supabase
SUPABASE_URL = dotenv.get_key(".env", "SUPABASE_URL")
SUPABASE_KEY = dotenv.get_key(".env", "SUPABASE_KEY")

if SUPABASE_URL is None or SUPABASE_KEY is None:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# Middleware to require login for all routes except specified ones
@app.before_request
def require_login():
    # Allowed public endpoints (by function name)
    allowed_routes = [
        "index",
        "login",
        "login_attempt",
        "sign_up",
        "signup_attempt",
        "static",
        "jobs",
    ]  # 'static' for CSS, JS
    if request.endpoint not in allowed_routes and "user" not in session:
        return redirect("/login")


# Route handlers to html files
@app.route("/")
def index():
    data = supabase.table("jobposts").select("*").execute()
    data = data.data
    job_types = Counter(job["jobType"] for job in data if "jobType" in job)

    data_sorted_by_latest = sorted(
        data, key=lambda x: x.get("datePosted", ""), reverse=True
    )
    featured_jobs = []
    today = datetime.now(timezone.utc)
    for job in data_sorted_by_latest[:4]:
        date_posted = datetime.fromisoformat(job["datePosted"])
        days_since_posted = (today - date_posted).days
        job["days_since_posted"] = days_since_posted
        job["skillsRequired"] = ast.literal_eval(
            job["skillsRequired"]
        )  # Convert string to list
        featured_jobs.append(job)

    return render_template(
        "index.html",
        jobs_data=data,
        logged_in=("user" in session),
        job_types=job_types,
        featured_jobs=featured_jobs,
    )


@app.route("/jobs", strict_slashes=False)
def jobs():
    data = supabase.table("jobposts").select("*").execute()
    data = data.data
    return render_template("jobs.html", jobs_data=data, logged_in=("user" in session))


@app.route("/account")
def account():
    # Fetch user data from Supabase
    user_id = session.get("user")
    if user_id:
        user_data = supabase.table("users").select("*").eq("uuid", user_id).execute()
        user_data = user_data.data[0] if user_data.data else None
    else:
        user_data = None
    print(f"User data: {user_data}")
    return render_template(
        "account.html", logged_in=("user" in session), user_data=user_data
    )


@app.route("/login")
def login():
    return render_template("login.html", logged_in=("user" in session))


@app.route("/sign_up")
def sign_up():
    return render_template("sign_up.html", logged_in=("user" in session))


@app.route("/post_job")
def post_job():
    return "Post Job Page"


# CRUD logic - should be in a separate file
@app.route("/loginattempt", methods=["POST"])
def login_attempt():
    email = request.form["email"]
    password = request.form["password"]
    result = supabase.auth.sign_in_with_password({"email": email, "password": password})

    if result.session:
        session["user"] = result.session.user.id
        return redirect("/account")
    else:
        return "Login failed", 401


@app.route("/signupattempt", methods=["POST"])
def signup_attempt():
    # Get form data
    is_employer = request.form.get("is_employer", False)
    email = request.form["email"]
    password = request.form["password"]
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    phone_number = request.form["phone"]

    result_signup = supabase.auth.sign_up({"email": email, "password": password})

    if result_signup and result_signup.user:
        supabase.table("users").insert(
            {
                "uuid": result_signup.user.id,
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": phone_number,
                "is_employer": is_employer,
            }
        ).execute()
        session["user"] = result_signup.user.id
        return redirect("/account")
    else:
        return "Sign up failed", 401


@app.route("/edit_account", methods=["POST"])
def edit_account():
    # Get form data
    user_id = session.get("user")
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    phone_number = request.form["phone_number"]

    # Update user data in Supabase
    supabase.table("users").update(
        {
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone_number,
        }
    ).eq("uuid", user_id).execute()

    return redirect("/account")


@app.route("/edit_account_type", methods=["POST"])
def edit_account_type():
    # Get form data
    user_id = session.get("user")
    is_employer = request.form.get("is_employer", False)

    # Update user data in Supabase
    supabase.table("users").update(
        {
            "is_employer": is_employer,
        }
    ).eq("uuid", user_id).execute()

    return redirect("/account")


@app.route("/logout")
def logout():
    supabase.auth.sign_out()
    session.pop("user", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
