"""
Path selection UI component for batch operations.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import streamlit as st


def get_predefined_paths() -> Dict[str, Path]:
    """
    Get predefined paths for imprint configs and directories.

    Returns:
        Dictionary mapping path names to Path objects
    """
    base_path = Path(".")

    return {
        "configs/imprints/": base_path / "configs" / "imprints",
        "configs/imprints_draft/": base_path / "configs" / "imprints_draft",
        "configs/imprints_staging/": base_path / "configs" / "imprints_staging",
        "configs/imprints_archive/": base_path / "configs" / "imprints_archive",
        "imprints/": base_path / "imprints",
        "imprints_in_development/": base_path / "imprints_in_development",
    }


def render_path_selector(
    allow_multi_select: bool = True,
    allow_custom_path: bool = True,
    filter_type: str = "all",  # "configs", "directories", "all"
    key_prefix: str = "batch_path"
) -> List[Path]:
    """
    Render path selection UI and return selected paths.

    Args:
        allow_multi_select: Whether to allow selecting multiple paths
        allow_custom_path: Whether to allow custom path entry
        filter_type: Type of paths to show ("configs", "directories", "all")
        key_prefix: Prefix for Streamlit widget keys

    Returns:
        List of selected Path objects
    """
    predefined_paths = get_predefined_paths()

    # Filter paths based on type
    if filter_type == "configs":
        filtered_paths = {k: v for k, v in predefined_paths.items() if k.startswith("configs/")}
    elif filter_type == "directories":
        filtered_paths = {k: v for k, v in predefined_paths.items() if k.startswith("imprints")}
    else:
        filtered_paths = predefined_paths

    selected_paths = []

    st.subheader("Select Source Path(s)")

    if allow_multi_select:
        # Use multiselect for multiple path selection
        selected_keys = st.multiselect(
            "Choose one or more paths:",
            options=list(filtered_paths.keys()),
            key=f"{key_prefix}_multiselect"
        )

        for key in selected_keys:
            path = filtered_paths[key]
            if path.exists():
                selected_paths.append(path)
            else:
                st.warning(f"⚠️ Path does not exist: {path}")
    else:
        # Use selectbox for single path selection
        selected_key = st.selectbox(
            "Choose a path:",
            options=[""] + list(filtered_paths.keys()),
            key=f"{key_prefix}_selectbox"
        )

        if selected_key:
            path = filtered_paths[selected_key]
            if path.exists():
                selected_paths.append(path)
            else:
                st.warning(f"⚠️ Path does not exist: {path}")

    # Custom path entry
    if allow_custom_path:
        st.markdown("---")
        custom_path_str = st.text_input(
            "Or enter a custom path:",
            key=f"{key_prefix}_custom",
            help="Enter an absolute or relative path"
        )

        if custom_path_str:
            custom_path = Path(custom_path_str)
            if custom_path.exists():
                if custom_path not in selected_paths:
                    selected_paths.append(custom_path)
                    st.success(f"✓ Added custom path: {custom_path}")
            else:
                st.error(f"❌ Custom path does not exist: {custom_path}")

    # Display selected paths summary
    if selected_paths:
        st.markdown("---")
        st.write(f"**Selected Paths ({len(selected_paths)}):**")
        for path in selected_paths:
            # Count files in each path
            if path.is_dir():
                json_files = list(path.glob("*.json"))
                # Exclude template files
                json_files = [f for f in json_files if "template" not in f.name.lower()]
                file_count = len(json_files)
                st.write(f"- `{path}` ({file_count} config files)")
            else:
                st.write(f"- `{path}`")

    return selected_paths


def get_configs_from_paths(paths: List[Path]) -> List[Path]:
    """
    Get all config files from the selected paths.

    Args:
        paths: List of directory paths to search

    Returns:
        List of config file paths
    """
    config_files = []

    for path in paths:
        if path.is_dir():
            # Get all JSON files, excluding templates
            json_files = list(path.glob("*.json"))
            for json_file in json_files:
                if "template" not in json_file.name.lower():
                    config_files.append(json_file)
        elif path.is_file() and path.suffix == ".json":
            config_files.append(path)

    return sorted(config_files)


def render_config_selector(
    config_files: List[Path],
    key_prefix: str = "batch_config"
) -> List[Path]:
    """
    Render config file selection UI.

    Args:
        config_files: List of available config files
        key_prefix: Prefix for Streamlit widget keys

    Returns:
        List of selected config file paths
    """
    if not config_files:
        st.warning("No config files found in selected paths.")
        return []

    st.subheader(f"Select Configs ({len(config_files)} available)")

    # Option to select all
    select_all = st.checkbox(
        "Select all configs",
        key=f"{key_prefix}_select_all"
    )

    if select_all:
        return config_files

    # Individual selection
    selected_files = []
    config_names = [f.stem for f in config_files]

    selected_names = st.multiselect(
        "Choose specific configs:",
        options=config_names,
        key=f"{key_prefix}_individual"
    )

    for name in selected_names:
        for config_file in config_files:
            if config_file.stem == name:
                selected_files.append(config_file)
                break

    if selected_files:
        st.info(f"✓ Selected {len(selected_files)} config file(s)")

    return selected_files


def display_path_stats(paths: List[Path]) -> Dict[str, Any]:
    """
    Display statistics about selected paths.

    Args:
        paths: List of paths to analyze

    Returns:
        Dictionary containing statistics
    """
    stats = {
        "total_paths": len(paths),
        "total_configs": 0,
        "by_directory": {}
    }

    for path in paths:
        if path.is_dir():
            json_files = list(path.glob("*.json"))
            json_files = [f for f in json_files if "template" not in f.name.lower()]
            count = len(json_files)
            stats["total_configs"] += count
            stats["by_directory"][str(path)] = count

    # Display in Streamlit
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Paths Selected", stats["total_paths"])

    with col2:
        st.metric("Total Config Files", stats["total_configs"])

    if stats["by_directory"]:
        st.write("**Files by Directory:**")
        for dir_path, count in stats["by_directory"].items():
            st.write(f"- {Path(dir_path).name}: {count} files")

    return stats
