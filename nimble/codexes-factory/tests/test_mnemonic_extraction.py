import pytest
import re


def extract_individual_mnemonics(mnemonics_tex):
    """
    Extract individual mnemonic entries from LaTeX content.
    Assumes each mnemonic starts with \textbf at line beginning.
    """
    if not mnemonics_tex or not isinstance(mnemonics_tex, str):
        return []
    
    try:
        # Split on line-beginning \textbf commands
        pattern = r'^\\textbf'
        parts = re.split(pattern, mnemonics_tex, flags=re.MULTILINE)
        
        mnemonics = []
        for i, part in enumerate(parts[1:], 1):  # Skip first empty part
            if part.strip():  # Only process non-empty parts
                # Reconstruct the mnemonic with its \textbf command
                mnemonic_content = f"\\textbf{part.strip()}"
                mnemonics.append(mnemonic_content)
        
        return mnemonics
        
    except Exception as e:
        # Return empty list to allow processing to continue
        return []


def test_extract_multiple_mnemonics():
    """Test extraction of multiple mnemonics from LaTeX content."""
    content = """\\textbf{First Mnemonic}
This is the first mnemonic content.

\\textbf{Second Mnemonic}
This is the second mnemonic content.

\\textbf{Third Mnemonic}
This is the third mnemonic content."""
    
    result = extract_individual_mnemonics(content)
    assert len(result) == 3
    assert result[0].startswith("\\textbf{First Mnemonic}")
    assert result[1].startswith("\\textbf{Second Mnemonic}")
    assert result[2].startswith("\\textbf{Third Mnemonic}")


def test_extract_single_mnemonic():
    """Test extraction of single mnemonic."""
    content = """\\textbf{Single Mnemonic}
This is a single mnemonic."""
    
    result = extract_individual_mnemonics(content)
    assert len(result) == 1
    assert result[0].startswith("\\textbf{Single Mnemonic}")


def test_extract_empty_content():
    """Test extraction from empty content."""
    result = extract_individual_mnemonics("")
    assert result == []
    
    result = extract_individual_mnemonics(None)
    assert result == []


def test_extract_no_mnemonics():
    """Test extraction from content without mnemonics."""
    content = "This is just regular text without any mnemonics."
    result = extract_individual_mnemonics(content)
    assert result == []


def test_extract_malformed_content():
    """Test extraction from malformed content."""
    content = """Some text before
\\textbf{Valid Mnemonic}
Valid content here.
    \\textbf{Indented - should not match}
More text."""
    
    result = extract_individual_mnemonics(content)
    assert len(result) == 1
    assert result[0].startswith("\\textbf{Valid Mnemonic}")


def test_extract_with_whitespace():
    """Test extraction handles whitespace correctly."""
    content = """\\textbf{First Mnemonic}
Content with spaces.

\\textbf{Second Mnemonic}
More content."""
    
    result = extract_individual_mnemonics(content)
    assert len(result) == 2
    assert "Content with spaces." in result[0]
    assert "More content." in result[1]