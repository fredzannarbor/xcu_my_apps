"""
DataFrame utility functions for PyArrow compatibility and data cleaning.
"""

import pandas as pd
import numpy as np
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def clean_dataframe_for_pyarrow(df: pd.DataFrame, max_string_length: int = 10000) -> pd.DataFrame:
    """
    Clean a DataFrame to ensure PyArrow compatibility.

    This function fixes common issues that cause PyArrow conversion errors:
    - Mixed data types in columns
    - Overly long strings that cause memory issues
    - None/NaN handling in string columns
    - Integer columns with NaN values

    Args:
        df: Input DataFrame to clean
        max_string_length: Maximum allowed string length (truncate longer strings)

    Returns:
        Cleaned DataFrame that should be PyArrow compatible
    """
    if df is None or df.empty:
        return df

    df_cleaned = df.copy()

    for col in df_cleaned.columns:
        try:
            # Handle different column types
            if df_cleaned[col].dtype == 'object':
                # For object columns, ensure all values are strings or None
                df_cleaned[col] = df_cleaned[col].astype(str)
                # Replace 'nan' and 'None' strings with actual None
                df_cleaned[col] = df_cleaned[col].replace(['nan', 'None', '<NA>'], None)

                # Truncate overly long strings
                if max_string_length > 0:
                    df_cleaned[col] = df_cleaned[col].apply(
                        lambda x: x[:max_string_length] + '...' if isinstance(x, str) and len(x) > max_string_length else x
                    )

            elif df_cleaned[col].dtype in ['int64', 'int32', 'int16', 'int8']:
                # Handle integer columns with potential NaN values
                if df_cleaned[col].isnull().any():
                    # Convert to nullable integer type
                    df_cleaned[col] = df_cleaned[col].astype('Int64')

            elif df_cleaned[col].dtype in ['float64', 'float32']:
                # Ensure float columns are properly handled
                df_cleaned[col] = df_cleaned[col].astype('float64')

            # Check for mixed types and fix them
            unique_types = df_cleaned[col].apply(lambda x: type(x) if pd.notnull(x) else type(None)).unique()
            if len(unique_types) > 2:  # More than just the expected type + NoneType
                logger.warning(f"Column '{col}' has mixed types: {unique_types}. Converting to string.")
                df_cleaned[col] = df_cleaned[col].astype(str).replace('nan', None)

        except Exception as e:
            logger.warning(f"Error processing column '{col}': {e}. Converting to string as fallback.")
            df_cleaned[col] = df_cleaned[col].astype(str).replace('nan', None)

    return df_cleaned


def safe_dataframe_display(df: pd.DataFrame, use_container_width: bool = True, **kwargs) -> None:
    """
    Safely display a DataFrame in Streamlit with PyArrow compatibility.

    Args:
        df: DataFrame to display
        use_container_width: Whether to use container width (deprecated, use width instead)
        **kwargs: Additional arguments to pass to st.dataframe
    """
    import streamlit as st

    if df is None or df.empty:
        st.info("No data to display")
        return

    try:
        # Clean the DataFrame for PyArrow compatibility
        cleaned_df = clean_dataframe_for_pyarrow(df)

        # Handle deprecated use_container_width parameter
        display_kwargs = kwargs.copy()
        if use_container_width and 'width' not in display_kwargs:
            display_kwargs['width'] = 'stretch'
        elif 'use_container_width' in display_kwargs:
            # Remove deprecated parameter
            del display_kwargs['use_container_width']

        st.dataframe(cleaned_df, **display_kwargs)

    except Exception as e:
        logger.error(f"Error displaying DataFrame: {e}")
        st.error(f"Error displaying data: {str(e)}")

        # Fallback: try to display basic info
        try:
            st.write("**DataFrame Info:**")
            st.write(f"Shape: {df.shape}")
            st.write(f"Columns: {list(df.columns)}")
            st.write(f"Data types: {df.dtypes.to_dict()}")
        except:
            st.error("Could not display DataFrame information")


def convert_to_arrow_compatible_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert DataFrame columns to Arrow-compatible types.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with Arrow-compatible types
    """
    if df is None or df.empty:
        return df

    df_converted = df.copy()

    # Define type conversions for common problematic columns
    type_conversions = {
        'ISBN': 'str',
        'ASIN': 'str',
        'Title': 'str',
        'Author': 'str',
        'Publisher': 'str',
        'Imprint': 'str',
        'Format': 'str',
        'Sales Market': 'str',
        'Marketplace': 'str',
        'Currency': 'str'
    }

    for col in df_converted.columns:
        try:
            # Apply specific conversions if column name matches
            if col in type_conversions:
                target_type = type_conversions[col]
                if target_type == 'str':
                    df_converted[col] = df_converted[col].astype(str).replace('nan', None)
                else:
                    df_converted[col] = df_converted[col].astype(target_type)

            # Handle numeric columns with NaN
            elif df_converted[col].dtype in ['int64', 'int32'] and df_converted[col].isnull().any():
                df_converted[col] = df_converted[col].astype('Int64')

        except Exception as e:
            logger.warning(f"Could not convert column '{col}' to Arrow-compatible type: {e}")

    return df_converted