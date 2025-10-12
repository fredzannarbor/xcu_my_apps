# tasks.py
from celery import Celery
from datetime import datetime
import json
import os

# Initialize Celery app
app = Celery('insurance_assessor')
app.config_from_object('celeryconfig')

# File to store user data
DATA_FILE = "user_data.json"

# Load user data from file if it exists
def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Check for updates or adjustments (simplified logic for demo)
def check_for_updates(data):
    last_updated = data.get("last_updated", "")
    if not last_updated or (datetime.now() - datetime.fromisoformat(last_updated)).days > 30:
        return "Data is outdated. Please review and update your information."
    if data.get("income", 0) > 100000 and data.get("dependents", 0) > 2:
        return "Consider increasing life insurance coverage due to high income and dependents."
    if data.get("home_value", 0) > data.get("home_coverage", 0) * 1.2:
        return "Consider increasing home insurance coverage as it may be undervalued compared to home value."
    if data.get("car_value", 0) > data.get("car_coverage", 0) * 1.2:
        return "Consider increasing car insurance coverage as it may be undervalued compared to car value."
    if data.get("personal_property_value", 0) > data.get("personal_property_coverage", 0) * 1.2:
        return "Consider increasing personal property coverage as it may be undervalued compared to property value."
    return "No immediate updates or adjustments needed."

# Check coverage status for monthly updates
def check_coverage_status(data):
    coverage_types = ["life", "health", "home", "car", "personal_property"]
    issues = []
    for coverage in coverage_types:
        exists = data.get(f"{coverage}_coverage_exists", False)
        accessible = data.get(f"{coverage}_coverage_accessible", False)
        paid = data.get(f"{coverage}_coverage_paid", False)
        if not exists:
            issues.append(f"{coverage.capitalize()} insurance does not exist.")
        if not accessible:
            issues.append(f"{coverage.capitalize()} insurance is not accessible online.")
        if not paid:
            issues.append(f"{coverage.capitalize()} insurance premium is not paid.")
    if issues:
        return "Coverage Issues: " + "; ".join(issues)
    return "All coverages are in place, accessible, and paid."

# Check if monthly checklist is due (simplified: once per month)
def is_monthly_checklist_due(data):
    last_checklist = data.get("last_checklist_date", "")
    if not last_checklist:
        return True
    last_date = datetime.fromisoformat(last_checklist)
    return (datetime.now() - last_date).days >= 30

@app.task
def periodic_check():
    data = load_user_data()
    if not data:
        print("No user data found for periodic check.")
        return "No data found."
    update_message = check_for_updates(data)
    if update_message != "No immediate updates or adjustments needed.":
        print(f"Proactive Notification at {datetime.now()}: {update_message}")
        # In a real-world scenario, send an email or other notification here
    return update_message

@app.task
def monthly_coverage_check():
    data = load_user_data()
    if not data or not data.get("initial_assessment_done", False):
        print("No user data or initial assessment not done for monthly coverage check.")
        return "No data or initial assessment not complete."
    if is_monthly_checklist_due(data):
        reminder_message = "Reminder: Monthly coverage checklist is due. Please log in to verify that all recommended coverages exist, are accessible online, and are paid up."
        print(f"Monthly Coverage Reminder at {datetime.now()}: {reminder_message}")
        # In a real-world scenario, send an email or other notification here
        return reminder_message
    else:
        coverage_message = check_coverage_status(data)
        if coverage_message != "All coverages are in place, accessible, and paid.":
            print(f"Monthly Coverage Notification at {datetime.now()}: {coverage_message}")
            # In a real-world scenario, send an email or other notification here
        else:
            print(f"Monthly Coverage Check at {datetime.now()}: All coverages are in good standing based on last checklist.")
        return coverage_message