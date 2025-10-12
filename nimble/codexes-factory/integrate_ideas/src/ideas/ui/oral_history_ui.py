import streamlit as st
import os
import uuid
import json
from datetime import datetime
import pandas as pd
from pathlib import Path
import subprocess
import shutil
from dotenv import load_dotenv
import stripe
import logging
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
if not STRIPE_SECRET_KEY:
    logger.error("STRIPE_SECRET_KEY not found in .env file")
    raise ValueError("STRIPE_SECRET_KEY is required")

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Product ID for the digital product required to use the app
PRODUCT_ID = os.getenv("STRIPE_PRODUCT_ID", "prod_XXXX")  # Replace with your actual Stripe Product ID

# Directory for saving run outputs
BASE_DIR = "runs"
CATALOG_FILE = "catalog.json"


# Function to verify if user has purchased the product (mock implementation)
def has_purchased_product(user_email: str) -> bool:
    """
    Check if the user has purchased the specific product via Stripe.
    This is a mock implementation; replace with actual Stripe API calls to verify purchase.
    """
    try:
        # In a real application, you'd query Stripe for customer purchases or use a database
        # Example: List customer purchases or checkout sessions
        customers = stripe.Customer.list(email=user_email)
        if customers.data:
            customer = customers.data[0]
            sessions = stripe.checkout.Session.list(customer=customer.id)
            for session in sessions.data:
                line_items = stripe.checkout.Session.list_line_items(session.id)
                for item in line_items.data:
                    if item.price.product == PRODUCT_ID:
                        return True
        return False
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error checking purchase: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking purchase: {e}")
        return False


# Function to update catalog of results
def update_catalog(run_id: str, title: str, output_path: str, output_dir: str):
    """Update the catalog JSON with new run results."""
    catalog_path = os.path.join(BASE_DIR, CATALOG_FILE)
    catalog = []
    if os.path.exists(catalog_path):
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)

    catalog.append({
        "run_id": run_id,
        "title": title,
        "timestamp": datetime.now().isoformat(),
        "output_path": output_path,
        "output_dir": output_dir
    })

    os.makedirs(BASE_DIR, exist_ok=True)
    with open(catalog_path, 'w') as f:
        json.dump(catalog, f, indent=2)


# Function to run the oral history builder script with provided arguments
def run_oral_history_builder(args: Dict) -> tuple:
    """Execute the vibe_oral_history_builder.py script with provided arguments."""
    run_id = str(uuid.uuid4())[:8]
    output_dir = os.path.join(BASE_DIR, f"run-{run_id}")
    os.makedirs(output_dir, exist_ok=True)

    cmd = ["uv", "run", "python", "src/ideas/vibes/vibe_oral_history_builder.py"]
    for key, value in args.items():
        if isinstance(value, bool):
            if value:  # Only append the flag if True
                cmd.append(f"--{key.replace('_', '-')}")
        elif isinstance(value, list) and value:  # Only extend if list is non-empty
            cmd.extend([f"--{key.replace('_', '-')}", *map(str, value)])
        elif value is not None and str(value).strip():  # Only extend if value is non-empty
            cmd.extend([f"--{key.replace('_', '-')}", str(value)])

    cmd.extend(["--base-dir", output_dir])

    with st.spinner("Generating oral history draft..."):
        # Quote arguments with spaces for clarity in the log
        quoted_cmd = [f'"{arg}"' if ' ' in arg else arg for arg in cmd]
        logger.info(f"Running command: {' '.join(quoted_cmd)}")
        try:
            # Run the subprocess and capture output
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Print the output to the console with clear formatting
            print("\n=== Subprocess Output (stdout) ===\n")
            if result.stdout:
                print(result.stdout)
            else:
                print("No output in stdout.")
            print("\n=== Subprocess Error Output (stderr) ===\n")
            if result.stderr:
                print(result.stderr)
            else:
                print("No output in stderr.")

            if result.returncode != 0:
                logger.error(f"Script execution failed: {result.stderr}")
                st.error(f"Error generating draft: {result.stderr}")
                return None, None, None
        except Exception as e:
            logger.error(f"Unexpected error during script execution: {e}")
            st.error(f"Unexpected error: {e}")
            return None, None, None

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, "oral_history_draft.md")

        return None, None, None  # Temporarily returning None as in the original code

        # Extract title from high-level spec for catalog
        hls_path = os.path.join(output_dir, "oral_history_high_level_spec.json")
        title = "Untitled Oral History"
        if os.path.exists(hls_path):
            with open(hls_path, 'r') as f:
                hls = json.load(f)
                title = hls.get("title", title)

        # Update catalog
        update_catalog(run_id, title, output_path, output_dir)
        return output_path, output_dir, title
# Streamlit App
st.title("Oral History Builder")

# User Authentication (mock - replace with actual login system if needed)
user_email = st.text_input("Enter your email to verify purchase:", placeholder="user@example.com")
if user_email:
    if not has_purchased_product(user_email):
        st.error("You must purchase the required product to use this tool.")
        st.markdown(f"[Purchase Access](#)", unsafe_allow_html=True)  # Link to Stripe Checkout (mock)
        st.stop()
    else:
        st.success("Purchase verified. You can use the tool.")

# Form for input parameters (mapped to argparse arguments)
with st.form("oral_history_form"):
    st.subheader("Configuration Options")

    mode = st.selectbox("Mode", ["full", "hls_only", "from_hls", "detailed_outline"],
                        help="Mode to run: 'full' for complete workflow, 'hls_only' to generate/review HLS only, 'from_hls' to start from existing HLS, 'detailed_outline' to start from detailed outline.")

    description = st.text_area("Description",
                               placeholder="Description for generating high-level spec. If not provided, a default is used.",
                               help="Description for generating high-level spec.")

    auto_refine = st.checkbox("Auto Refine HLS",
                              help="Automatically refine HLS with LLM instead of pausing for human edit.")

    limit_sections = st.number_input("Limit Sections", min_value=1, value=None, step=1, format="%d",
                                     help="Maximum number of draft sections to create (default = None for unlimited).")

    retry_quotes = st.checkbox("Retry Quotes",
                               help="Enable retry logic for quote generation to meet word count targets (may slow down execution).")

    word_count_target = st.number_input("Word Count Target", min_value=1000, value=60000, step=1000,
                                        help="Target word count for the entire project (default = 60000).")

    generate_ideas = st.checkbox("Generate Ideas",
                                 help="Generate ideas for oral history topics using ContinuousIdeaGenerator before HLS.")

    run_tournament = st.checkbox("Run Tournament",
                                 help="Run a tournament to rank generated ideas and select the best for HLS or outline.")

    idea_batch_size = st.number_input("Idea Batch Size", min_value=1, value=5, step=1,
                                      help="Number of ideas to generate per batch (default = 5).")

    writing_model = st.text_input("Writing Model", value="grok-3-fast-beta",
                                  help="Model to use for writing (default = 'grok-3-fast-beta').")

    idea_model = st.text_input("Idea Model", value="mistral",
                               help="Model to use for idea generation (default = 'mistral').")

    idea_temperature = st.number_input("Idea Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1,
                                       help="Temperature for idea generation model (default = 0.7).")

    stipulated_facts = st.text_area("Stipulated Facts Files (one per line)",
                                    placeholder="Paths to files (PDF, JSON, or text) containing stipulated facts for story grounding.",
                                    help="Paths to files containing stipulated facts.")

    submitted = st.form_submit_button("Generate Oral History")

    if submitted:
        # Convert inputs to a dictionary matching argparse arguments
        args = {
            "mode": mode,
            "description": description if description.strip() else None,
            "auto_refine": auto_refine,
            "limit_sections": limit_sections if limit_sections else None,
            "retry_quotes": retry_quotes,
            "word_count_target": word_count_target,
            "generate_ideas": generate_ideas,
            "run_tournament": run_tournament,
            "idea_batch_size": idea_batch_size,
            "writing_model": writing_model,
            "idea_model": idea_model,
            "idea_temperature": idea_temperature,
            "stipulated_facts": stipulated_facts.splitlines() if stipulated_facts.strip() else []
        }

        # Run the script
        output_path, output_dir, title = run_oral_history_builder(args)

        if output_path:
            st.success(f"Generated oral history draft: {title}")

            # Provide download link for the main output
            with open(output_path, 'rb') as f:
                st.download_button(
                    label="Download Oral History Draft (Markdown)",
                    data=f,
                    file_name=os.path.basename(output_path),
                    mime="text/markdown"
                )

            # Provide download link for the entire output directory as a zip
            zip_path = os.path.join(BASE_DIR, f"run-{os.path.basename(output_dir)}.zip")
            shutil.make_archive(os.path.splitext(zip_path)[0], 'zip', output_dir)
            with open(zip_path, 'rb') as f:
                st.download_button(
                    label="Download All Outputs (ZIP)",
                    data=f,
                    file_name=os.path.basename(zip_path),
                    mime="application/zip"
                )

# Display catalog of previous runs
st.subheader("Catalog of Generated Oral Histories")
catalog_path = os.path.join(BASE_DIR, CATALOG_FILE)
if os.path.exists(catalog_path):
    with open(catalog_path, 'r') as f:
        catalog = json.load(f)
    if catalog:
        catalog_df = pd.DataFrame(catalog)
        st.dataframe(catalog_df[["run_id", "title", "timestamp"]])

        # Allow downloading files from catalog
        selected_run = st.selectbox("Select a run to download outputs:", [entry["run_id"] for entry in catalog])
        if selected_run:
            entry = next((e for e in catalog if e["run_id"] == selected_run), None)
            if entry:
                output_path = entry["output_path"]
                output_dir = entry["output_dir"]

                if os.path.exists(output_path):
                    with open(output_path, 'rb') as f:
                        st.download_button(
                            label=f"Download {entry['title']} Draft (Markdown)",
                            data=f,
                            file_name=os.path.basename(output_path),
                            mime="text/markdown"
                        )

                zip_path = os.path.join(BASE_DIR, f"run-{os.path.basename(output_dir)}.zip")
                if not os.path.exists(zip_path):
                    shutil.make_archive(os.path.splitext(zip_path)[0], 'zip', output_dir)
                with open(zip_path, 'rb') as f:
                    st.download_button(
                        label=f"Download All Outputs for {entry['title']} (ZIP)",
                        data=f,
                        file_name=os.path.basename(zip_path),
                        mime="application/zip"
                    )
    else:
        st.info("No previous runs found in catalog.")
else:
    st.info("No catalog file found. Generate an oral history to start building the catalog.")

# Footer
st.markdown("---")
st.markdown("Powered by Oral History Builder | Purchase verification by Stripe")