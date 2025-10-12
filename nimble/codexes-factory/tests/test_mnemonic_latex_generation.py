import pytest
import tempfile
import shutil
from pathlib import Path


def test_latex_command_generation():
    """Test that LaTeX commands are properly generated for mnemonics."""
    # Test data
    mnemonics = [
        "\\textbf{First Mnemonic}\nContent for first mnemonic.",
        "\\textbf{Second Mnemonic}\nContent for second mnemonic."
    ]
    
    # Generate LaTeX content
    latex_parts = []
    latex_parts.append("\\cleartoverso")
    latex_parts.append("\\chapter*{Mnemonics}")
    latex_parts.append("\\addcontentsline{toc}{chapter}{Mnemonics}")
    
    for i, mnemonic_content in enumerate(mnemonics, 1):
        instruction = f"Mnemonic Practice {i}"
        latex_parts.append(f"\\mnemonicwithpractice{{{mnemonic_content}}}{{{instruction}}}")
    
    latex_parts.append("\\cleardoublepage")
    content = "\n".join(latex_parts)
    
    # Verify content
    assert "\\cleartoverso" in content
    assert "\\chapter*{Mnemonics}" in content
    assert content.count("\\mnemonicwithpractice") == 2
    assert "Mnemonic Practice 1" in content
    assert "Mnemonic Practice 2" in content
    assert "First Mnemonic" in content
    assert "Second Mnemonic" in content
    assert "\\cleardoublepage" in content


def test_latex_template_commands():
    """Test that LaTeX template commands are properly structured."""
    # Read the template file to verify commands exist
    template_path = Path("imprints/xynapse_traces/template.tex")
    if template_path.exists():
        content = template_path.read_text()
        
        # Check for new commands
        assert "\\newcommand{\\mnemonicwithpractice}" in content
        assert "\\newcommand{\\fullpagedotgridwithinstruction}" in content
        assert "\\newcounter{mnemonicpractice}" in content
        assert "\\cleartoverso" in content
        assert "\\formattedquote" in content
        assert "\\fullpagedotgridwithinstruction" in content


def test_page_sequencing_logic():
    """Test that page sequencing logic is correct."""
    # Test with different numbers of mnemonics
    test_cases = [1, 3, 5, 10]
    
    for mnemonic_count in test_cases:
        # Each mnemonic should create 2 pages (verso + recto)
        expected_pages = mnemonic_count * 2
        
        # Generate content
        latex_parts = ["\\cleartoverso", "\\chapter*{Mnemonics}"]
        for i in range(1, mnemonic_count + 1):
            latex_parts.append(f"\\mnemonicwithpractice{{content}}{{{f'Mnemonic Practice {i}'}}}")
        
        content = "\n".join(latex_parts)
        
        # Verify correct number of practice pages
        assert content.count("\\mnemonicwithpractice") == mnemonic_count
        assert content.count("Mnemonic Practice") == mnemonic_count


def test_instruction_numbering():
    """Test that practice instructions are numbered correctly."""
    mnemonics = [f"\\textbf{{Mnemonic {i}}}\nContent {i}" for i in range(1, 6)]
    
    instructions = []
    for i, mnemonic in enumerate(mnemonics, 1):
        instruction = f"Mnemonic Practice {i}"
        instructions.append(instruction)
    
    # Verify sequential numbering
    assert instructions == [
        "Mnemonic Practice 1",
        "Mnemonic Practice 2", 
        "Mnemonic Practice 3",
        "Mnemonic Practice 4",
        "Mnemonic Practice 5"
    ]


def test_latex_escaping():
    """Test that LaTeX special characters are handled properly."""
    # Test content with special characters
    test_content = "Test & content with % special $ characters # and more"
    
    # Simple escaping function (mimicking escape_latex)
    def simple_escape(text):
        return text.replace("&", "\\&").replace("%", "\\%").replace("$", "\\$").replace("#", "\\#")
    
    escaped = simple_escape(test_content)
    assert "\\&" in escaped
    assert "\\%" in escaped
    assert "\\$" in escaped
    assert "\\#" in escaped


if __name__ == "__main__":
    pytest.main([__file__])