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
        "job_details",
        "about",
    ]  # 'static' for CSS, JS
    if request.endpoint not in allowed_routes and "user" not in session:
        return redirect("/login")


# Route handlers to html files
@app.route("/")
def index():
    data = supabase.table("jobposts").select("*").execute()
    data = data.data
    job_types = Counter(job["type"] for job in data if "type" in job)

    data_sorted_by_latest = sorted(
        data, key=lambda x: x.get("created_at", ""), reverse=True
    )
    featured_jobs = []
    today = datetime.now(timezone.utc)
    for job in data_sorted_by_latest[:4]:
        date_posted = datetime.fromisoformat(job["created_at"])
        days_since_posted = (today - date_posted).days
        job["days_since_posted"] = days_since_posted
        job["tags"] = ast.literal_eval(job["tags"])  # Convert string to list
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

    today = datetime.now(timezone.utc)
    for job in data:
        today = datetime.now(timezone.utc)
        date_posted = datetime.fromisoformat(job["created_at"])
        days_since_posted = (today - date_posted).days
        job["days_since_posted"] = days_since_posted
        job["tags"] = ast.literal_eval(job["tags"])  # Convert string to list
        job["deadline"] = datetime.fromisoformat(job["deadline"]).strftime("%Y-%m-%d")
        job["created_at"] = datetime.fromisoformat(job["created_at"]).strftime(
            "%Y-%m-%d"
        )

    # Check if the user is an employer
    user_id = session.get("user")
    user_employer = False
    if user_id:
        user_data = supabase.table("users").select("*").eq("uuid", user_id).execute()
        user_data = user_data.data[0] if user_data.data else None
        user_employer = user_data.get("is_employer") if user_data else False

    return render_template(
        "jobs.html",
        jobs_data=data,
        user_employer=user_employer,
        logged_in=("user" in session),
    )


@app.route("/jobs/<int:job_id>", strict_slashes=False)
def job_details(job_id):
    job_data = supabase.table("jobposts").select("*").eq("id", job_id).execute()
    job_data = job_data.data[0] if job_data.data else None

    if job_data:
        today = datetime.now(timezone.utc)
        date_posted = datetime.fromisoformat(job_data["created_at"])
        days_since_posted = (today - date_posted).days
        job_data["days_since_posted"] = days_since_posted
        job_data["tags"] = ast.literal_eval(job_data["tags"])  # Convert string to list
        job_data["deadline"] = datetime.fromisoformat(job_data["deadline"]).strftime(
            "%Y-%m-%d"
        )
        job_data["created_at"] = datetime.fromisoformat(
            job_data["created_at"]
        ).strftime("%Y-%m-%d")

    return render_template(
        "job_details.html",
        job=job_data,
        logged_in=("user" in session),
    )


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
    response = None

    if user_data and user_data.get("has_picture") is True:
        response = supabase.storage.from_("profile-pictures").create_signed_url(
            f"folder/{user_data['id']}", 60
        )
    else:
        response = {
            "signedURL": "https://cdn-icons-png.flaticon.com/512/3655/3655713.png"
        }

    return render_template(
        "account.html",
        logged_in=("user" in session),
        user_data=user_data,
        image_url=response["signedURL"],
    )


@app.route("/about")
def about():
    team_members = [
        {
            "name": "Kristian Hviid Nielsen",
            "role": "CEO & Co-Founder",
            "image_url": "https://cdn-icons-png.flaticon.com/512/3655/3655713.png",
            "responsibilities": ["Styling", "Frontend", "UX", "Deployment"],
        },
        {
            "name": "Lasse Lotzkat Thorsen",
            "role": "CTO & Co-Founder",
            "image_url": "https://cdn-icons-png.flaticon.com/512/3655/3655713.png",
            "responsibilities": ["Backend", "Database", "Authentication"],
        },
    ]
    return render_template(
        "about.html", logged_in=("user" in session), team_members=team_members
    )


@app.route("/login")
def login():
    return render_template("login.html", logged_in=("user" in session))


@app.route("/sign_up")
def sign_up():
    return render_template("sign_up.html", logged_in=("user" in session))


@app.route("/post_job")
def post_job():
    return render_template(
        "post_job.html",
        logged_in=("user" in session),
    )


@app.route("/post_job_attempt", methods=["POST"])
def post_job_attempt():
    # get id from users table in supabase
    # Get user ID from session
    user_id = session.get("user")
    user_row = supabase.table("users").select("id").eq("uuid", user_id).execute()
    user_id = user_row.data[0]["id"] if user_row.data else None
    # Get form data
    title = request.form["title"]
    description = request.form["description"]
    job_type = request.form["type"]
    tags = request.form["tags"]
    # Convert comma-separated string to list and strip whitespace
    tags = [skill.strip() for skill in tags.split(",") if skill.strip()]
    deadline = request.form["deadline"]
    company_email = request.form["company_email"]
    company = request.form["company"]
    location = request.form["location"]
    duration = request.form["duration"]
    status = request.form["status"]
    basis = request.form["basis"]
    currency = request.form["currency"]
    salary = request.form["salary"]

    # Insert job post into Supabase
    supabase.table("jobposts").insert(
        {
            "title": title,
            "description": description,
            "type": job_type,
            "tags": tags,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "UserID": user_id,
            "deadline": deadline,
            "company_email": company_email,
            "company": company,
            "location": location,
            "duration": duration,
            "status": status,
            "basis": basis,
            "currency": currency,
            "salary": salary,
        }
    ).execute()

    return redirect("/jobs")


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
    # get image upload from form
    image = request.files["profile_image"]

    result_signup = supabase.auth.sign_up({"email": email, "password": password})

    if result_signup and result_signup.user:
        supabase.table("users").insert(
            {
                "uuid": result_signup.user.id,
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": phone_number,
                "is_employer": is_employer,
                "has_picture": False,
            }
        ).execute()
        session["user"] = result_signup.user.id
        # Upload image to Supabase storage
        if image:
            # Upload the image to Supabase storage
            file_path = f"folder/{result_signup.user.id}"
            image_bytes = image.read()
            supabase.storage.from_("profile-pictures").upload(file_path, image_bytes)

            # Update the user record to indicate that the user has a profile picture
            supabase.table("users").update({"has_picture": True}).eq(
                "uuid", result_signup.user.id
            ).execute()
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
