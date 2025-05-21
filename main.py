from flask import Flask
from routes.account.account import account_bp
from supabase import create_client, Client
import dotenv
import secrets

# Load environment variables from .env file

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Configuration for Supabase
SUPABASE_URL = dotenv.get_key(".env", "SUPABASE_URL")
SUPABASE_KEY = dotenv.get_key(".env", "SUPABASE_KEY")


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


app.register_blueprint(account_bp)
app.register_blueprint(jobs_bp)


@app.route("/")
def hello_world():
    return "Hello, World!"


if __name__ == "__main__":
    app.run(debug=True)
