import pytest
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add the src directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "imprints" / "xynapse_traces"))

from prepress import _create_content_tex_files


class TestMnemonicIntegration:
    """Integration tests for mnemonic practice layout processing."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.build_dir = self.temp_dir / "build"
        self.build_dir.mkdir(parents=True)
        self.templates_dir = self.temp_dir / "templates"
        self.templates_dir.mkdir(parents=True)
        
        # Create a minimal dot grid file
        (self.build_dir / "dotgrid.png").touch()
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_single_mnemonic_processing(self):
        """Test processing of a single mnemonic."""
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "mnemonics_tex": "\\textbf{Single Mnemonic}\nThis is a test mnemonic for memory."
        }
        
        _create_content_tex_files(data, self.build_dir, self.templates_dir)
        
        # Check that mnemonics.tex was created
        mnemonics_file = self.build_dir / "mnemonics.tex"
        assert mnemonics_file.exists()
        
        content = mnemonics_file.read_text()
        assert "\\chapter*{Mnemonics}" in content
        assert "\\mnemonicwithpractice" in content
        assert "Mnemonic Practice 1" in content
        assert "Single Mnemonic" in content
    
    def test_multiple_mnemonics_processing(self):
        """Test processing of multiple mnemonics."""
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "mnemonics_tex": """\\textbf{First Mnemonic}
This is the first test mnemonic.

\\textbf{Second Mnemonic}
This is the second test mnemonic.

\\textbf{Third Mnemonic}
This is the third test mnemonic."""
        }
        
        _create_content_tex_files(data, self.build_dir, self.templates_dir)
        
        mnemonics_file = self.build_dir / "mnemonics.tex"
        content = mnemonics_file.read_text()
        
        # Should have 3 mnemonic/practice pairs
        assert content.count("\\mnemonicwithpractice") == 3
        assert "Mnemonic Practice 1" in content
        assert "Mnemonic Practice 2" in content
        assert "Mnemonic Practice 3" in content
        assert "First Mnemonic" in content
        assert "Second Mnemonic" in content
        assert "Third Mnemonic" in content
    
    def test_empty_mnemonics_handling(self):
        """Test handling of empty mnemonic content."""
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "mnemonics_tex": ""
        }
        
        _create_content_tex_files(data, self.build_dir, self.templates_dir)
        
        # Should not create mnemonics.tex for empty content
        mnemonics_file = self.build_dir / "mnemonics.tex"
        assert not mnemonics_file.exists()
    
    def test_malformed_mnemonics_handling(self):
        """Test handling of malformed mnemonic content."""
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "mnemonics_tex": "This is not properly formatted mnemonic content."
        }
        
        _create_content_tex_files(data, self.build_dir, self.templates_dir)
        
        # Should not create mnemonics.tex for malformed content
        mnemonics_file = self.build_dir / "mnemonics.tex"
        assert not mnemonics_file.exists()
    
    def test_latex_escaping_in_mnemonics(self):
        """Test that special LaTeX characters are handled properly."""
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "mnemonics_tex": "\\textbf{Mnemonic with & special % characters}\nContent with $ and # symbols."
        }
        
        _create_content_tex_files(data, self.build_dir, self.templates_dir)
        
        mnemonics_file = self.build_dir / "mnemonics.tex"
        content = mnemonics_file.read_text()
        
        # Should contain the mnemonic content
        assert "\\mnemonicwithpractice" in content
        assert "Mnemonic Practice 1" in content
    
    def test_page_sequencing_validation(self):
        """Test that page sequencing is properly validated."""
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "mnemonics_tex": """\\textbf{First}
Content 1

\\textbf{Second}
Content 2"""
        }
        
        _create_content_tex_files(data, self.build_dir, self.templates_dir)
        
        mnemonics_file = self.build_dir / "mnemonics.tex"
        content = mnemonics_file.read_text()
        
        # Should start on verso page and have proper sequencing
        assert "\\cleartoverso" in content
        assert "\\cleardoublepage" in content
        assert content.count("\\mnemonicwithpractice") == 2
    
    def test_backward_compatibility(self):
        """Test that old-style mnemonic processing still works."""
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "mnemonics": "* First mnemonic item\n* Second mnemonic item"
        }
        
        _create_content_tex_files(data, self.build_dir, self.templates_dir)
        
        # Should fall back to old processing
        mnemonics_file = self.build_dir / "mnemonics.tex"
        if mnemonics_file.exists():
            content = mnemonics_file.read_text()
            assert "\\chapter*{Mnemonics}" in content
    
    def test_required_files_creation(self):
        """Test that all required files are created."""
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "mnemonics_tex": "\\textbf{Test Mnemonic}\nTest content."
        }
        
        _create_content_tex_files(data, self.build_dir, self.templates_dir)
        
        # Check that required files exist
        assert (self.build_dir / "title_page.tex").exists()
        assert (self.build_dir / "copyright_page.tex").exists()
        assert (self.build_dir / "mnemonics.tex").exists()
        
        # Check mnemonics directory
        mnemonics_dir = self.build_dir / "mnemonics"
        assert mnemonics_dir.exists()
        assert (mnemonics_dir / "mnemonics_content.tex").exists()


if __name__ == "__main__":
    pytest.main([__file__])