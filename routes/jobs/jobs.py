from flask import Blueprint, render_template, jsonify
import json


jobs_bp = Blueprint("jobs", __name__, url_prefix="/jobs", template_folder="templates")


@jobs_bp.route("/")
def jobs():
    data = json.load(open("routes/jobs/job_listings.json"))
    return render_template("index.html", jobs_data=data, job=data)


@jobs_bp.route("/<int:job_id>")
def job_detail(job_id):
    return f"Job Detail Page for Job ID: {job_id}"


@jobs_bp.route("/apply/<int:job_id>")
def apply_job(job_id):
    return f"Apply for Job ID: {job_id}"


@jobs_bp.route("/search")
def search_jobs():
    return "Search Jobs Page"
