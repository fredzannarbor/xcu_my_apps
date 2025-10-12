# insurance_assessor.py
import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

# Initialize OpenAI client
load_dotenv()
client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

# File to store user data
DATA_FILE = "user_data.json"

# Required fields for insurance assessment (core fields for initial assessment)
REQUIRED_FIELDS = [
    "name", "age", "income", "dependents", "health_status", "assets", "liabilities",
    "home_value", "home_coverage", "car_value", "car_coverage",
    "personal_property_value", "personal_property_coverage", "misc_info", "specific_concerns"
]

# Additional fields for tracking coverage status after initial assessment
# Additional fields for tracking coverage status after initial assessment
COVERAGE_FIELDS = [
    "life_coverage_exists", "life_coverage_accessible", "life_coverage_paid", "life_coverage_claims_open",
    "life_coverage_comments", "life_coverage_provider", "life_coverage_url",
    "health_coverage_exists", "health_coverage_accessible", "health_coverage_paid", "health_coverage_claims_open",
    "health_coverage_comments", "health_coverage_provider", "health_coverage_url",
    "home_coverage_exists", "home_coverage_accessible", "home_coverage_paid", "home_coverage_claims_open",
    "home_coverage_comments", "home_coverage_provider", "home_coverage_url",
    "car_coverage_exists", "car_coverage_accessible", "car_coverage_paid", "car_coverage_claims_open",
    "car_coverage_comments", "car_coverage_provider", "car_coverage_url",
    "personal_property_coverage_exists", "personal_property_coverage_accessible", "personal_property_coverage_paid",
    "personal_property_coverage_claims_open", "personal_property_coverage_comments",
    "personal_property_coverage_provider", "personal_property_coverage_url"
]


# Load user data from file if it exists
def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


# Save user data to file
def save_user_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# Check if data is complete for initial assessment
def is_data_complete(data):
    core_fields = [f for f in REQUIRED_FIELDS if f not in ["misc_info", "specific_concerns"]]
    return all(field in data and data[field] is not None for field in core_fields) and \
        all(field in data for field in ["misc_info", "specific_concerns"])


# Get initial insurance assessment from LLM
def get_insurance_assessment(data):
    prompt = f"""
    Assess the insurance needs for the following user:
    Name: {data.get('name', 'N/A')}
    Age: {data.get('age', 'N/A')}
    Annual Income: {data.get('income', 'N/A')}
    Dependents: {data.get('dependents', 'N/A')}
    Health Status: {data.get('health_status', 'N/A')}
    Assets: {data.get('assets', 'N/A')}
    Liabilities: {data.get('liabilities', 'N/A')}
    Home Value ($): {data.get('home_value', 'N/A')}
    Home Insurance Coverage ($): {data.get('home_coverage', 'N/A')}
    Car Value ($): {data.get('car_value', 'N/A')}
    Car Insurance Coverage ($): {data.get('car_coverage', 'N/A')}
    Personal Property Value ($): {data.get('personal_property_value', 'N/A')}
    Personal Property Coverage ($): {data.get('personal_property_coverage', 'N/A')}
    Miscellaneous Information: {data.get('misc_info', 'N/A')}
    Specific Concerns: {data.get('specific_concerns', 'N/A')}

    Provide recommendations for life, health, property, home, car, and personal property insurance coverage.
    Additionally, include a separate section titled 'Possibly Unnoticed Issues' to highlight potential risks or gaps 
    in coverage that the user may not have considered, based on all provided information.

    Escape dollar signs with a backslash.
    """
    try:
        response = client.chat.completions.create(
            model="grok-3-latest",
            messages=[
                {"role": "system", "content": "You are an expert insurance advisor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=6000
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error fetching assessment: {str(e)}"


# Get summary of assessment from LLM (5-7 bullet points)
def get_assessment_summary(assessment):
    if not assessment or "No assessment available" in assessment:
        return "No summary available. Please complete an assessment."

    prompt = f"""
    Summarize the following insurance assessment into 3-5 bullet points focusing on the key recommendations 
    for life, health, property, home, car, and personal property insurance coverage, as well as any critical 
    unnoticed issues. Ensure the bullet points are concise and actionable and do not include any explanations.  Make sure any unusual or critical issues are included.  Format the output as markdown-only bullet points, no LaTex, and starting with '-'. No font changes for numerals. Escape dollar signs with a backslash.

    Assessment Text:
    {assessment}


    """
    try:
        response = client.chat.completions.create(
            model="grok-3-latest",
            messages=[
                {"role": "system", "content": "You are an expert in summarizing insurance assessments."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error fetching summary: {str(e)}"


# Check for updates or adjustments (used in Streamlit display)
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


# Check if monthly checklist is due (simplified: once per month)
def is_monthly_checklist_due(data):
    last_checklist = data.get("last_checklist_date", "")
    if not last_checklist:
        return True
    last_date = datetime.fromisoformat(last_checklist)
    return (datetime.now() - last_date).days >= 30


# Streamlit App Interface
def main():
    st.title("Insurance Needs Assessment Tool")
    user_data = load_user_data()
    initial_assessment_done = user_data.get("initial_assessment_done", False)

    if not initial_assessment_done:
        st.write(
            "Enter your information to assess your insurance needs. Data will be periodically reviewed for updates.")
        st.write("Background tasks are managed by Celery for periodic checks after the initial assessment.")
        gather_initial_data(user_data)
    else:
        st.write("Your initial assessment is complete. Review the summary and update information as needed.")
        st.write("Monthly checklists are required to verify coverage status.")
        display_assessment_and_updates(user_data)


def gather_initial_data(user_data):
    with st.form("user_info_form"):
        st.subheader("Personal Information")
        user_data["name"] = st.text_input("Full Name", value=user_data.get("name", ""))
        user_data["age"] = st.number_input("Age", min_value=18, max_value=100, value=int(user_data.get("age", 30)))
        user_data["income"] = st.number_input("Annual Income ($)", min_value=0, value=int(user_data.get("income", 0)))
        user_data["dependents"] = st.number_input("Number of Dependents", min_value=0,
                                                  value=int(user_data.get("dependents", 0)))
        user_data["health_status"] = st.selectbox("Health Status", ["Good", "Average", "Poor"],
                                                  index=["Good", "Average", "Poor"].index(
                                                      user_data.get("health_status", "Good")))

        st.subheader("Financial Information")
        user_data["assets"] = st.number_input("Total Assets ($)", min_value=0, value=int(user_data.get("assets", 0)))
        user_data["liabilities"] = st.number_input("Total Liabilities ($)", min_value=0,
                                                   value=int(user_data.get("liabilities", 0)))

        st.subheader("Property Information")
        user_data["home_value"] = st.number_input("Home Value ($)", min_value=0,
                                                  value=int(user_data.get("home_value", 0)))
        user_data["home_coverage"] = st.number_input("Home Insurance Coverage ($)", min_value=0,
                                                     value=int(user_data.get("home_coverage", 0)))
        user_data["car_value"] = st.number_input("Car Value ($)", min_value=0, value=int(user_data.get("car_value", 0)))
        user_data["car_coverage"] = st.number_input("Car Insurance Coverage ($)", min_value=0,
                                                    value=int(user_data.get("car_coverage", 0)))
        user_data["personal_property_value"] = st.number_input("Personal Property Value ($)", min_value=0,
                                                               value=int(user_data.get("personal_property_value", 0)))
        user_data["personal_property_coverage"] = st.number_input("Personal Property Insurance Coverage ($)",
                                                                  min_value=0, value=int(
                user_data.get("personal_property_coverage", 0)))

        st.subheader("Miscellaneous Information and Concerns")
        user_data["misc_info"] = st.text_area("Additional Information (e.g., lifestyle, hobbies, risks, etc.)",
                                              value=user_data.get("misc_info", ""),
                                              help="Provide any additional context that might affect your insurance needs.")
        user_data["specific_concerns"] = st.text_area(
            "Specific Insurance Concerns (e.g., flood risk, medical conditions, etc.)",
            value=user_data.get("specific_concerns", ""),
            help="Detail any specific worries or areas you want addressed.")

        submitted = st.form_submit_button("Submit and Assess")

    if submitted:
        user_data["last_updated"] = datetime.now().isoformat()
        if is_data_complete(user_data):
            st.success("Data is complete. Generating insurance assessment...")
            assessment = get_insurance_assessment(user_data)
            user_data["initial_assessment_done"] = True
            user_data["initial_assessment"] = assessment
            # Initialize coverage status fields assuming user will set them post-assessment
            for field in COVERAGE_FIELDS:
                if field not in user_data:
                    user_data[field] = False if "comments" not in field else ""
            save_user_data(user_data)
            st.subheader("Insurance Needs Assessment")
            st.write(assessment)
        else:
            core_fields = [f for f in REQUIRED_FIELDS if f not in ["misc_info", "specific_concerns"]]
            missing = [field for field in core_fields if field not in user_data or user_data[field] is None]
            st.error(f"Please complete the following fields: {', '.join(missing)}")

    # Display current data status
    if user_data:
        st.subheader("Current Data Status")
        st.write(f"Last Updated: {user_data.get('last_updated', 'Never')}")
        update_message = check_for_updates(user_data)
        if update_message != "No immediate updates or adjustments needed.":
            st.warning(update_message)


# Helper function to check if checklist is completed for the current month
# Helper function to check if checklist is completed for the current month
def is_checklist_completed_for_current_month(data, current_date=None):
    last_checklist = data.get("last_checklist_date", "")
    if not last_checklist:
        return False
    last_date = datetime.fromisoformat(last_checklist)
    if current_date is None:
        current_date = datetime.now()
    print(last_date, current_date)
    return (last_date.year == current_date.year) and (last_date.month == current_date.month)

# Helper function to check if it is the first day of the month
def is_first_of_month():
    return datetime.now().day == 1

# Updated display_assessment_and_updates function
def display_assessment_and_updates(user_data):
    current_date = datetime.now()
    checklist_completed = is_checklist_completed_for_current_month(user_data)
    first_of_month = is_first_of_month()

    # Reset checklist status if it's the first of the month and the last checklist was from a previous month
    if first_of_month and not checklist_completed:
        user_data["last_checklist_date"] = ""  # Reset to force checklist completion
        save_user_data(user_data)
        st.warning("It's the first of the month. Your monthly coverage checklist is required. Please complete it below to verify your insurance status.")

    # Check if monthly checklist is due (always due on the first, or if not completed for current month)
    checklist_due = first_of_month or not checklist_completed

    if checklist_due:
        st.warning("Your monthly coverage checklist is due. Please complete it below to verify your insurance status.")
    else:
        st.success("Your monthly checklist for this month is complete. See the status report below.")

    with st.expander("Recommended Insurances Summary"):
        assessment = user_data.get("initial_assessment", "No assessment available.")
        summary = get_assessment_summary(assessment)
        st.markdown(summary)

    # Detailed Assessment Report in Expander (always visible)
    with st.expander("Detailed Assessment Report"):
        st.write(assessment)

    # Update Information Button (always visible)
    st.subheader("Update Information")
    update_clicked = st.button("Update Info and Reassess")

    if update_clicked:
        with st.form("update_info_form"):
            st.subheader("Personal Information (Update if Necessary)")
            user_data["name"] = st.text_input("Full Name", value=user_data.get("name", ""))
            user_data["age"] = st.number_input("Age", min_value=18, max_value=100, value=int(user_data.get("age", 30)))
            user_data["income"] = st.number_input("Annual Income ($)", min_value=0,
                                                  value=int(user_data.get("income", 0)))
            user_data["dependents"] = st.number_input("Number of Dependents", min_value=0,
                                                      value=int(user_data.get("dependents", 0)))
            user_data["health_status"] = st.selectbox("Health Status", ["Good", "Average", "Poor"],
                                                      index=["Good", "Average", "Poor"].index(
                                                          user_data.get("health_status", "Good")))

            st.subheader("Financial Information (Update if Necessary)")
            user_data["assets"] = st.number_input("Total Assets ($)", min_value=0,
                                                  value=int(user_data.get("assets", 0)))
            user_data["liabilities"] = st.number_input("Total Liabilities ($)", min_value=0,
                                                       value=int(user_data.get("liabilities", 0)))

            st.subheader("Property Information (Update if Necessary)")
            user_data["home_value"] = st.number_input("Home Value ($)", min_value=0,
                                                      value=int(user_data.get("home_value", 0)))
            user_data["home_coverage"] = st.number_input("Home Insurance Coverage ($)", min_value=0,
                                                         value=int(user_data.get("home_coverage", 0)))
            user_data["car_value"] = st.number_input("Car Value ($)", min_value=0,
                                                     value=int(user_data.get("car_value", 0)))
            user_data["car_coverage"] = st.number_input("Car Insurance Coverage ($)", min_value=0,
                                                        value=int(user_data.get("car_coverage", 0)))
            user_data["personal_property_value"] = st.number_input("Personal Property Value ($)", min_value=0,
                                                                   value=int(
                                                                       user_data.get("personal_property_value", 0)))
            user_data["personal_property_coverage"] = st.number_input("Personal Property Insurance Coverage ($)",
                                                                      min_value=0, value=int(
                    user_data.get("personal_property_coverage", 0)))

            st.subheader("Miscellaneous Information and Concerns (Update if Necessary)")
            user_data["misc_info"] = st.text_area("Additional Information (e.g., lifestyle, hobbies, risks, etc.)",
                                                  value=user_data.get("misc_info", ""),
                                                  help="Provide any additional context that might affect your insurance needs.")
            user_data["specific_concerns"] = st.text_area(
                "Specific Insurance Concerns (e.g., flood risk, medical conditions, etc.)",
                value=user_data.get("specific_concerns", ""),
                help="Detail any specific worries or areas you want addressed.")

            submitted = st.form_submit_button("Submit Updated Information and Reassess")

        if submitted:
            user_data["last_updated"] = datetime.now().isoformat()
            if is_data_complete(user_data):
                st.success("Data is complete. Generating insurance assessment...")
                assessment = get_insurance_assessment(user_data)
                user_data["initial_assessment_done"] = True
                user_data["initial_assessment"] = assessment
                # Initialize coverage status fields assuming user will set them post-assessment
                for field in COVERAGE_FIELDS:
                    if field not in user_data:
                        user_data[
                            field] = False if "comments" not in field and "provider" not in field and "url" not in field else ""
                save_user_data(user_data)
                st.subheader("Insurance Needs Assessment")
                st.write(assessment)
            else:
                core_fields = [f for f in REQUIRED_FIELDS if f not in ["misc_info", "specific_concerns"]]
                missing = [field for field in core_fields if field not in user_data or user_data[field] is None]
                st.error(f"Please complete the following fields: {', '.join(missing)}")
    # Display Monthly Checklist only if it's due (first of the month or not completed for current month)
    # Inside display_assessment_and_updates function, modify the checklist section if checklist_due is True
    if checklist_due:
        st.subheader("Monthly Coverage Checklist")
        st.write("Please verify the status of your recommended coverages. This is required monthly.")
        with st.form("monthly_checklist_form"):
            st.write("Update the status of your insurance coverages in the table below:")
            coverage_types = ["Life", "Health", "Home", "Car", "Personal Property"]
            # Create a DataFrame for the checklist data with new Provider and URL columns
            checklist_df = pd.DataFrame([
                {
                    "Coverage Type": coverage,
                    "Exists": user_data.get(f"{coverage.lower().replace(' ', '_')}_coverage_exists", False),
                    "Accessible Online": user_data.get(f"{coverage.lower().replace(' ', '_')}_coverage_accessible",
                                                       False),
                    "Paid Up": user_data.get(f"{coverage.lower().replace(' ', '_')}_coverage_paid", False),
                    "Claims Open": user_data.get(f"{coverage.lower().replace(' ', '_')}_coverage_claims_open", False),
                    "Comments": user_data.get(f"{coverage.lower().replace(' ', '_')}_coverage_comments", ""),
                    "Provider": user_data.get(f"{coverage.lower().replace(' ', '_')}_coverage_provider", ""),
                    "URL": user_data.get(f"{coverage.lower().replace(' ', '_')}_coverage_url", "")
                }
                for coverage in coverage_types
            ])

            # Display and allow editing of the checklist data using st.data_editor
            edited_df = st.data_editor(
                checklist_df,
                use_container_width=True,
                column_config={
                    "Coverage Type": st.column_config.Column(disabled=True),  # Prevent editing of coverage type
                },
                hide_index=True,
                key="checklist_editor"
            )

            checklist_submitted = st.form_submit_button("Submit Monthly Checklist")

        if checklist_submitted:
            # Update user_data with edited values from data_editor, including Provider and URL
            for _, row in edited_df.iterrows():
                coverage = row["Coverage Type"]
                prefix = coverage.lower().replace(' ', '_')
                user_data[f"{prefix}_coverage_exists"] = row["Exists"]
                user_data[f"{prefix}_coverage_accessible"] = row["Accessible Online"]
                user_data[f"{prefix}_coverage_paid"] = row["Paid Up"]
                user_data[f"{prefix}_coverage_claims_open"] = row["Claims Open"]
                user_data[f"{prefix}_coverage_comments"] = row["Comments"]
                user_data[f"{prefix}_coverage_provider"] = row["Provider"]
                user_data[f"{prefix}_coverage_url"] = row["URL"]
            user_data["last_checklist_date"] = datetime.now().isoformat()
            user_data["last_updated"] = datetime.now().isoformat()
            save_user_data(user_data)
            st.success("Monthly checklist submitted successfully. Thank you for verifying your coverage status.")
            st.rerun()  # Refresh the page to reflect updated status

    # Update the status report display section near the end of display_assessment_and_updates
    if user_data:
        st.subheader("Current Data Status")
        st.write(f"Last Updated: {user_data.get('last_updated', 'Never')}")
        st.write(f"Last Checklist Completed: {user_data.get('last_checklist_date', 'Never')}")
        update_message = check_for_updates(user_data)
        if update_message != "No immediate updates or adjustments needed.":
            st.warning(update_message)

        # Display current coverage status if checklist data exists, with Provider and URL
        if any(field in user_data for field in COVERAGE_FIELDS):
            st.subheader("Current Coverage Status")
            st.write("Latest status of your insurance coverages based on your last checklist:")
            coverage_types = ["Life", "Health", "Home", "Car", "Personal Property"]
            status_data = []
            for coverage in coverage_types:
                prefix = coverage.lower().replace(' ', '_')
                status_data.append({
                    "Coverage Type": coverage,
                    "Exists": "Yes" if user_data.get(f"{prefix}_coverage_exists", False) else "No",
                    "Accessible Online": "Yes" if user_data.get(f"{prefix}_coverage_accessible", False) else "No",
                    "Paid Up": "Yes" if user_data.get(f"{prefix}_coverage_paid", False) else "No",
                    "Claims Open": "Yes" if user_data.get(f"{prefix}_coverage_claims_open", False) else "No",
                    "Comments": user_data.get(f"{prefix}_coverage_comments", ""),
                    "Provider": user_data.get(f"{prefix}_coverage_provider", ""),
                    "URL": user_data.get(f"{prefix}_coverage_url", "")
                })
            st.table(status_data)
            
if __name__ == "__main__":
    main()