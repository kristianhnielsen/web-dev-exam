from flask import Blueprint


account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.route("/")
def profile():
    return "Account Page"


@account_bp.route("/login")
def login():
    return "Login Page"


@account_bp.route("/sign-up")
def sign_up():
    return "Sign Up Page"
