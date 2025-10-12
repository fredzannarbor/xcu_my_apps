# Codexes Factory: AI-Assisted Publishing Platform (v3.2)

Codexes Factory is a Streamlit-based application designed to streamline and enhance the book publishing lifecycle using Large Language Models. It provides a suite of tools for manuscript analysis, metadata generation, and the creation of distribution-ready files.

## Current State & Key Features

The platform is currently operational with the following core features implemented:

*   **Robust Authentication & Authorization:**
    *   Full user login, registration, and session management via `streamlit-authenticator`.
    *   Role-Based Access Control (RBAC) with four defined roles: `public`, `user`, `subscriber`, `admin`.
    *   Navigation and page access are dynamically controlled based on the logged-in user's role.

*   **Dynamic Imprint Management:**
    *   The system supports the concept of "imprints," which are distinct publishing brands with their own unique branding, templates, and content generation workflows.
    *   Each imprint has its own dedicated directory, containing custom prompts, LaTeX templates, and catalog data.
    *   A command-line pipeline is available to process books for a specific imprint, generating distribution-ready files based on the imprint's configuration.

*   **Imprint Prepress Pipeline:**
    *   The `imprints/xynapse_traces/prepress.py` script provides a command-line interface for processing a single book from a JSON file.
    *   **Inputs:** The script takes a JSON file containing the book's metadata, a final output directory, and a templates directory.
    *   **Processing:** It generates the book's interior PDF using a LaTeX template and the provided metadata. It then determines the page count and generates the cover using another LaTeX template.
    *   **Outputs:** The script saves the final interior PDF and cover files to the output directory. It also updates the input JSON file with the final page count and the paths to the generated cover files.
    *   **Dependencies:** The script uses `PyMuPDF` for PDF manipulation and relies on helper modules for TeX compilation and cover generation.

*   **Metadata & Distribution Workflow:**
    *   Users can upload a manuscript file (`.pdf`, `.docx`, `.txt`).
    *   A selection of LLM-powered prompts can be run against the manuscript to generate rich metadata.
    *   The system generates a centralized `CodexMetadata` object, which acts as a single source of truth for the book.
    *   From this central object, it generates formatted output files for specific distributors.
        *   **LSI ACS:** Creates a CSV file compatible with IngramSpark's Automated Content Submission system.
        *   **Pilsa Bookstore:** Creates a CSV to populate the integrated e-commerce storefront.

*   **Pilsa E-Commerce Storefront:**
    *   A public-facing bookstore page (`pages/6_Pilsa_Bookstore.py`) that displays a catalog of books from a `data/books.csv` file.
    *   Features include product detail pages, a shopping cart, and a full checkout process powered by **Stripe**.
    *   Supports bilingual (English/Korean) display of book information.

*   **Admin Dashboard:**
    *   A secure, admin-only page (`pages/7_Admin_Dashboard.py`) for user management.
    *   Admins can view, add, edit, and delete users and their roles directly from the UI.

*   **Command-Line Interface (CLI):**
    *   A functional CLI (`src/codexes/cli.py`) allows for automated, headless execution of the metadata generation workflow.

## Getting Started

Follow these steps to set up and run the development environment. The project is structured as an installable package to ensure clean and reliable imports.

1.  **Navigate into the Project Directory:**
    