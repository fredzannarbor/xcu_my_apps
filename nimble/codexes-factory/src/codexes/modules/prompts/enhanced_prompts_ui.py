#!/usr/bin/env python3
"""
Streamlit UI components for Enhanced Prompts Management System
"""

import streamlit as st
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

try:
    from codexes.modules.prompts.enhanced_prompts_manager import (
        EnhancedPromptsManager, BookStructure, PromptSection
    )
except ImportError:
    from src.codexes.modules.prompts.enhanced_prompts_manager import (
        EnhancedPromptsManager, BookStructure, PromptSection
    )

class EnhancedPromptsUI:
    """Streamlit UI for enhanced prompts management."""

    def __init__(self):
        """Initialize the prompts UI."""
        self.manager = EnhancedPromptsManager()

    def render_prompts_configuration_section(self) -> Tuple[List[str], List[str], BookStructure]:
        """Render the complete prompts configuration section.

        Returns:
            Tuple of (publisher_files, imprint_files, book_structure)
        """
        st.subheader("📝 Enhanced Prompts Configuration")

        with st.expander("ℹ️ How Enhanced Prompts Work", expanded=False):
            st.markdown("""
            **Hierarchical Prompts Selection:**
            - Select publisher-level and imprint-level prompts files
            - Imprint prompts override publisher prompts for identical keys
            - Creates a virtual prompts file with merged content

            **Book Structure Organization:**
            - **Front Matter**: Prompts for content before the main body (e.g., preface, intro)
            - **Body Source**: Select an existing markdown or PDF file as the main content
            - **Back Matter**: Prompts for content after the main body (e.g., bibliography, bio)
            """)

        # Discover available prompts files
        available_files = self.manager.discover_prompts_files()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🏢 Publisher-Level Prompts")
            publisher_files = st.multiselect(
                "Select publisher prompts files",
                options=available_files["publisher"],
                default=["global"] if "global" in available_files["publisher"] else [],
                help="Publisher-level prompts apply to all imprints"
            )

        with col2:
            st.markdown("#### 🏷️ Imprint-Level Prompts")
            imprint_files = st.multiselect(
                "Select imprint prompts files",
                options=available_files["imprint"],
                help="Imprint prompts override publisher prompts for identical keys"
            )

        # Create virtual prompts file if any files are selected
        virtual_prompts = {}
        if publisher_files or imprint_files:
            with st.spinner("Creating virtual prompts file..."):
                virtual_prompts = self.manager.create_virtual_prompts_file(
                    publisher_files, imprint_files
                )

            # Show virtual prompts summary
            if virtual_prompts:
                st.success(f"✅ Virtual prompts file created with {len(virtual_prompts.get('prompt_keys', []))} prompt keys")

                with st.expander("🔍 Virtual Prompts Preview", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Prompt Keys:**")
                        for key in virtual_prompts.get("prompt_keys", []):
                            st.write(f"• {key}")
                    with col2:
                        st.write("**Source Files:**")
                        metadata = virtual_prompts.get("_metadata", {})
                        source_files = metadata.get("source_files", {})
                        if source_files.get("publisher"):
                            st.write("Publisher:")
                            for f in source_files["publisher"]:
                                st.write(f"  • {f}")
                        if source_files.get("imprint"):
                            st.write("Imprint:")
                            for f in source_files["imprint"]:
                                st.write(f"  • {f}")

        # Book structure configuration
        st.markdown("---")
        book_structure = self._render_book_structure_section(virtual_prompts)

        return publisher_files, imprint_files, book_structure

    def _render_book_structure_section(self, virtual_prompts: Dict[str, Any]) -> BookStructure:
        """Render the book structure configuration section."""

        # Make Book Structure Configuration collapsible with default collapsed
        with st.expander("📖 Book Structure Configuration", expanded=False):
            if not virtual_prompts:
                st.info("Select prompts files above to configure book structure")
                return BookStructure()

            # Get available prompts
            available_prompts = self.manager.get_available_prompts(virtual_prompts)
            if not available_prompts:
                st.warning("No valid prompts found in selected files")
                return BookStructure()

            # Categorize prompts for suggestions
            categorized = self.manager.categorize_prompts(available_prompts)

            # Initialize session state for book structure
            if 'book_structure' not in st.session_state:
                st.session_state.book_structure = BookStructure()

            structure = st.session_state.book_structure

            # Show default front matter suggestion as info box
            if categorized.get("front_matter"):
                st.info(f"💡 Suggested default front matter: {', '.join(categorized['front_matter'][:3])}{'...' if len(categorized['front_matter']) > 3 else ''}")

            # Three columns for front matter, body, back matter
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                st.markdown("#### 📑 Front Matter")
                st.caption("Content before the main body")

                # Multi-select for front matter prompts
                front_matter_options = categorized["front_matter"] + [p for p in available_prompts if p not in categorized["front_matter"]]

                # Set default front matter if none selected
                default_front_matter = structure.front_matter.prompts if structure.front_matter.prompts else categorized.get("front_matter", [])[:3]

                selected_front = st.multiselect(
                    "Select front matter prompts (order matters):",
                    options=front_matter_options,
                    default=default_front_matter,
                    key="front_matter_selection",
                    help="Prompts will appear in the order selected"
                )
                structure.front_matter.prompts = selected_front

            with col2:
                st.markdown("#### 📄 Body Source")
                st.caption("Main content file")

                # File selection with selectbox
                file_types = ["*.md", "*.pdf", "*.txt"]
                available_files = []
                for pattern in file_types:
                    available_files.extend(Path(".").glob(f"**/{pattern}"))

                file_options = [""] + [str(f) for f in sorted(available_files)]
                selected_body_file = st.selectbox(
                    "Select body source file:",
                    options=file_options,
                    index=file_options.index(structure.body_source) if structure.body_source and structure.body_source in file_options else 0,
                    key="body_source_selection",
                    help="Path to markdown (.md), PDF (.pdf), or text (.txt) file"
                )

                # Manual file path input as fallback
                manual_body_source = st.text_input(
                    "Or enter file path manually:",
                    value="" if selected_body_file else (structure.body_source or ""),
                    key="manual_body_source",
                    help="Type the full path to your file"
                )

                structure.body_source = selected_body_file if selected_body_file else (manual_body_source if manual_body_source else None)

                if not available_files:
                    st.info("No .md, .pdf, or .txt files found in project")

            with col3:
                st.markdown("#### 📚 Back Matter")
                st.caption("Content after the main body")

                # Multi-select for back matter prompts
                back_matter_options = categorized["back_matter"] + [p for p in available_prompts if p not in categorized["back_matter"]]
                selected_back = st.multiselect(
                    "Select back matter prompts (order matters):",
                    options=back_matter_options,
                    default=structure.back_matter.prompts,
                    key="back_matter_selection",
                    help="Prompts will appear in the order selected"
                )
                structure.back_matter.prompts = selected_back

                # Show suggested prompts as info
                if categorized["back_matter"]:
                    st.info(f"💡 Suggested: {', '.join(categorized['back_matter'][:3])}{'...' if len(categorized['back_matter']) > 3 else ''}")

        # Update session state
        st.session_state.book_structure = structure

        # Validation
        if virtual_prompts:
            errors = self.manager.validate_book_structure(structure, virtual_prompts)
            if errors:
                st.error("❌ Validation errors:")
                for error in errors:
                    st.write(f"• {error}")
            else:
                st.success("✅ Book structure is valid")

        return structure

    def render_command_preview(self,
                             publisher_files: List[str],
                             imprint_files: List[str],
                             structure: BookStructure) -> List[str]:
        """Render command line preview section."""
        st.subheader("🖥️ Command Line Preview")

        if not (publisher_files or imprint_files):
            st.info("Configure prompts above to see command line arguments")
            return []

        # Generate command line arguments
        args = self.manager.generate_command_line_args(
            publisher_files, imprint_files, structure
        )

        if args:
            st.markdown("**Additional arguments for enhanced prompts:**")
            st.code(" ".join(args), language="bash")

            # Show full example command
            with st.expander("📋 Full Example Command", expanded=False):
                base_cmd = "python run_book_pipeline.py --schedule-file books.csv --imprint my_imprint --model gemini/gemini-2.5-flash"
                full_cmd = f"{base_cmd} {' '.join(args)}"
                st.code(full_cmd, language="bash")
        else:
            st.info("No enhanced prompts arguments needed")

        return args

    def render_save_load_section(self, structure: BookStructure) -> None:
        """Render save/load configuration section (form-compatible version)."""
        st.subheader("💾 Save/Load Configuration")

        # Show current configuration summary
        if structure.front_matter.prompts or structure.body_source or structure.back_matter.prompts:
            st.markdown("**Current Configuration:**")
            if structure.front_matter.prompts:
                st.write(f"• Front Matter: {len(structure.front_matter.prompts)} prompts")
            if structure.body_source:
                st.write(f"• Body Source: {structure.body_source}")
            if structure.back_matter.prompts:
                st.write(f"• Back Matter: {len(structure.back_matter.prompts)} prompts")

        # Note about saving configurations outside the form
        st.info("💡 Save/Load functionality available after form submission in the main pipeline.")