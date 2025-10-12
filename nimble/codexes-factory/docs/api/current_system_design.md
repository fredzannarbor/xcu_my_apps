
Of course. Based on the complete set of files you've provided and the successful import fixes, I can now create a comprehensive design document. This document will describe the current, working architecture ("Design As Is") and then outline a strategic path for future enhancements, all without writing or modifying any code.

***

## Codexes Factory - Design Document (v3.2)

This document outlines the current architecture of the Codexes Factory project and proposes a strategy for future development.

### Part 1: Design As Is

This section describes the current state of the application after the recent import fixes and integration of the authentication system.

#### 1.1. Core Architecture

*   **Package Structure:** The project is structured as an installable Python package named `codexes`. The source code resides in the `src/` directory, which is defined as the package root in `pyproject.toml`. This allows for robust, absolute imports (e.g., `from codexes.core import ...`) throughout the application, eliminating the need for `sys.path` manipulation.
*   **Application Entry Points:**
    *   **Streamlit UI:** `src/codexes/Codexes.py` is the main entry point for the multi-page web application, launched via `streamlit run`.
    *   **Command-Line Interface (CLI):** `src/codexes/cli.py` provides a terminal-based interface for automated workflows, driven by command-line arguments.

#### 1.2. Key Components

*   **Authentication (`core/auth.py`, `pages/8_Login_Register.py`)**
    *   **Technology**: Uses `streamlit-authenticator` for handling user login, registration, and session state (cookies).
    *   **Configuration**: User data (usernames, hashed passwords, roles) is stored externally in `resources/yaml/config.yaml`. A utility script (`src/core/genpw.py`) is provided for hashing passwords.
    *   **Role-Based Access Control (RBAC)**:
        *   A clear hierarchy of roles is defined: `public`, `user`, `subscriber`, `admin`.
        *   The `core/auth.py` module contains a `PAGE_ACCESS_LEVELS` dictionary that maps each page file to a minimum required role.
        *   The main `Codexes.py` script dynamically filters the navigation sidebar based on the current user's role, only showing pages they are authorized to view.
    *   **UI**: The `pages/8_Login_Register.py` file provides a dedicated UI for users to log in or create new accounts.

*   **Internationalization (i18n) (`core/translations.py`)**
    *   A centralized dictionary system supports multiple languages (currently English and Korean).
    *   The `get_translation(lang, key)` function retrieves UI strings.
    *   A lambda function `T()` is used as a shorthand in UI pages to reduce boilerplate.
    *   Language can be switched dynamically from the Streamlit sidebar.

*   **LLM Interaction (`core/llm_caller.py`)**
    *   **Abstraction**: `litellm` is used as a consistent interface to call various LLM APIs (Gemini, OpenAI, etc.).
    *   **Robustness**: Implements a `tenacity`-based retry decorator with exponential backoff for transient network or API errors. It intelligently distinguishes between retryable (e.g., timeouts) and non-retryable (e.g., invalid API key) errors.
    *   **Parsing**: Includes a helper function (`_parse_llm_response`) to safely handle and parse LLM outputs, including cleaning and decoding JSON responses.

*   **Workflow Modules (`modules/`)**
    *   **Metadata Model (`modules/metadata/metadata_models.py`)**:
        *   The `CodexMetadata` dataclass is the central data structure. It acts as a "single source of truth" for all information related to a book during a processing pipeline.
        *   It contains fields for bibliographic data, generative content (summaries, keywords), physical specifications, pricing, and storefront-specific content.
        *   The `update_from_dict` method intelligently populates the object from raw LLM JSON responses.
    *   **Metadata Generation (`modules/metadata/metadata_generator.py`)**:
        *   The `generate_metadata_from_prompts` function orchestrates the core workflow:
            1.  Loads a document (`file_handler.py`).
            2.  Extracts deterministic data (page count, etc.).
            3.  Loads and prepares prompts (`prompt_manager.py`).
            4.  Calls the LLM (`llm_caller.py`).
            5.  Populates and returns a single, complete `CodexMetadata` object.
    *   **Distribution Output (`modules/distribution/`)**:
        *   A `BaseGenerator` abstract class defines the interface for creating distribution files.
        *   `LsiAcsGenerator` implements this interface to create a CSV file conforming to the LSI ACS specification, using the `CodexMetadata` object as input.
        *   `StorefrontGenerator` implements the interface to create a CSV for the `Pilsa Bookstore` catalog.

    *   **Imprint Prepress Pipeline (`imprints/xynapse_traces/prepress.py`)**:
        *   This script provides a command-line interface for processing a single book from a JSON file for a specific imprint.
        *   **Purpose:** It automates the generation of distribution-ready interior and cover files based on an imprint's unique templates and branding.
        *   **Inputs:** The script takes a JSON file containing the book's metadata, a final output directory, and a templates directory.
        *   **Processing:** It generates the book's interior PDF using a LaTeX template and the provided metadata. It then determines the page count and generates the cover using another LaTeX template.
        *   **Outputs:** The script saves the final interior PDF and cover files to the output directory. It also updates the input JSON file with the final page count and the paths to the generated cover files.
        *   **Dependencies:** The script uses `PyMuPDF` for PDF manipulation and relies on helper modules for TeX compilation and cover generation.

*   **Configuration & Data**
    *   `prompts/`: Contains JSON files with prompts for various LLM tasks.
    *   `templates/`: Holds header/template files for outputs, like `LSI_ACS_header.csv`.
    *   `data/`: Stores application data, such as the `books.csv` catalog for the storefront.
    *   `.env`: Stores secret API keys, loaded by `python-dotenv`.

#### 1.3. User Interface (Streamlit Pages)

*   **`Codexes.py`**: The main application wrapper. It handles session initialization, authentication state checking, and builds the `st.navigation` object based on the user's role.
*   **`pages/1_Home.py`**: A public-facing informational page.
*   **`pages/4_Metadata_and_Distribution.py`**: The core functional page for authorized users. It allows manuscript upload and triggers the metadata generation workflow. Displays results and download links.
*   **`pages/6_Pilsa_Bookstore.py`**: A public-facing e-commerce storefront with a catalog, detail pages, a shopping cart, and Stripe integration. It uses internal `st.session_state` to manage its view (catalog vs. details vs. cart).
*   **`pages/7_Admin_Dashboard.py`**: An admin-only page for user management (view, add, edit, delete users) that directly interacts with the `config.yaml` file.
*   **`pages/8_Login_Register.py`**: A public page dedicated to user login and registration.

---

### Part 2: Future Enhancement Strategy

This section outlines potential improvements to build upon the current v3.2 architecture, aligning with the project's goals and coding guidelines.

#### 2.1. Code Unification and Refactoring

*   **Integrate External Modules**: The files listed in `found_files.csv` from directories like `codexes-ideas`, `codexes-leo-bloom`, etc., should be systematically migrated into the main `codexes-factory/src/codexes/modules/` directory. This will:
    *   Eliminate redundant code (e.g., multiple `multi_model_multi_prompt_caller.py` files).
    *   Create a single, cohesive, and importable `codexes` library.
    *   Centralize all functionality under the same robust structure.
*   **Refactor `Pilsa_Bookstore.py`**: The bookstore's internal routing (`st.session_state.page`) should be refactored. The "Details" and "Cart" views should become separate pages within the `pages` directory. This will simplify the code, align with Streamlit's multipage app paradigm, and allow for cleaner state management and URL-based navigation to specific books.
*   **Centralize `CodexMetadata`**: Ensure that all new modules (Ideation, Enhancement, etc.) are refactored to accept and return the `CodexMetadata` object. This maintains it as the single source of truth passed between workflow stages.

#### 2.2. UI/UX and Workflow Improvements

*   **Multi-Step Wizard for Metadata**: Convert the `4_Metadata_and_Distribution.py` page into a guided, multi-step process using `st.container` and stateful buttons.
    1.  Step 1: Upload File.
    2.  Step 2: Select Prompts (with previews).
    3.  Step 3: Review & Edit generated metadata in a form pre-populated from the `CodexMetadata` object.
    4.  Step 4: Select and generate distribution formats.
*   **Dynamic Bookstore Catalog**: Instead of relying on a static `data/books.csv`, connect the bookstore to a more robust data source (e.g., a simple SQLite database or a remote DB). Create a function on the Admin Dashboard to "publish" a new book, which would take a generated `CodexMetadata` object and add it to the live catalog.
*   **Complete Placeholder Pages**: Build out the functionality for `2_Ideation_and_Development.py` and `3_Manuscript_Enhancement.py` by integrating the logic from the `codexes-ideas` and `codexes-copy-edit` modules.

#### 2.3. LSI ACS Generation Enhancement

*   **Full LSI Spec Implementation**: The current `LsiAcsGenerator` maps a subset of fields. The next step is to comprehensively map every field from the `lsi_acs_metadata.csv` and `codes.csv` to the `CodexMetadata` dataclass.
*   **LSI Code Lookups**: Implement helper functions within the `LsiAcsGenerator` to use the `codes.csv` data. For example, a function that takes a descriptive text like "Perfect Bound" and finds the corresponding LSI `Rendition / Booktype` code.
*   **Pricing Engine**: The current price calculation is a simple placeholder. Develop a more sophisticated pricing engine in a new `core/pricing.py` module that can calculate all international prices based on the USD price, page count, and exchange rates (static or dynamic). This logic should be used to populate all pricing fields in the `CodexMetadata` object before it's passed to the LSI generator.

#### 2.4. Expanded Testing and Error Handling

*   **Unit Tests**: Create `pytest` tests for the core logic, especially:
    *   `llm_caller.py`: Test retry logic and JSON parsing with mock responses.
    *   `metadata_models.py`: Test the `update_from_dict` logic with various malformed inputs.
    *   `auth.py`: Test `get_allowed_pages` for each role.
*   **Input Validation**: Strengthen input validation in Streamlit forms (e.g., for user registration, metadata editing) to provide immediate, user-friendly feedback before submission.
*   **Logging**: Ensure the session-based `request_id` from `utils.py` is passed down and logged in all major function calls to allow for complete tracing of a user's workflow in the logs.

By following this strategy, Codexes Factory can evolve from a functional application into a robust, scalable, and maintainable platform.
