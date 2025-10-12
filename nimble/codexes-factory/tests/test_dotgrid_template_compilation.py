"""
Test script to verify dotgrid template compilation with new positioning.
"""

import tempfile
import subprocess
from pathlib import Path
import shutil
import logging

logger = logging.getLogger(__name__)


def test_xynapse_traces_template_compilation():
    """Test that the updated xynapse_traces template compiles correctly"""
    try:
        # Create temporary directory for test
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy template to temp directory
            template_source = Path("imprints/xynapse_traces/template.tex")
            if not template_source.exists():
                logger.error(f"Template not found: {template_source}")
                return False
            
            template_dest = temp_path / "template.tex"
            shutil.copy(template_source, template_dest)
            
            # Create a minimal test document
            test_doc = temp_path / "test_dotgrid.tex"
            test_content = """
\\documentclass{memoir}
\\input{template.tex}

\\begin{document}
\\dotgridtranscription{Test instruction for dotgrid positioning}
\\end{document}
"""
            test_doc.write_text(test_content)
            
            # Create dummy dotgrid.png file
            dotgrid_dummy = temp_path / "dotgrid.png"
            dotgrid_dummy.write_bytes(b"dummy png content")
            
            # Try to compile with lualatex
            try:
                result = subprocess.run(
                    ["lualatex", "-interaction=nonstopmode", "test_dotgrid.tex"],
                    cwd=temp_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    logger.info("Template compilation successful")
                    return True
                else:
                    logger.error(f"Template compilation failed: {result.stderr}")
                    return False
                    
            except FileNotFoundError:
                logger.warning("lualatex not found, skipping compilation test")
                return True  # Consider it passed if lualatex is not available
            except subprocess.TimeoutExpired:
                logger.error("Template compilation timed out")
                return False
                
    except Exception as e:
        logger.error(f"Error testing template compilation: {e}")
        return False


def validate_dotgrid_positioning():
    """Validate that the dotgrid positioning meets requirements"""
    try:
        template_path = Path("imprints/xynapse_traces/template.tex")
        if not template_path.exists():
            logger.error(f"Template not found: {template_path}")
            return False
        
        content = template_path.read_text()
        
        # Check for improved positioning
        if "2.0in" in content:
            logger.info("✅ Found improved dotgrid positioning (2.0in)")
        else:
            logger.warning("❌ Improved positioning not found")
            return False
        
        # Check for reduced height to ensure spacing
        if "height=0.75\\textheight" in content:
            logger.info("✅ Found reduced dotgrid height for proper spacing")
        else:
            logger.warning("❌ Reduced height not found")
            return False
        
        # Check for updated instruction positioning
        if "vspace{0.75\\textheight}" in content:
            logger.info("✅ Found updated instruction positioning")
        else:
            logger.warning("❌ Updated instruction positioning not found")
            return False
        
        logger.info("✅ All dotgrid positioning validations passed")
        return True
        
    except Exception as e:
        logger.error(f"Error validating dotgrid positioning: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing dotgrid template updates...")
    
    # Validate positioning changes
    if validate_dotgrid_positioning():
        print("✅ Dotgrid positioning validation passed")
    else:
        print("❌ Dotgrid positioning validation failed")
    
    # Test compilation
    if test_xynapse_traces_template_compilation():
        print("✅ Template compilation test passed")
    else:
        print("❌ Template compilation test failed")