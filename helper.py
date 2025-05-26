import ast
from datetime import datetime, timezone
from flask import session
from supabase import Client


def get_user_data(user_id: str | int, supabase: Client):
    user_data = supabase.table("users").select("*").eq("uuid", user_id).execute()
    return user_data.data[0] if user_data.data else None


def format_job_data(job: dict) -> dict:
    today = datetime.now(timezone.utc)
    date_posted = datetime.fromisoformat(job["created_at"])
    job["days_since_posted"] = (today - date_posted).days
    job["tags"] = ast.literal_eval(job["tags"])
    job["deadline"] = datetime.fromisoformat(job["deadline"]).strftime("%Y-%m-%d")
    job["created_at"] = date_posted.strftime("%Y-%m-%d")
    return job


def get_profile_image_url(user_data: dict | None, supabase: Client):
    if user_data and user_data.get("has_picture"):
        response = supabase.storage.from_("profile-pictures").create_signed_url(
            f"folder/{user_data['uuid']}", 60
        )
        return response["signedURL"]
    return "https://cdn-icons-png.flaticon.com/512/3655/3655713.png"


def is_user_employer(supabase: Client) -> bool:
    user_id = session.get("user")

    if user_id:
        user_data = supabase.table("users").select("*").eq("uuid", user_id).execute()
        user_data = user_data.data[0] if user_data.data else None
        user_employer = user_data.get("is_employer") if user_data else False
        return bool(user_employer)

    return False
