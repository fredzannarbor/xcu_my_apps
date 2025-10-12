"""
Main CLI entry point for Trillions of People.
"""

import click
import os
from pathlib import Path
from typing import Optional

from ..core.logging_config import get_logger
from ..modules.people_utilities import PeopleManager

logger = get_logger(__name__)


@click.group()
@click.version_option(version="1.0.0")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def main(verbose: bool) -> None:
    """
    Trillions of People - Generate synthetic people data for historical, present, and future scenarios.

    A tool to explore the human story through AI-generated personas.
    """
    if verbose:
        os.environ["LOG_LEVEL"] = "DEBUG"
        logger.info("Verbose logging enabled")


@main.command()
@click.option("--country", "-c", default="Random", help="Country for persona generation")
@click.option("--year", "-y", type=int, default=2024, help="Target year (CE = positive, BCE = negative)")
@click.option("--count", "-n", type=int, default=1, help="Number of personas to generate")
@click.option("--output", "-o", type=click.Path(), help="Output CSV file (default: people_data/people.csv)")
@click.option("--api-key", envvar="OPENAI_API_KEY", help="OpenAI API key")
def generate(
    country: str,
    year: int,
    count: int,
    output: Optional[str],
    api_key: Optional[str]
) -> None:
    """Generate synthetic personas for specified parameters."""

    if not api_key:
        click.echo("Error: OpenAI API key required. Set OPENAI_API_KEY environment variable or use --api-key", err=True)
        return

    click.echo(f"Generating {count} persona(s) for {country} in year {year}")

    try:
        # Initialize people manager
        people_manager = PeopleManager()

        # Load countries to get country code
        countries = people_manager.load_countries()
        country_code = countries.get(country, country.upper()[:2])

        if country == "Random":
            import random
            country = random.choice(list(countries.keys()))
            country_code = countries[country]
            click.echo(f"Randomly selected country: {country}")

        # Generate personas
        people_df, card_df = people_manager.create_new_people(
            country=country,
            country_code=country_code,
            count=count,
            target_year=year,
            api_key=api_key
        )

        if people_df.empty:
            click.echo("Error: No personas were generated", err=True)
            return

        # Save to file
        if output:
            output_path = Path(output)
            people_df.to_csv(output_path, index=False)
            click.echo(f"Saved {len(people_df)} personas to {output_path}")
        else:
            people_manager.save_people(people_df, backup=True)
            click.echo(f"Saved {len(people_df)} personas to default location")

        # Display first persona
        if not card_df.empty:
            click.echo("\n--- Generated Persona ---")
            for _, row in card_df.iterrows():
                click.echo(f"{row['Attributes']}: {row['Values']}")

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        click.echo(f"Error: {e}", err=True)


@main.command()
@click.option("--limit", "-l", type=int, help="Limit number of records shown")
@click.option("--format", "output_format", type=click.Choice(["table", "json", "csv"]), default="table", help="Output format")
def browse(limit: Optional[int], output_format: str) -> None:
    """Browse existing personas in the database."""

    try:
        people_manager = PeopleManager()
        people_df = people_manager.browse_people(limit=limit)

        if people_df.empty:
            click.echo("No personas found in database")
            return

        if output_format == "json":
            click.echo(people_df.to_json(orient="records", indent=2))
        elif output_format == "csv":
            click.echo(people_df.to_csv(index=False))
        else:
            # Table format (default)
            click.echo(f"\nFound {len(people_df)} personas:")
            # Show key columns only for readability
            display_cols = ["name", "age", "gender", "born", "country", "occupation"]
            available_cols = [col for col in display_cols if col in people_df.columns]
            if available_cols:
                click.echo(people_df[available_cols].to_string(index=False))
            else:
                click.echo(people_df.to_string(index=False))

    except Exception as e:
        logger.error(f"Browse failed: {e}")
        click.echo(f"Error: {e}", err=True)


@main.command()
def countries() -> None:
    """List available countries for persona generation."""

    try:
        people_manager = PeopleManager()
        countries = people_manager.load_countries()

        click.echo("Available countries:")
        for country, code in countries.items():
            click.echo(f"  {country} ({code})")

    except Exception as e:
        logger.error(f"Countries listing failed: {e}")
        click.echo(f"Error: {e}", err=True)


@main.command()
@click.option("--check-api", is_flag=True, help="Check API key validity")
def status() -> None:
    """Show system status and configuration."""

    click.echo("Trillions of People - System Status")
    click.echo("=" * 35)

    # Check data directory
    people_manager = PeopleManager()
    if people_manager.data_dir.exists():
        click.echo(f"✓ Data directory: {people_manager.data_dir}")

        # Check people file
        people_df = people_manager.browse_people()
        click.echo(f"✓ Personas in database: {len(people_df)}")

        # Check countries file
        countries = people_manager.load_countries()
        click.echo(f"✓ Available countries: {len(countries)}")
    else:
        click.echo(f"✗ Data directory not found: {people_manager.data_dir}")

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        click.echo(f"✓ OpenAI API key configured (length: {len(api_key)})")
    else:
        click.echo("✗ OpenAI API key not set")


if __name__ == "__main__":
    main()