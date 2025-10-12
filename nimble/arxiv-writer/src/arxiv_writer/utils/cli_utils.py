"""
CLI utility functions for arxiv-writer.
"""

import json
import yaml
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging
from datetime import datetime

from ..core.exceptions import ArxivWriterError, ConfigurationError, ValidationError

logger = logging.getLogger(__name__)


def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load JSON data from file with error handling.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded JSON data
        
    Raises:
        ArxivWriterError: If file cannot be loaded
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise ArxivWriterError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ArxivWriterError(f"Invalid JSON in file {file_path}: {e}")
    except Exception as e:
        raise ArxivWriterError(f"Failed to load file {file_path}: {e}")


def save_json_file(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Save data to JSON file with error handling.
    
    Args:
        data: Data to save
        file_path: Output file path
        indent: JSON indentation level
        
    Raises:
        ArxivWriterError: If file cannot be saved
    """
    file_path = Path(file_path)
    
    try:
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, default=str, ensure_ascii=False)
    except Exception as e:
        raise ArxivWriterError(f"Failed to save file {file_path}: {e}")


def load_yaml_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load YAML data from file with error handling.
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Loaded YAML data
        
    Raises:
        ArxivWriterError: If file cannot be loaded
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise ArxivWriterError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ArxivWriterError(f"Invalid YAML in file {file_path}: {e}")
    except Exception as e:
        raise ArxivWriterError(f"Failed to load file {file_path}: {e}")


def save_yaml_file(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """
    Save data to YAML file with error handling.
    
    Args:
        data: Data to save
        file_path: Output file path
        
    Raises:
        ArxivWriterError: If file cannot be saved
    """
    file_path = Path(file_path)
    
    try:
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    except Exception as e:
        raise ArxivWriterError(f"Failed to save file {file_path}: {e}")


def validate_file_format(file_path: Union[str, Path], allowed_formats: List[str]) -> str:
    """
    Validate file format based on extension.
    
    Args:
        file_path: Path to file
        allowed_formats: List of allowed file extensions (without dots)
        
    Returns:
        File format (extension without dot)
        
    Raises:
        ValidationError: If format is not allowed
    """
    file_path = Path(file_path)
    file_format = file_path.suffix.lower().lstrip('.')
    
    if file_format not in allowed_formats:
        raise ValidationError(
            f"Unsupported file format '{file_format}'. "
            f"Allowed formats: {', '.join(allowed_formats)}"
        )
    
    return file_format


def create_backup_file(file_path: Union[str, Path]) -> Path:
    """
    Create a backup of an existing file.
    
    Args:
        file_path: Path to file to backup
        
    Returns:
        Path to backup file
        
    Raises:
        ArxivWriterError: If backup cannot be created
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise ArxivWriterError(f"Cannot backup non-existent file: {file_path}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f".{timestamp}.backup{file_path.suffix}")
    
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        raise ArxivWriterError(f"Failed to create backup: {e}")


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get comprehensive file information.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file information
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {"exists": False, "path": str(file_path)}
    
    stat = file_path.stat()
    
    return {
        "exists": True,
        "path": str(file_path),
        "name": file_path.name,
        "stem": file_path.stem,
        "suffix": file_path.suffix,
        "size_bytes": stat.st_size,
        "size_formatted": format_file_size(stat.st_size),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "is_file": file_path.is_file(),
        "is_dir": file_path.is_dir(),
        "is_symlink": file_path.is_symlink()
    }


def find_files_by_pattern(
    directory: Union[str, Path],
    patterns: List[str],
    recursive: bool = True,
    exclude_patterns: Optional[List[str]] = None
) -> List[Path]:
    """
    Find files matching patterns in directory.
    
    Args:
        directory: Directory to search
        patterns: List of glob patterns to match
        recursive: Whether to search recursively
        exclude_patterns: Optional patterns to exclude
        
    Returns:
        List of matching file paths
    """
    directory = Path(directory)
    exclude_patterns = exclude_patterns or []
    
    if not directory.exists():
        return []
    
    found_files = []
    
    for pattern in patterns:
        if recursive:
            matches = directory.rglob(pattern)
        else:
            matches = directory.glob(pattern)
        
        for match in matches:
            if match.is_file():
                # Check if file should be excluded
                should_exclude = False
                for exclude_pattern in exclude_patterns:
                    if match.match(exclude_pattern):
                        should_exclude = True
                        break
                
                if not should_exclude:
                    found_files.append(match)
    
    return sorted(set(found_files))


def create_directory_structure(base_path: Union[str, Path], structure: Dict[str, Any]) -> None:
    """
    Create directory structure from nested dictionary.
    
    Args:
        base_path: Base directory path
        structure: Nested dictionary representing directory structure
    """
    base_path = Path(base_path)
    
    for name, content in structure.items():
        path = base_path / name
        
        if isinstance(content, dict):
            # It's a directory
            path.mkdir(parents=True, exist_ok=True)
            create_directory_structure(path, content)
        else:
            # It's a file
            path.parent.mkdir(parents=True, exist_ok=True)
            if content is not None:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(str(content))
            else:
                path.touch()


def validate_directory_structure(
    base_path: Union[str, Path],
    required_structure: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate that directory structure matches requirements.
    
    Args:
        base_path: Base directory to validate
        required_structure: Required structure specification
        
    Returns:
        Validation results
    """
    base_path = Path(base_path)
    results = {
        "valid": True,
        "missing_directories": [],
        "missing_files": [],
        "extra_items": [],
        "errors": []
    }
    
    if not base_path.exists():
        results["valid"] = False
        results["errors"].append(f"Base directory does not exist: {base_path}")
        return results
    
    def check_structure(current_path: Path, structure: Dict[str, Any], path_prefix: str = ""):
        for name, content in structure.items():
            item_path = current_path / name
            full_name = f"{path_prefix}/{name}" if path_prefix else name
            
            if isinstance(content, dict):
                # It's a directory
                if not item_path.exists():
                    results["missing_directories"].append(full_name)
                    results["valid"] = False
                elif item_path.is_file():
                    results["errors"].append(f"Expected directory but found file: {full_name}")
                    results["valid"] = False
                else:
                    # Recursively check subdirectory
                    check_structure(item_path, content, full_name)
            else:
                # It's a file
                if not item_path.exists():
                    results["missing_files"].append(full_name)
                    results["valid"] = False
                elif item_path.is_dir():
                    results["errors"].append(f"Expected file but found directory: {full_name}")
                    results["valid"] = False
    
    check_structure(base_path, required_structure)
    return results


def generate_cli_report(
    operation: str,
    success: bool,
    details: Dict[str, Any],
    output_file: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Generate a standardized CLI operation report.
    
    Args:
        operation: Name of the operation performed
        success: Whether the operation was successful
        details: Operation-specific details
        output_file: Optional file to save report to
        
    Returns:
        Report data
    """
    report = {
        "operation": operation,
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "details": details,
        "summary": {
            "status": "SUCCESS" if success else "FAILED",
            "duration": details.get("duration"),
            "items_processed": details.get("items_processed", 0),
            "errors": details.get("errors", []),
            "warnings": details.get("warnings", [])
        }
    }
    
    if output_file:
        save_json_file(report, output_file)
    
    return report


def format_cli_output(
    message: str,
    level: str = "info",
    prefix: Optional[str] = None,
    color: bool = True
) -> str:
    """
    Format CLI output message with appropriate styling.
    
    Args:
        message: Message to format
        level: Message level (info, success, warning, error)
        prefix: Optional prefix to add
        color: Whether to use color formatting
        
    Returns:
        Formatted message
    """
    if not color:
        return f"{prefix} {message}" if prefix else message
    
    # Define color codes
    colors = {
        "info": "\033[94m",      # Blue
        "success": "\033[92m",   # Green
        "warning": "\033[93m",   # Yellow
        "error": "\033[91m",     # Red
        "reset": "\033[0m"       # Reset
    }
    
    # Define prefixes
    prefixes = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    color_code = colors.get(level, colors["info"])
    emoji_prefix = prefixes.get(level, "")
    
    formatted_prefix = prefix or emoji_prefix
    formatted_message = f"{color_code}{formatted_prefix} {message}{colors['reset']}"
    
    return formatted_message


def parse_key_value_pairs(pairs: List[str]) -> Dict[str, str]:
    """
    Parse key=value pairs from command line arguments.
    
    Args:
        pairs: List of key=value strings
        
    Returns:
        Dictionary of parsed key-value pairs
        
    Raises:
        ValidationError: If pairs are malformed
    """
    result = {}
    
    for pair in pairs:
        if '=' not in pair:
            raise ValidationError(f"Invalid key=value pair: {pair}")
        
        key, value = pair.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        if not key:
            raise ValidationError(f"Empty key in pair: {pair}")
        
        result[key] = value
    
    return result


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Prompt user for confirmation.
    
    Args:
        message: Confirmation message
        default: Default response if user just presses enter
        
    Returns:
        True if user confirms, False otherwise
    """
    suffix = " [Y/n]" if default else " [y/N]"
    
    try:
        response = input(f"{message}{suffix}: ").strip().lower()
        
        if not response:
            return default
        
        return response in ['y', 'yes', 'true', '1']
    except (KeyboardInterrupt, EOFError):
        return False


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

de
f load_context_data(context_file: Union[str, Path]) -> Dict[str, Any]:
    """
    Load context data from file.
    
    Args:
        context_file: Path to context data file
        
    Returns:
        Loaded context data
    """
    context_file = Path(context_file)
    
    if not context_file.exists():
        raise ArxivWriterError(f"Context file not found: {context_file}")
    
    file_format = validate_file_format(context_file, ['json', 'yaml', 'yml'])
    
    if file_format == 'json':
        return load_json_file(context_file)
    else:
        return load_yaml_file(context_file)


def validate_output_directory(output_dir: Union[str, Path]) -> Path:
    """
    Validate and create output directory if needed.
    
    Args:
        output_dir: Output directory path
        
    Returns:
        Validated output directory path
        
    Raises:
        ValidationError: If directory cannot be created or accessed
    """
    output_dir = Path(output_dir)
    
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Test write access
        test_file = output_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        
        return output_dir
    except Exception as e:
        raise ValidationError(f"Cannot access output directory {output_dir}: {e}")


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    format_string: Optional[str] = None
) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level
        log_file: Optional log file path
        format_string: Optional custom format string
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[
            logging.StreamHandler(),
            *([] if log_file is None else [logging.FileHandler(log_file)])
        ]
    )