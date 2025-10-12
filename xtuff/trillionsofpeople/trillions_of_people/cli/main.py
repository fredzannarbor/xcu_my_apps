"""Command-line interface for TrillionsOfPeople package."""

import click
import sys
import os
from pathlib import Path
from typing import Optional

from ..core.config import ConfigManager
from ..core.generator import PeopleGenerator
from ..core.exceptions import TrillionsOfPeopleError
from ..utils.formatters import (
    format_person_csv, 
    format_person_json, 
    format_person_parquet,
    load_people_from_csv,
    load_people_from_json
)


@click.group()
@click.version_option(version="0.1.0")
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """TrillionsOfPeople - Generate synthetic people data."""
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = config
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--count', '-n', default=1, type=click.IntRange(1, 1000), 
              help='Number of people to generate (1-1000)')
@click.option('--year', '-y', default=2100, type=click.IntRange(-233000, 100000),
              help='Birth year for generated people (-233000 to 100000)')
@click.option('--country', '-c', default='Random', 
              help='Country for generated people (use "Random" for random selection)')
@click.option('--output', '-o', type=click.Path(), 
              help='Output file path (prints to stdout if not specified)')
@click.option('--format', '-f', type=click.Choice(['csv', 'json', 'parquet']), default='csv', 
              help='Output format')
@click.option('--species', type=click.Choice(['sapiens', 'neanderthalensis', 'denisovan', 'floresiensis']),
              help='Species for generated people (random if not specified)')
@click.option('--timeline', type=click.Choice(['ours', 'RCP 8.5', 'Earth-616', 'Earth-1218', 'ODNI2040']),
              help='Timeline for generated people (defaults to "ours")')
@click.pass_context
def generate(ctx, count: int, year: int, country: str, output: Optional[str], format: str, 
             species: Optional[str], timeline: Optional[str]):
    """Generate synthetic people data.
    
    Examples:
    
        # Generate 5 people for the year 2100
        trillions generate -n 5 -y 2100
        
        # Generate people for ancient Rome
        trillions generate -n 3 -y -50 -c Italy
        
        # Generate Neanderthals and save to file
        trillions generate -n 10 --species neanderthalensis -o neanderthals.csv
        
        # Generate people in JSON format
        trillions generate -n 2 -f json -o people.json
    """
    try:
        # Validate count
        if count < 1 or count > 1000:
            click.echo("Error: Count must be between 1 and 1000", err=True)
            sys.exit(1)
        
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config(ctx.obj.get('config_file'))
        
        # Initialize generator
        generator = PeopleGenerator(config)
        
        # Prepare generation parameters
        kwargs = {}
        if species:
            kwargs['species'] = species
        if timeline:
            kwargs['timeline'] = timeline
        
        # Generate people
        if ctx.obj.get('verbose'):
            click.echo(f"Generating {count} people for year {year} in {country}...")
            if species:
                click.echo(f"Species: {species}")
            if timeline:
                click.echo(f"Timeline: {timeline}")
        
        people = generator.generate_people(count, year, country, **kwargs)
        
        # Handle output
        if output:
            output_path = Path(output)
            
            if format == 'parquet':
                format_person_parquet(people, str(output_path))
                click.echo(f"Results written to {output_path}")
            else:
                # Format output text
                if format == 'json':
                    output_text = format_person_json(people)
                else:
                    output_text = format_person_csv(people)
                
                output_path.write_text(output_text, encoding='utf-8')
                click.echo(f"Results written to {output_path}")
        else:
            # Print to stdout
            if format == 'parquet':
                click.echo("Error: Parquet format requires an output file path", err=True)
                sys.exit(1)
            elif format == 'json':
                output_text = format_person_json(people)
            else:
                output_text = format_person_csv(people)
            
            click.echo(output_text)
            
    except TrillionsOfPeopleError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        if ctx.obj.get('verbose'):
            raise
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--format', '-f', type=click.Choice(['csv', 'json', 'parquet']), required=True,
              help='Export format')
@click.option('--output', '-o', type=click.Path(), required=True, 
              help='Output file path')
@click.argument('input_file', type=click.Path(exists=True))
@click.pass_context
def export(ctx, format: str, output: str, input_file: str):
    """Export data to different formats.
    
    Convert people data between CSV, JSON, and Parquet formats.
    
    Examples:
    
        # Convert CSV to JSON
        trillions export people.csv -f json -o people.json
        
        # Convert JSON to Parquet
        trillions export people.json -f parquet -o people.parquet
        
        # Convert CSV to Parquet
        trillions export people.csv -f parquet -o people.parquet
    """
    try:
        input_path = Path(input_file)
        output_path = Path(output)
        
        if ctx.obj.get('verbose'):
            click.echo(f"Exporting {input_path} to {output_path} in {format} format...")
        
        # Determine input format from file extension
        input_ext = input_path.suffix.lower()
        
        # Load data based on input format
        if input_ext == '.csv':
            people = load_people_from_csv(str(input_path))
        elif input_ext == '.json':
            people = load_people_from_json(str(input_path))
        else:
            click.echo(f"Error: Unsupported input format '{input_ext}'. Supported: .csv, .json", err=True)
            sys.exit(1)
        
        if not people:
            click.echo("Warning: No people data found in input file")
        
        # Export to target format
        if format == 'csv':
            output_text = format_person_csv(people)
            output_path.write_text(output_text, encoding='utf-8')
        elif format == 'json':
            output_text = format_person_json(people)
            output_path.write_text(output_text, encoding='utf-8')
        elif format == 'parquet':
            format_person_parquet(people, str(output_path))
        
        click.echo(f"Successfully exported {len(people)} people to {output_path}")
        
    except FileNotFoundError:
        click.echo(f"Error: Input file '{input_file}' not found", err=True)
        sys.exit(1)
    except PermissionError:
        click.echo(f"Error: Permission denied writing to '{output}'", err=True)
        sys.exit(1)
    except Exception as e:
        if ctx.obj.get('verbose'):
            raise
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
@click.pass_context
def config(ctx):
    """Manage configuration settings."""
    pass


@config.command('show')
@click.pass_context
def config_show(ctx):
    """Show current configuration settings."""
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config(ctx.obj.get('config_file'))
        
        click.echo("Current configuration:")
        click.echo(f"  Default country: {config.default_country}")
        click.echo(f"  Default year: {config.default_year}")
        click.echo(f"  Max people per request: {config.max_people_per_request}")
        click.echo(f"  Enable image generation: {config.enable_image_generation}")
        click.echo(f"  Data directory: {config.data_directory}")
        click.echo(f"  Log level: {config.log_level}")
        click.echo(f"  OpenAI API key: {'Set' if config.openai_api_key else 'Not set'}")
        
        # Show configuration sources
        click.echo("\nConfiguration sources (in order of precedence):")
        click.echo("  1. Command-line arguments")
        click.echo("  2. Environment variables (TRILLIONS_*)")
        click.echo("  3. Configuration file")
        click.echo("  4. Default values")
        
    except TrillionsOfPeopleError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@config.command('validate')
@click.pass_context
def config_validate(ctx):
    """Validate current configuration."""
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config(ctx.obj.get('config_file'))
        
        # Validate configuration
        config_manager.validate_config(config)
        
        click.echo("✓ Configuration is valid")
        
        # Check API key availability
        if not config.openai_api_key:
            click.echo("⚠ Warning: OpenAI API key is not set. Some features may not work.")
            click.echo("  Set TRILLIONS_OPENAI_API_KEY environment variable or add to config file.")
        else:
            click.echo("✓ OpenAI API key is configured")
        
    except TrillionsOfPeopleError as e:
        click.echo(f"✗ Configuration error: {e}", err=True)
        sys.exit(1)


@config.command('init')
@click.option('--file', '-f', type=click.Path(), default='config.toml',
              help='Configuration file to create')
@click.pass_context
def config_init(ctx):
    """Create a sample configuration file."""
    try:
        config_file = ctx.params['file']
        config_path = Path(config_file)
        
        if config_path.exists():
            if not click.confirm(f"Configuration file '{config_file}' already exists. Overwrite?"):
                click.echo("Configuration file creation cancelled.")
                return
        
        # Create sample configuration
        sample_config = """# TrillionsOfPeople Configuration File
# All settings can be overridden with environment variables using TRILLIONS_ prefix

[general]
default_country = "Random"
default_year = 2100
max_people_per_request = 5
enable_image_generation = true
data_directory = "data"
log_level = "INFO"

[api]
# Set your OpenAI API key here or use TRILLIONS_OPENAI_API_KEY environment variable
# openai_api_key = "your-api-key-here"

[generation]
# Default species for people generation
default_species = "sapiens"
# Default timeline for people generation  
default_timeline = "ours"
"""
        
        config_path.write_text(sample_config, encoding='utf-8')
        click.echo(f"✓ Sample configuration file created: {config_file}")
        click.echo("Edit the file to customize your settings.")
        
    except Exception as e:
        if ctx.obj.get('verbose'):
            raise
        click.echo(f"Error creating configuration file: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.pass_context
def validate(ctx, input_file: str):
    """Validate people data file format and content.
    
    Check if a CSV or JSON file contains valid people data.
    
    Examples:
    
        # Validate a CSV file
        trillions validate people.csv
        
        # Validate a JSON file  
        trillions validate people.json
    """
    try:
        input_path = Path(input_file)
        input_ext = input_path.suffix.lower()
        
        if ctx.obj.get('verbose'):
            click.echo(f"Validating {input_path}...")
        
        # Load and validate data
        if input_ext == '.csv':
            people = load_people_from_csv(str(input_path))
        elif input_ext == '.json':
            people = load_people_from_json(str(input_path))
        else:
            click.echo(f"Error: Unsupported file format '{input_ext}'. Supported: .csv, .json", err=True)
            sys.exit(1)
        
        click.echo(f"✓ File format is valid")
        click.echo(f"✓ Found {len(people)} people records")
        
        # Basic validation statistics
        if people:
            years = [p.birth_year for p in people]
            countries = set(p.country for p in people if p.country)
            species = set(p.species.value if hasattr(p.species, 'value') else p.species for p in people)
            
            click.echo(f"  Year range: {min(years)} to {max(years)}")
            click.echo(f"  Countries: {len(countries)} unique")
            click.echo(f"  Species: {', '.join(sorted(species))}")
        
    except Exception as e:
        if ctx.obj.get('verbose'):
            raise
        click.echo(f"✗ Validation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table',
              help='Output format for listing')
@click.pass_context
def countries(ctx, format: str):
    """List available countries for people generation.
    
    Examples:
    
        # List countries in table format
        trillions countries
        
        # List countries in JSON format
        trillions countries -f json
    """
    try:
        from ..utils.data_loader import DataLoader
        
        data_loader = DataLoader()
        countries_data = data_loader.load_countries()
        
        if format == 'json':
            import json
            click.echo(json.dumps(countries_data, indent=2))
        else:
            click.echo("Available countries:")
            click.echo("=" * 50)
            for country in sorted(countries_data.keys()):
                click.echo(f"  {country}")
            click.echo(f"\nTotal: {len(countries_data)} countries")
            click.echo("\nUse 'Random' to select a random country.")
        
    except Exception as e:
        if ctx.obj.get('verbose'):
            raise
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()