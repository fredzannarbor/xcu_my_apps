# src/codexes/pages/11_Backmatter_Manager.py
import streamlit as st
from pathlib import Path
import json
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, '/Users/fred/xcu_my_apps')

# Try to import from the correct module path
try:
    from codexes.modules.prepress.partsofthebook_processor import PartsOfTheBookProcessor
    from codexes.modules.distribution.isbn_lookup import ISBNLookupService
    from codexes.modules.distribution.quote_processor import QuoteProcessor
    from codexes.modules.distribution.pricing_validator import PricingValidator
except ImportError:
    try:
        from src.codexes.modules.prepress.partsofthebook_processor import PartsOfTheBookCreator
        from src.codexes.modules.distribution.isbn_lookup import ISBNLookupService
        from src.codexes.modules.distribution.quote_processor import QuoteProcessor
        from src.codexes.modules.distribution.pricing_validator import PricingValidator
    except ImportError:
        st.error("Failed to import required modules. Make sure you're running from the correct directory.")
        st.stop()

st.set_page_config(page_title="Backmatter Manager", layout="wide")

st.title("📚 Backmatter Manager")
st.markdown("Generate and manage backmatter sections for your books.")

# --- Helper function to find processed book data ---
def get_processed_books():
    books = []
    
    # Check in output directories
    output_dir = Path("output")
    if output_dir.is_dir():
        for imprint_dir in output_dir.glob("*_build"):
            if imprint_dir.is_dir():
                processed_dir = imprint_dir / "processed_json"
                if processed_dir.is_dir():
                    for file in processed_dir.glob("*.json"):
                        books.append(str(file))
    
    return books

# --- Helper function to load book data ---
def load_book_data(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load book data: {e}")
        return None

# --- Main UI ---
st.header("Backmatter Generation")

# --- Book Selection ---
book_options = get_processed_books()
if not book_options:
    st.warning("No processed book data found. Run the Book Pipeline first to generate book data.")
    st.info("You can also upload a book JSON file directly.")
    uploaded_file = st.file_uploader("Upload Book JSON", type=["json"])
    if uploaded_file:
        try:
            book_data = json.loads(uploaded_file.getvalue().decode("utf-8"))
            st.success("Book data loaded successfully!")
        except Exception as e:
            st.error(f"Failed to parse JSON: {e}")
            st.stop()
    else:
        st.stop()
else:
    selected_book = st.selectbox("Select Book", options=book_options)
    book_data = load_book_data(selected_book)
    if not book_data:
        st.stop()

# Display book info
st.subheader("Book Information")
col1, col2, col3 = st.columns(3)
with col1:
    st.write(f"**Title:** {book_data.get('title', 'Unknown')}")
    st.write(f"**Author:** {book_data.get('author', 'Unknown')}")
with col2:
    st.write(f"**Imprint:** {book_data.get('imprint', 'Unknown')}")
    st.write(f"**ISBN:** {book_data.get('isbn13', 'Not assigned')}")
with col3:
    quote_count = len(book_data.get('quotes', []))
    st.write(f"**Quotes:** {quote_count}")
    st.write(f"**Stream:** {book_data.get('stream', 'Unknown')}")

# --- Backmatter Generation Options ---
st.header("Generate Backmatter")

with st.form("backmatter_form"):
    st.subheader("Select Sections to Generate")
    
    col1, col2 = st.columns(2)
    with col1:
        generate_mnemonics = st.checkbox("Generate Mnemonics", value=True)
        generate_bibliography = st.checkbox("Generate Bibliography", value=True)
    with col2:
        generate_verification_log = st.checkbox("Generate Verification Log", value=True)
        generate_glossary = st.checkbox("Generate Glossary", value=True)
    
    st.subheader("Advanced Options")
    col1, col2 = st.columns(2)
    with col1:
        lookup_isbns = st.checkbox("Lookup ISBNs for Bibliography", value=True)
        validate_pricing = st.checkbox("Validate USD Pricing", value=True)
    with col2:
        llm_model = st.selectbox(
            "LLM Model for Mnemonics", 
            options=["gemini/gemini-2.5-flash", "gemini/gemini-2.5-pro", "openai/gpt-4o"],
            index=0
        )
        output_format = st.selectbox(
            "Output Format",
            options=["LaTeX", "Markdown", "HTML"],
            index=0
        )
    
    output_dir = st.text_input("Output Directory", value="backmatter_output")
    
    submitted = st.form_submit_button("Generate Backmatter", type="primary", use_container_width=True)

# --- Processing Logic ---
if submitted:
    start_time = time.time()
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Initialize processors
    backmatter_processor = PartsOfTheBookCreator()
    quote_processor = QuoteProcessor()
    
    # Process quotes if needed
    with st.spinner("Processing quotes..."):
        processed_quotes, validation_summary = quote_processor.extract_and_validate_quotes(book_data)
        book_data['quotes'] = processed_quotes
        st.success(f"Processed {len(processed_quotes)} quotes: {validation_summary['valid']} valid, {validation_summary['invalid']} invalid")
    
    # Generate backmatter sections
    results = {}
    
    if generate_mnemonics:
        with st.spinner("Generating mnemonics..."):
            try:
                mnemonics_content = backmatter_processor.process_mnemonics(book_data, model=llm_model)
                if mnemonics_content and mnemonics_content.strip():
                    mnemonics_path = output_path / "mnemonics.tex"
                    with open(mnemonics_path, "w", encoding="utf-8") as f:
                        f.write(mnemonics_content)
                    results["mnemonics"] = str(mnemonics_path)
                    st.success(f"✅ Mnemonics generated ({len(mnemonics_content)} characters)")
                else:
                    st.warning("⚠️ No mnemonics content generated - skipping mnemonics.tex creation")
                    results["mnemonics"] = None
            except Exception as e:
                st.error(f"Failed to generate mnemonics: {e}")
                results["mnemonics"] = None
    
    if generate_bibliography:
        with st.spinner("Generating bibliography..."):
            try:
                # Lookup ISBNs if requested
                if lookup_isbns:
                    isbn_service = ISBNLookupService()
                    sources = quote_processor.extract_bibliography_sources(processed_quotes)
                    st.info(f"Looking up ISBNs for {len(sources)} sources...")
                    sources_with_isbns = isbn_service.lookup_multiple_isbns(sources)
                    
                    # Update book data with ISBN information
                    for source in sources_with_isbns:
                        if source.get('isbn'):
                            st.success(f"Found ISBN for '{source['title']}' by {source['author']}: {source['isbn']}")
                
                bibliography_content = backmatter_processor.process_bibliography(book_data)
                if bibliography_content and bibliography_content.strip():
                    bibliography_path = output_path / "bibliography.tex"
                    with open(bibliography_path, "w", encoding="utf-8") as f:
                        f.write(bibliography_content)
                    results["bibliography"] = str(bibliography_path)
                    st.success(f"✅ Bibliography generated ({len(bibliography_content)} characters)")
                else:
                    st.warning("⚠️ No bibliography content generated - skipping bibliography.tex creation")
                    results["bibliography"] = None
            except Exception as e:
                st.error(f"Failed to generate bibliography: {e}")
                results["bibliography"] = None
    
    if generate_verification_log:
        with st.spinner("Generating verification log..."):
            try:
                verification_log_content = backmatter_processor.process_verification_log(book_data)
                if verification_log_content and verification_log_content.strip():
                    verification_log_path = output_path / "verification_log.tex"
                    with open(verification_log_path, "w", encoding="utf-8") as f:
                        f.write(verification_log_content)
                    results["verification_log"] = str(verification_log_path)
                    st.success(f"✅ Verification log generated ({len(verification_log_content)} characters)")
                else:
                    st.warning("⚠️ No verification log content generated - skipping verification_log.tex creation")
                    results["verification_log"] = None
            except Exception as e:
                st.error(f"Failed to generate verification log: {e}")
                results["verification_log"] = None
    
    if generate_glossary:
        with st.spinner("Generating glossary..."):
            try:
                glossary_content = backmatter_processor.process_glossary()
                glossary_path = output_path / "glossary.tex"
                with open(glossary_path, "w", encoding="utf-8") as f:
                    f.write(glossary_content)
                results["glossary"] = str(glossary_path)
                st.success(f"✅ Glossary generated ({len(glossary_content)} characters)")
            except Exception as e:
                st.error(f"Failed to generate glossary: {e}")
                results["glossary"] = None
    
    if validate_pricing:
        with st.spinner("Validating pricing..."):
            try:
                pricing_validator = PricingValidator()
                book_data = pricing_validator.validate_usd_pricing(book_data)
                pricing_summary = pricing_validator.generate_pricing_summary(book_data)
                st.success("✅ Pricing validated")
                st.info(pricing_summary)
            except Exception as e:
                st.error(f"Failed to validate pricing: {e}")
    
    # Save updated book data
    updated_book_path = output_path / "updated_book_data.json"
    with open(updated_book_path, "w", encoding="utf-8") as f:
        json.dump(book_data, f, ensure_ascii=False, indent=2)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Display results
    st.header("Generation Results")
    st.success(f"All requested backmatter sections generated in {duration:.2f} seconds!")
    st.info(f"Output files are available in: {output_path}")
    
    # Display download buttons for generated files
    st.subheader("Download Generated Files")
    col1, col2 = st.columns(2)
    
    with col1:
        for section, path in results.items():
            if path and Path(path).exists():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                st.download_button(
                    f"Download {section}.tex",
                    data=content,
                    file_name=f"{section}.tex",
                    mime="text/plain"
                )
    
    with col2:
        if Path(updated_book_path).exists():
            with open(updated_book_path, "r", encoding="utf-8") as f:
                content = f.read()
            st.download_button(
                "Download Updated Book Data",
                data=content,
                file_name="updated_book_data.json",
                mime="application/json"
            )

# --- Preview Section ---
st.header("Preview Generated Content")
if 'results' in locals() and results:
    section = st.selectbox("Select Section to Preview", options=[k for k, v in results.items() if v])
    
    if section and results[section]:
        with open(results[section], "r", encoding="utf-8") as f:
            content = f.read()
        
        st.code(content, language="latex")
        
        # Show estimated page count
        lines = content.count('\n')
        estimated_pages = max(1, lines // 40)  # Rough estimate: 40 lines per page
        st.info(f"Estimated page count: {estimated_pages}")