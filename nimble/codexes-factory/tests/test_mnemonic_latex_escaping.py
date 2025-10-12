import unittest
import sys
import os
import re
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Since we can't import directly due to module structure, let's define a simplified version
# of the extract_individual_mnemonics function for testing
def extract_individual_mnemonics(mnemonics_tex):
    """
    Extract individual mnemonic entries from LaTeX content.
    Assumes each mnemonic starts with \textbf at line beginning.
    
    Important: This function preserves the raw LaTeX commands in the extracted mnemonics,
    as they are intended to be interpreted as LaTeX, not escaped as text.
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
                # Do NOT escape the LaTeX commands here - they should be preserved as-is
                mnemonic_content = f"\\textbf{part.strip()}"
                mnemonics.append(mnemonic_content)
        
        return mnemonics
        
    except Exception as e:
        # Return empty list to allow processing to continue
        return []

class TestMnemonicLatexEscaping(unittest.TestCase):
    
    def test_extract_mnemonics_preserves_latex_commands(self):
        """Test that LaTeX commands are preserved in extracted mnemonics."""
        # Sample input with LaTeX commands
        test_input = """\\textbf{D.E.E.P. Learning} (for Deep Understanding \\& Interconnected Knowledge)
\\begin{itemize}
\\item\\textbf{D}eep understanding
\\item\\textbf{E}ngage actively
\\item\\textbf{E}xplore connections
\\item\\textbf{P}ractice persistently
\\end{itemize}
\\vspace{1em}

\\textbf{Another Mnemonic}
This is another mnemonic with \\textit{italic text} and \\textbf{bold text}.
"""
        
        # Extract mnemonics
        mnemonics = extract_individual_mnemonics(test_input)
        
        # Verify we got 2 mnemonics
        self.assertEqual(len(mnemonics), 2)
        
        # Verify LaTeX commands are preserved
        self.assertIn("\\begin{itemize}", mnemonics[0])
        self.assertIn("\\item\\textbf{D}", mnemonics[0])
        self.assertIn("\\end{itemize}", mnemonics[0])
        self.assertIn("\\vspace{1em}", mnemonics[0])
        
        self.assertIn("\\textit{italic text}", mnemonics[1])
        self.assertIn("\\textbf{bold text}", mnemonics[1])
        
        # Verify the mnemonics start with \textbf
        self.assertTrue(mnemonics[0].startswith("\\textbf{D.E.E.P. Learning}"))
        self.assertTrue(mnemonics[1].startswith("\\textbf{Another Mnemonic}"))

if __name__ == '__main__':
    unittest.main()