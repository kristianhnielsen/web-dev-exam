import json
from flask import Flask, redirect, render_template, request, session
from supabase import create_client, Client
import dotenv
import secrets

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
        "static",
        "jobs",
    ]  # 'static' for CSS, JS
    if request.endpoint not in allowed_routes and "user" not in session:
        return redirect("/login")


# Route handlers to html files
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/jobs/")
def jobs():
    data = json.load(open("./job_listings.json"))
    return render_template("jobs.html", jobs_data=data)


@app.route("/account")
def profile():
    return "Account Page"


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/sign-up")
def sign_up():
    return "Sign Up Page"


# CRUD logic - should be in a separate file
@app.route("/loginattempt", methods=["POST"])
def login_attempt():
    email = request.form["email"]
    password = request.form["password"]
    result = supabase.auth.sign_in_with_password({"email": email, "password": password})

    if result.session:
        session["user"] = result.session.access_token

        return redirect("/account")
    else:
        return "Login failed", 401


if __name__ == "__main__":
    app.run(debug=True)
