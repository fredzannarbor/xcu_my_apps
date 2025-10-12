#!/usr/bin/env python3
"""
Test package installation in isolated Docker environments.
This script tests the package across different Python versions and operating systems.
"""

import subprocess
import sys
import os
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any


def run_command(cmd: List[str], cwd=None, check=True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd, 
        cwd=cwd, 
        capture_output=True, 
        text=True, 
        check=check
    )
    if result.stdout:
        print(f"STDOUT: {result.stdout}")
    if result.stderr and result.stderr.strip():
        print(f"STDERR: {result.stderr}")
    return result


def create_test_dockerfile(python_version: str, base_image: str = "python") -> str:
    """Create a Dockerfile for testing a specific Python version."""
    dockerfile_content = f"""
FROM {base_image}:{python_version}-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY dist/ ./dist/
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./

# Install the package from wheel
RUN pip install --no-cache-dir dist/*.whl

# Test basic functionality
RUN python -c "import arxiv_writer; print('Package imported successfully')"
RUN arxiv-writer --help

# Create test script
RUN echo '#!/usr/bin/env python3\\n\\
import sys\\n\\
try:\\n\\
    import arxiv_writer\\n\\
    print(f"Package version: {{getattr(arxiv_writer, \\"__version__\\", \\"unknown\\")}}")\\n\\
    \\n\\
    from arxiv_writer.core.generator import ArxivPaperGenerator\\n\\
    from arxiv_writer.config.loader import PaperConfig\\n\\
    from arxiv_writer.llm.caller import LLMCaller\\n\\
    print("Core classes imported successfully")\\n\\
    \\n\\
    from arxiv_writer.cli.main import main\\n\\
    print("CLI main function imported successfully")\\n\\
    \\n\\
    print("✓ All functionality tests passed")\\n\\
except Exception as e:\\n\\
    print(f"✗ Test failed: {{e}}")\\n\\
    sys.exit(1)\\n\\
' > /app/test_functionality.py && chmod +x /app/test_functionality.py

# Default command runs the test
CMD ["python", "/app/test_functionality.py"]
"""
    return dockerfile_content


def test_python_version(python_version: str, base_image: str = "python") -> Dict[str, Any]:
    """Test package installation for a specific Python version."""
    print(f"\n{'='*60}")
    print(f"Testing Python {python_version} ({base_image})")
    print(f"{'='*60}")
    
    result = {
        "python_version": python_version,
        "base_image": base_image,
        "success": False,
        "error": None,
        "logs": []
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        dockerfile_path = temp_path / "Dockerfile"
        
        # Create Dockerfile
        dockerfile_content = create_test_dockerfile(python_version, base_image)
        dockerfile_path.write_text(dockerfile_content)
        
        # Copy dist directory to temp directory
        dist_path = Path("dist")
        if not dist_path.exists():
            result["error"] = "dist/ directory not found - run 'python -m build' first"
            return result
        
        temp_dist = temp_path / "dist"
        temp_dist.mkdir()
        for file in dist_path.iterdir():
            if file.is_file():
                (temp_dist / file.name).write_bytes(file.read_bytes())
        
        # Copy required files
        for file_name in ["pyproject.toml", "README.md", "LICENSE"]:
            src_file = Path(file_name)
            if src_file.exists():
                (temp_path / file_name).write_text(src_file.read_text())
        
        try:
            # Build Docker image
            image_name = f"arxiv-writer-test-py{python_version.replace('.', '')}"
            build_cmd = ["docker", "build", "-t", image_name, "."]
            
            build_result = run_command(build_cmd, cwd=temp_path)
            result["logs"].append(f"Docker build: {build_result.returncode}")
            
            # Run Docker container
            run_cmd = ["docker", "run", "--rm", image_name]
            run_result = run_command(run_cmd)
            result["logs"].append(f"Docker run: {run_result.returncode}")
            
            if run_result.returncode == 0:
                result["success"] = True
                print(f"✓ Python {python_version} test passed")
            else:
                result["error"] = f"Container execution failed: {run_result.stderr}"
                print(f"✗ Python {python_version} test failed")
            
            # Clean up Docker image
            try:
                run_command(["docker", "rmi", image_name], check=False)
            except subprocess.CalledProcessError:
                pass  # Ignore cleanup errors
            
        except subprocess.CalledProcessError as e:
            result["error"] = f"Docker command failed: {e}"
            print(f"✗ Python {python_version} test failed: {e}")
        except Exception as e:
            result["error"] = f"Unexpected error: {e}"
            print(f"✗ Python {python_version} test failed: {e}")
    
    return result


def test_alpine_versions() -> List[Dict[str, Any]]:
    """Test package installation on Alpine Linux (smaller images)."""
    print(f"\n{'='*60}")
    print("Testing Alpine Linux versions")
    print(f"{'='*60}")
    
    alpine_versions = ["3.11", "3.12"]
    results = []
    
    for version in alpine_versions:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dockerfile_path = temp_path / "Dockerfile"
            
            # Create Alpine-specific Dockerfile
            dockerfile_content = f"""
FROM python:{version}-alpine

# Install system dependencies
RUN apk add --no-cache \\
    git \\
    build-base \\
    linux-headers

# Set working directory
WORKDIR /app

# Copy package files
COPY dist/ ./dist/
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./

# Install the package from wheel
RUN pip install --no-cache-dir dist/*.whl

# Test basic functionality
RUN python -c "import arxiv_writer; print('Package imported successfully')"
RUN arxiv-writer --help

# Test functionality
RUN python -c "
import sys
try:
    import arxiv_writer
    from arxiv_writer.core.generator import ArxivPaperGenerator
    from arxiv_writer.config.loader import PaperConfig
    from arxiv_writer.llm.caller import LLMCaller
    from arxiv_writer.cli.main import main
    print('✓ All Alpine tests passed')
except Exception as e:
    print(f'✗ Alpine test failed: {{e}}')
    sys.exit(1)
"

CMD ["echo", "Alpine test completed successfully"]
"""
            
            dockerfile_path.write_text(dockerfile_content)
            
            # Copy required files
            dist_path = Path("dist")
            temp_dist = temp_path / "dist"
            temp_dist.mkdir()
            for file in dist_path.iterdir():
                if file.is_file():
                    (temp_dist / file.name).write_bytes(file.read_bytes())
            
            for file_name in ["pyproject.toml", "README.md", "LICENSE"]:
                src_file = Path(file_name)
                if src_file.exists():
                    (temp_path / file_name).write_text(src_file.read_text())
            
            result = {
                "python_version": version,
                "base_image": "python-alpine",
                "success": False,
                "error": None,
                "logs": []
            }
            
            try:
                # Build and run
                image_name = f"arxiv-writer-alpine-py{version.replace('.', '')}"
                
                build_result = run_command(
                    ["docker", "build", "-t", image_name, "."], 
                    cwd=temp_path
                )
                
                run_result = run_command(["docker", "run", "--rm", image_name])
                
                if run_result.returncode == 0:
                    result["success"] = True
                    print(f"✓ Alpine Python {version} test passed")
                else:
                    result["error"] = f"Alpine test failed: {run_result.stderr}"
                    print(f"✗ Alpine Python {version} test failed")
                
                # Clean up
                try:
                    run_command(["docker", "rmi", image_name], check=False)
                except subprocess.CalledProcessError:
                    pass
                
            except Exception as e:
                result["error"] = f"Alpine test error: {e}"
                print(f"✗ Alpine Python {version} test failed: {e}")
            
            results.append(result)
    
    return results


def main():
    """Run isolated installation tests."""
    print("Arxiv-Writer Isolated Installation Test")
    print("=" * 60)
    
    # Check Docker availability
    try:
        run_command(["docker", "--version"])
        print("✓ Docker is available")
    except subprocess.CalledProcessError:
        print("✗ Docker is not available - cannot run isolated tests")
        return 1
    
    # Check if dist directory exists
    if not Path("dist").exists():
        print("✗ dist/ directory not found - run 'python -m build' first")
        return 1
    
    all_results = []
    
    # Test standard Python versions
    python_versions = ["3.8", "3.9", "3.10", "3.11", "3.12"]
    
    for version in python_versions:
        result = test_python_version(version)
        all_results.append(result)
    
    # Test Alpine versions
    alpine_results = test_alpine_versions()
    all_results.extend(alpine_results)
    
    # Generate summary report
    print("\n" + "=" * 60)
    print("ISOLATED INSTALLATION TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for result in all_results:
        status = "✓ PASS" if result["success"] else "✗ FAIL"
        version_info = f"{result['base_image']}:{result['python_version']}"
        print(f"{status:8} {version_info:20} {result.get('error', 'Success')}")
        
        if result["success"]:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    # Save detailed results
    with open("isolated-test-results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("Detailed results saved to: isolated-test-results.json")
    
    print("\n" + "=" * 60)
    if failed == 0:
        print("🎉 ALL ISOLATED TESTS PASSED!")
        print("Package works correctly across all tested environments.")
    else:
        print(f"❌ {failed} TESTS FAILED!")
        print("Please review the failures and fix compatibility issues.")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())