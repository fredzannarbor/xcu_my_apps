import argparse
import shutil
from pathlib import Path

def create_imprint(imprint_name: str):
    """
    Creates a new imprint by copying the template from xynapse_traces.
    """
    base_path = Path('imprints')
    template_path = base_path / 'xynapse_traces'
    new_imprint_path = base_path / imprint_name

    if not template_path.is_dir():
        print(f"Error: Template directory not found at {template_path}")
        return

    if new_imprint_path.exists():
        print(f"Error: Imprint '{imprint_name}' already exists at {new_imprint_path}")
        return

    print(f"Creating new imprint '{imprint_name}' at {new_imprint_path}")
    shutil.copytree(template_path, new_imprint_path)
    print("Imprint created successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage imprints for the codexes factory.")
    parser.add_argument("name", type=str, help="The name of the new imprint to create.")
    args = parser.parse_args()

    create_imprint(args.name)
