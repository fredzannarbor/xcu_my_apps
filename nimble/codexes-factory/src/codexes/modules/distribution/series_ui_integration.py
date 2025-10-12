"""
Series UI Integration Module

This module provides UI components for series selection and creation.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple, Callable

import streamlit as st

from ..metadata.metadata_models import CodexMetadata
from .series_registry import SeriesRegistry
from .series_assigner import SeriesAssigner

logger = logging.getLogger(__name__)


class SeriesUIIntegration:
    """
    Class for integrating series management with the UI.
    
    This class provides UI components for series selection and creation.
    """
    
    def __init__(self, series_registry: SeriesRegistry, series_assigner: SeriesAssigner):
        """
        Initialize the series UI integration.
        
        Args:
            series_registry: SeriesRegistry instance to use for series management
            series_assigner: SeriesAssigner instance to use for series assignment
        """
        self.series_registry = series_registry
        self.series_assigner = series_assigner
    
    def render_series_selector(self, metadata: CodexMetadata, on_change: Optional[Callable] = None) -> None:
        """
        Render a UI component for selecting or creating a series.
        
        Args:
            metadata: CodexMetadata object to update with series information
            on_change: Optional callback function to call when the series is changed
        """
        st.subheader("Series Information")
        
        # Get publisher from metadata
        publisher_id = metadata.publisher
        
        # Get available series options
        series_options = self.series_assigner.get_series_options(publisher_id)
        
        # Add "None" and "Create New Series" options
        series_names = ["None", "Create New Series"] + [option["name"] for option in series_options]
        
        # Get current series name from metadata
        current_series = metadata.series_name if metadata.series_name else "None"
        
        # Create series selector
        selected_series = st.selectbox(
            "Series",
            options=series_names,
            index=series_names.index(current_series) if current_series in series_names else 0,
            key="series_selector"
        )
        
        # Handle series selection
        if selected_series == "None":
            # Clear series information
            metadata.series_name = ""
            metadata.series_number = ""
            
            if on_change:
                on_change()
                
        elif selected_series == "Create New Series":
            # Show form for creating a new series
            with st.expander("Create New Series", expanded=True):
                new_series_name = st.text_input("Series Name", key="new_series_name")
                multi_publisher = st.checkbox("Allow multiple publishers", key="multi_publisher")
                description = st.text_area("Description", key="series_description")
                
                if st.button("Create Series", key="create_series_button"):
                    if new_series_name:
                        try:
                            # Create the series
                            series_id = self.series_registry.create_series(
                                new_series_name, publisher_id, multi_publisher, description
                            )
                            
                            # Assign the book to the series
                            _, sequence_number = self.series_assigner.assign_book_to_series(
                                metadata, new_series_name, publisher_id=publisher_id
                            )
                            
                            st.success(f"Created series '{new_series_name}' and assigned book as #{sequence_number}")
                            
                            if on_change:
                                on_change()
                                
                        except Exception as e:
                            st.error(f"Error creating series: {e}")
                    else:
                        st.error("Series name cannot be empty")
                        
        else:
            # Find the selected series option
            selected_option = next((option for option in series_options if option["name"] == selected_series), None)
            
            if selected_option:
                # Show series information
                st.write(f"Publisher: {selected_option['publisher_id']}")
                st.write(f"Books in series: {selected_option['book_count']}")
                
                if selected_option["description"]:
                    st.write(f"Description: {selected_option['description']}")
                
                # Allow selecting or auto-assigning sequence number
                sequence_options = ["Auto-assign", "Specify"]
                sequence_choice = st.radio(
                    "Sequence Number",
                    options=sequence_options,
                    key="sequence_choice"
                )
                
                if sequence_choice == "Auto-assign":
                    # Use next available sequence number
                    sequence_number = selected_option["next_sequence"]
                    st.write(f"Next available sequence number: {sequence_number}")
                else:
                    # Allow specifying a sequence number
                    sequence_number = st.number_input(
                        "Sequence Number",
                        min_value=1,
                        value=int(metadata.series_number) if metadata.series_number.isdigit() else selected_option["next_sequence"],
                        key="sequence_number"
                    )
                
                # Button to assign the book to the series
                if st.button("Assign to Series", key="assign_series_button"):
                    try:
                        # Assign the book to the series
                        _, assigned_sequence = self.series_assigner.assign_book_to_series(
                            metadata, selected_series, sequence_number, publisher_id
                        )
                        
                        st.success(f"Assigned book to series '{selected_series}' as #{assigned_sequence}")
                        
                        if on_change:
                            on_change()
                            
                    except Exception as e:
                        st.error(f"Error assigning book to series: {e}")
    
    def render_series_manager(self, publisher_id: str) -> None:
        """
        Render a UI component for managing series.
        
        Args:
            publisher_id: ID of the publisher
        """
        st.subheader("Series Management")
        
        # Get all series for the publisher
        series_list = self.series_registry.get_series_for_publisher(publisher_id)
        
        if not series_list:
            st.write("No series found for this publisher.")
            
        else:
            # Show series in a table
            series_data = []
            for series in series_list:
                # Get books in the series
                try:
                    books = self.series_registry.get_books_in_series(series.id)
                    book_count = len(books)
                except Exception:
                    book_count = 0
                
                # Add series information
                series_data.append({
                    "ID": series.id,
                    "Name": series.name,
                    "Books": book_count,
                    "Multi-Publisher": "Yes" if series.multi_publisher else "No",
                    "Created": series.creation_date.strftime("%Y-%m-%d")
                })
            
            # Display series table
            st.table(series_data)
            
            # Series details and editing
            st.subheader("Edit Series")
            
            # Select a series to edit
            selected_series_name = st.selectbox(
                "Select Series",
                options=[series.name for series in series_list],
                key="edit_series_selector"
            )
            
            # Find the selected series
            selected_series = next((series for series in series_list if series.name == selected_series_name), None)
            
            if selected_series:
                # Show series details
                with st.expander("Series Details", expanded=True):
                    # Edit series name
                    new_name = st.text_input("Name", value=selected_series.name, key="edit_series_name")
                    
                    # Edit multi-publisher flag
                    multi_publisher = st.checkbox(
                        "Allow multiple publishers",
                        value=selected_series.multi_publisher,
                        key="edit_multi_publisher"
                    )
                    
                    # Edit description
                    description = st.text_area(
                        "Description",
                        value=selected_series.description or "",
                        key="edit_series_description"
                    )
                    
                    # Update button
                    if st.button("Update Series", key="update_series_button"):
                        try:
                            # Update the series
                            updates = {
                                "name": new_name,
                                "multi_publisher": multi_publisher,
                                "description": description
                            }
                            
                            self.series_registry.update_series(selected_series.id, updates)
                            st.success(f"Updated series '{new_name}'")
                            
                        except Exception as e:
                            st.error(f"Error updating series: {e}")
                    
                    # Delete button
                    if st.button("Delete Series", key="delete_series_button"):
                        try:
                            # Try to delete the series
                            self.series_registry.delete_series(selected_series.id)
                            st.success(f"Deleted series '{selected_series.name}'")
                            
                        except Exception as e:
                            st.error(f"Error deleting series: {e}")
                            
                            # Show force delete option
                            if "assigned books" in str(e):
                                if st.button("Force Delete (will remove all books from series)", key="force_delete_button"):
                                    try:
                                        self.series_registry.delete_series(selected_series.id, force=True)
                                        st.success(f"Force deleted series '{selected_series.name}'")
                                    except Exception as e2:
                                        st.error(f"Error force deleting series: {e2}")
                
                # Show books in the series
                try:
                    books = self.series_registry.get_books_in_series(selected_series.id)
                    
                    if books:
                        st.subheader("Books in Series")
                        
                        # Prepare book data
                        book_data = []
                        for book in books:
                            book_data.append({
                                "ID": book.book_id,
                                "Sequence": book.sequence_number,
                                "Added": book.addition_date.strftime("%Y-%m-%d")
                            })
                        
                        # Display book table
                        st.table(book_data)
                        
                        # Reorder books
                        st.subheader("Reorder Books")
                        
                        # Select a book to reorder
                        selected_book_id = st.selectbox(
                            "Select Book",
                            options=[book.book_id for book in books],
                            key="reorder_book_selector"
                        )
                        
                        # Find the selected book
                        selected_book = next((book for book in books if book.book_id == selected_book_id), None)
                        
                        if selected_book:
                            # Input new sequence number
                            new_sequence = st.number_input(
                                "New Sequence Number",
                                min_value=1,
                                value=selected_book.sequence_number,
                                key="new_sequence_number"
                            )
                            
                            # Update button
                            if st.button("Update Sequence", key="update_sequence_button"):
                                try:
                                    # Remove the book from the series
                                    self.series_registry.remove_book_from_series(selected_series.id, selected_book_id)
                                    
                                    # Add it back with the new sequence number
                                    self.series_registry.add_book_to_series(
                                        selected_series.id, selected_book_id, new_sequence
                                    )
                                    
                                    st.success(f"Updated sequence number to {new_sequence}")
                                    
                                except Exception as e:
                                    st.error(f"Error updating sequence number: {e}")
                    else:
                        st.write("No books in this series.")
                        
                except Exception as e:
                    st.error(f"Error loading books: {e}")
        
        # Create new series
        st.subheader("Create New Series")
        
        new_series_name = st.text_input("Series Name", key="new_series_name_manager")
        multi_publisher = st.checkbox("Allow multiple publishers", key="multi_publisher_manager")
        description = st.text_area("Description", key="series_description_manager")
        
        if st.button("Create Series", key="create_series_button_manager"):
            if new_series_name:
                try:
                    # Create the series
                    series_id = self.series_registry.create_series(
                        new_series_name, publisher_id, multi_publisher, description
                    )
                    
                    st.success(f"Created series '{new_series_name}'")
                    
                except Exception as e:
                    st.error(f"Error creating series: {e}")
            else:
                st.error("Series name cannot be empty")


# Example usage in a Streamlit page
def render_series_page():
    """Render a Streamlit page for series management."""
    st.title("Series Management")
    
    # Create registry and assigner
    registry = SeriesRegistry()
    assigner = SeriesAssigner(registry)
    ui = SeriesUIIntegration(registry, assigner)
    
    # Get publisher ID (in a real app, this would come from authentication)
    publisher_id = st.text_input("Publisher ID", value="test-publisher")
    
    # Render series manager
    ui.render_series_manager(publisher_id)


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Render the page
    render_series_page()