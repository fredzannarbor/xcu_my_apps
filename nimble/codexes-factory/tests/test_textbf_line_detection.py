"""
Unit tests for the textbf line detection regex pattern.

This module tests the regex pattern used to count \textbf commands that appear
at the beginning of lines in LaTeX content, addressing the bug in prepress.py
where the system incorrectly counted any \textbf command after a newline.
"""

import re
import pytest


def count_line_beginning_textbf(content: str) -> int:
    """
    Count \textbf commands that appear at the beginning of lines.
    
    This function implements the regex pattern that will be used to fix
    the bug in prepress.py.
    
    Args:
        content: LaTeX content string to analyze
        
    Returns:
        Number of \textbf commands at line beginnings
    """
    if not content:
        return 0
    
    # Count \textbf commands that appear at the beginning of lines
    return len(re.findall(r'^\\textbf', content, re.MULTILINE))


class TestTextbfLineDetection:
    """Test cases for the textbf line detection regex pattern."""
    
    def test_textbf_at_line_beginning_single(self):
        """Test that \textbf at the beginning of a line is counted."""
        content = "\\textbf{First mnemonic}"
        assert count_line_beginning_textbf(content) == 1
    
    def test_textbf_at_line_beginning_multiple(self):
        """Test that multiple \textbf commands at line beginnings are counted."""
        content = """\\textbf{First mnemonic}
Some content here
\\textbf{Second mnemonic}
More content
\\textbf{Third mnemonic}"""
        assert count_line_beginning_textbf(content) == 3
    
    def test_textbf_with_leading_whitespace_not_counted(self):
        """Test that \textbf with leading whitespace is not counted."""
        content = """\\textbf{Should count}
    \\textbf{Should not count - has leading spaces}
\t\\textbf{Should not count - has leading tab}
 \t \\textbf{Should not count - mixed whitespace}"""
        assert count_line_beginning_textbf(content) == 1
    
    def test_textbf_in_middle_of_line_not_counted(self):
        """Test that \textbf in the middle of a line is not counted."""
        content = """\\textbf{Should count}
Some text with \\textbf{inline bold} in middle
Another line with text \\textbf{at end}"""
        assert count_line_beginning_textbf(content) == 1
    
    def test_mixed_scenarios(self):
        """Test a complex mix of different \textbf positioning scenarios."""
        content = """\\textbf{First mnemonic - should count}
Some intro text
\\textbf{Second mnemonic - should count}
    \\textbf{This should not count - has leading spaces}
Regular text with \\textbf{inline bold} text
\\textbf{Third mnemonic - should count}
\t\\textbf{Tab-indented - should not count}
Final line with \\textbf{end bold}"""
        assert count_line_beginning_textbf(content) == 3
    
    def test_empty_string(self):
        """Test that empty string returns 0."""
        assert count_line_beginning_textbf("") == 0
    
    def test_none_input(self):
        """Test that None input returns 0."""
        assert count_line_beginning_textbf(None) == 0
    
    def test_no_textbf_commands(self):
        """Test that content without \textbf commands returns 0."""
        content = """This is regular text
With multiple lines
But no textbf commands
Just normal content"""
        assert count_line_beginning_textbf(content) == 0
    
    def test_textbf_variations_not_matched(self):
        """Test that variations of textbf are not incorrectly matched."""
        content = """\\textbf{Should count}
\\textit{Should not count}
\\textsc{Should not count}
\\textbold{Should not count}
text\\textbf{Should not count}"""
        assert count_line_beginning_textbf(content) == 1
    
    def test_multiple_textbf_same_line(self):
        """Test multiple \textbf commands on the same line."""
        content = """\\textbf{First} and \\textbf{Second} on same line
    \\textbf{Indented first} and \\textbf{indented second}
\\textbf{Line start} then \\textbf{middle}"""
        # Only the ones at line beginnings should count
        assert count_line_beginning_textbf(content) == 2
    
    def test_textbf_after_empty_lines(self):
        """Test \textbf commands after empty lines."""
        content = """\\textbf{First mnemonic}

\\textbf{After empty line}


\\textbf{After multiple empty lines}"""
        assert count_line_beginning_textbf(content) == 3
    
    def test_textbf_with_different_content(self):
        """Test \textbf with various content inside braces."""
        content = """\\textbf{Simple text}
\\textbf{Text with spaces and punctuation!}
\\textbf{Multi-word content here}
\\textbf{}
\\textbf{123 numbers}"""
        assert count_line_beginning_textbf(content) == 5
    
    def test_windows_line_endings(self):
        """Test that Windows line endings (CRLF) work correctly."""
        content = "\\textbf{First mnemonic}\r\n\\textbf{Second mnemonic}\r\nRegular text"
        assert count_line_beginning_textbf(content) == 2
    
    def test_mixed_line_endings(self):
        """Test mixed line endings."""
        content = "\\textbf{First}\n\\textbf{Second}\r\n\\textbf{Third}\n\\textbf{Fourth}"
        # Should handle different line ending styles (LF and CRLF)
        assert count_line_beginning_textbf(content) == 4
    
    def test_real_world_mnemonics_example(self):
        """Test with a realistic mnemonics LaTeX content example."""
        content = """% Mnemonics section
\\section{Memory Aids}

\\textbf{HOMES} - Great Lakes (Huron, Ontario, Michigan, Erie, Superior)
Remember the five Great Lakes with this simple acronym.

\\textbf{ROY G. BIV} - Colors of the rainbow
    This is indented and should not count

\\textbf{Please Excuse My Dear Aunt Sally} - Order of operations
Mathematical operations: Parentheses, Exponents, Multiplication, Division, Addition, Subtraction.

Some explanatory text with \\textbf{inline formatting} here.

\\textbf{Every Good Boy Does Fine} - Musical notes on staff lines
The notes E, G, B, D, F on the treble clef staff lines."""
        
        # Should count: HOMES, ROY G. BIV, Please Excuse..., Every Good Boy...
        # Should not count: the indented one and the inline one
        assert count_line_beginning_textbf(content) == 4


class TestRegexPatternDetails:
    """Test specific aspects of the regex pattern implementation."""
    
    def test_regex_pattern_directly(self):
        """Test the regex pattern directly without the wrapper function."""
        pattern = r'^\\textbf'
        flags = re.MULTILINE
        
        content = """\\textbf{Should match}
    \\textbf{Should not match}
\\textbf{Should match}"""
        
        matches = re.findall(pattern, content, flags)
        assert len(matches) == 2
    
    def test_multiline_flag_necessity(self):
        """Test that MULTILINE flag is necessary for correct behavior."""
        pattern = r'^\\textbf'
        content = """Some text
\\textbf{This should match with MULTILINE}
More text"""
        
        # Without MULTILINE flag, ^ only matches start of string
        matches_without_multiline = re.findall(pattern, content)
        assert len(matches_without_multiline) == 0
        
        # With MULTILINE flag, ^ matches start of each line
        matches_with_multiline = re.findall(pattern, content, re.MULTILINE)
        assert len(matches_with_multiline) == 1
    
    def test_backslash_escaping(self):
        """Test that backslashes are properly escaped in the pattern."""
        # The pattern should match literal \textbf, not treat \ as escape
        content = "textbf{Should not match - missing backslash}\n\\textbf{Should match}"
        matches = re.findall(r'^\\textbf', content, re.MULTILINE)
        assert len(matches) == 1


if __name__ == "__main__":
    # Run the tests if this file is executed directly
    pytest.main([__file__, "-v"])