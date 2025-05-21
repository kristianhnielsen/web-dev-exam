from flask import Blueprint
from flask import render_template
from flask import redirect, request, session
from supabase import create_client, Client
import dotenv

account_bp = Blueprint("account", __name__, url_prefix="/account")

# Configuration for Supabase
SUPABASE_URL = dotenv.get_key(".env", "SUPABASE_URL")
SUPABASE_KEY = dotenv.get_key(".env", "SUPABASE_KEY")


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@account_bp.route("/")
def profile():
    return "Account Page"


@account_bp.route("/login")
def login():
    return render_template("login.html")


@account_bp.route("/loginattempt", methods=["POST"])
def login_attempt():
    email = request.form["email"]
    password = request.form["password"]
    result = supabase.auth.sign_in_with_password({"email": email, "password": password})

    if result.session:
        session["user"] = result.session.access_token
        return redirect("/Account/")
    else:
        return "Login failed", 401


@account_bp.route("/sign-up")
def sign_up():
    return "Sign Up Page"
