import argparse
import json
import logging
import sys
import traceback
import uuid
import time
from datetime import datetime
from pathlib import Path
import random as random_module
from threading import Event

import nltk
import pandas as pd

from src.ideas.BookClasses.Model2BookIdeas import Models2BookIdeas
from src.ideas.Tournament.Tournament import ShowTournamentResults, Tournament

from src.ideas.cli import create_parser


class ContinuousIdeaGenerator:
    def __init__(self, ideas_per_batch=5, batch_interval=300, model="deepseek-r1:latest", temperature=0.7,
                 run_duration=None, base_dir="output", custom_prompt=None, api_type="ollama"):
        self.idea_id = None
        self.run_id = None
        self.ideas_per_batch = ideas_per_batch
        self.batch_interval = batch_interval
        self.model = model
        self.temperature = temperature
        self.run_duration = run_duration
        self.custom_prompt = custom_prompt  # Store custom_prompt as an instance variable
        self.api_type = api_type

        # Setup basic attributes
        self.exit_event = Event()
        # Progress tracking
        self.generation_count = 0
        self.start_time = datetime.now()
        self.last_report_time = self.start_time
        self.successful_generations = 0
        self.failed_generations = 0

        # Constants
        self.MAX_FILE_SIZE = 60000
        self.MAX_ENTRIES_PER_FILE = 1000
        self.REPORT_INTERVAL = 10  # Report every 10 generations by default

        # Setup directories with custom base_dir
        self.base_dir = Path(base_dir)
        self.resources_dir = self.base_dir / "resources"
        self.setup_directories()

        # Setup logging
        self.setup_logging()

    def setup_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.base_dir, self.resources_dir]:
            directory.mkdir(exist_ok=True)

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('generator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_directories(self):
        """Create necessary directories if they don't exist"""
        for directory in [self.base_dir, self.resources_dir]:
            directory.mkdir(exist_ok=True)

    def generate_progress_report(self, initial_report=False):
        """Generate a detailed progress report"""
        current_time = datetime.now()
        running_time = current_time - self.start_time
        time_since_last_report = current_time - self.last_report_time

        # Calculate rates
        total_ideas = self.successful_generations * self.ideas_per_batch
        ideas_per_hour = (total_ideas / running_time.total_seconds()) * 3600 if running_time.total_seconds() > 0 else 0
        success_rate = (self.successful_generations / (
                    self.successful_generations + self.failed_generations)) * 100 if self.successful_generations + self.failed_generations > 0 else 0

        # Get current file sizes
        csv_size = self.get_file_size(self.resources_dir / "cumulative.csv")
        json_size = self.get_file_size(self.resources_dir / "cumulative.json")

        report = f"""
=== Progress Report ===
Generations Completed: {self.generation_count}
Time Running: {str(running_time).split('.')[0]}
Time Since Last Report: {str(time_since_last_report).split('.')[0]}
"""

        # Only include performance metrics if we have some data
        if not initial_report:
            report += f"""
Performance Metrics:
- Total Ideas Generated: {total_ideas:,}
- Ideas per Hour: {ideas_per_hour:.2f}
- Successful Generations: {self.successful_generations:,}
- Failed Generations: {self.failed_generations:,}
- Success Rate: {success_rate:.2f}%
"""

        report += f"""
Storage Status:
- Latest Cumulative CSV Size: {csv_size}
- Latest Cumulative JSON Size: {json_size}
====================
"""
        return report


    def get_file_size(self, file_path):
        """Get human-readable file size"""
        if not file_path.exists():
            return "0 B"
        size = file_path.stat().st_size
        for unit in ['B', 'KB', 'MB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} GB"

    def save_progress_report(self, report):
        """Save progress report to a log file"""
        report_file = self.resources_dir / "progress_reports.log"
        with open(report_file, 'a') as f:
            f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(report)

    def generate_single_batch(self, mode=None, count=None):
        """
        Generate a single batch of ideas without continuous operation
        Args:
            mode: Optional generation mode
            count: Number of ideas to generate (overrides ideas_per_batch if provided)
        Returns:
            Dictionary of generated ideas
        """
        # Store original value to restore later if needed
        original_batch_size = self.ideas_per_batch
        if count is not None:
            self.ideas_per_batch = count

        try:
            model_runner = Models2BookIdeas(model=self.model, temperature=self.temperature)
            self.run_id = str(uuid.uuid4())[:8]
            self.logger.warning(f"args: {args}")
            # Create run-specific directory
            batch_dir = self.base_dir / self.run_id
            self.logger.info(f"Creating batch directory: {batch_dir}")
            batch_dir.mkdir(exist_ok=True)

            seed_ideas = {}
            # Generate ideas one at a time
            for i in range(self.ideas_per_batch):
                self.idea_id = str(uuid.uuid4())[:8]
                self.logger.info(f"Custom prompt is {self.custom_prompt}")
                # Use stored custom_prompt if provided, otherwise pass None
                seed_idea = model_runner.create_idea(custom_prompt=self.custom_prompt)

                self.logger.info(f"Generated seed idea: {seed_idea}")

                if isinstance(seed_idea, dict) and 'title' in seed_idea and 'logline' in seed_idea:
                    seed_ideas[f"{self.idea_id}"] = {
                        'title': seed_idea['title'],
                        'logline': seed_idea['logline'],
                        'model': self.model,
                        'temperature': self.temperature
                    }

            # Save batch results
            csv_path = batch_dir / "generated_book_ideas.csv"
            json_path = batch_dir / "generated_book_ideas.json"

            self.logger.info(f"Saving batch {self.run_id} results to CSV: {csv_path}")
            model_runner.save_to_csv(seed_ideas, str(csv_path))

            # Update cumulative files
            self.update_cumulative_files(csv_path, json_path, self.run_id)



            # Run tournament if there are enough ideas
            if len(seed_ideas) > 1:
                self.send_batch_results_to_tournament(batch_dir, seed_ideas)

            return seed_ideas

        except Exception as e:
            self.logger.error(f"Error generating batch: {traceback.format_exc()}")
            return None
        finally:
            # Restore original batch size if it was changed
            if count is not None:
                self.ideas_per_batch = original_batch_size

    def generate_batch(self):
        """Generate a batch of ideas for continuous operation"""
        try:
            seed_ideas = self.generate_single_batch()
            if seed_ideas:
                self.generation_count += 1
                self.successful_generations += 1

                # Show completion message
                completion_message = f"Generation {self.generation_count} completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.logger.info(completion_message)
                self.save_progress_report(completion_message)
                batch_progress_report = self.generate_progress_report()
                self.logger.info("\n" + batch_progress_report)

                # Check if it's time to generate a progress report
                if self.generation_count % self.REPORT_INTERVAL == 0:
                    report = self.generate_progress_report()
                    self.logger.info("\n" + report)
                    self.save_progress_report(report)
                    self.last_report_time = datetime.now()

                return True
            else:
                self.failed_generations += 1
                return False

        except Exception as e:
            self.failed_generations += 1
            self.logger.error(f"Error generating batch: {traceback.format_exc()}")

            # Immediate report on failure
            failure_report = f"Generation failed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {str(e)}"
            self.logger.error(failure_report)
            self.save_progress_report(failure_report)

            return False

    def send_batch_results_to_tournament(self, batch_dir, seed_ideas):
        """Send batch results to a tournament"""
        try:
            # Calculate tournament size (nearest power of 2 that doesn't exceed number of ideas)
            num_ideas = len(seed_ideas)
            tournament_size = 2 ** ((num_ideas).bit_length() - 1)
            tournament_size = min(tournament_size, num_ideas)  # Ensure we don't exceed available ideas

            self.logger.info(f"Running tournament with {tournament_size} ideas out of {num_ideas}")

            # Randomly select ideas for the tournament
            selected_ideas = random_module.sample(list(seed_ideas.values()), tournament_size)

            # Run the tournament
            tournament = Tournament(selected_ideas, model=self.model)
            tournament.create_brackets()
            bracket_packet_path = batch_dir / "bracket_packet.md"
            tournament.create_bracket_packet(selected_ideas, bracket_packet_path)


            # Save tournament results
            results_display = ShowTournamentResults(tournament.rounds, tournament.total_ideas)
            results_display.generate_readable_results()

            csv_path = batch_dir / "tournament_results.csv"
            results_display.save_results_to_csv(csv_path)

            json_path = batch_dir / "tournament_matches.json"
            tournament.save_match_data_as_json(json_path)

            self.logger.info(f"Tournament results saved to {csv_path} and {json_path}")
        except Exception as e:
            self.logger.error(f"Error during tournament: {traceback.format_exc()}")

    def update_cumulative_files(self, csv_path, json_path, run_id):
        """Update both cumulative CSV and JSON files with results from this run"""
        cumulative_csv = self.resources_dir / "cumulative.csv"
        cumulative_json = self.resources_dir / "cumulative.json"
        try:
            # Read the new data
            self.logger.info(f"Reading new data from CSV: {csv_path}")  # Log step
            new_data = pd.read_csv(csv_path)

            # Add metadata
            #timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_data['run_id'] = run_id
         #   new_data['timestamp'] = timestamp

            # Update cumulative CSV
            if cumulative_csv.exists():
                self.logger.info(f"Appending to cumulative CSV: {cumulative_csv}")  # Log step
                new_data.to_csv(cumulative_csv, mode='a', header=False, index=False)
            else:
                self.logger.info(f"Creating cumulative CSV: {cumulative_csv}")  # Log step
                new_data.to_csv(cumulative_csv, index=False)

            # # Update cumulative JSON
            # self.logger.info(f"Loading new JSON data from: {json_path}")  # Log step
            # with open(json_path, 'r') as f:
            #     new_json_data = json.load(f)

            # run_data = {
            #     'run_id': run_id,
            #     'timestamp': timestamp,
            #     'ideas': new_json_data
            # }

            # if cumulative_json.exists():
            #     self.logger.info(f"Loading existing cumulative JSON: {cumulative_json}")  # Log step
            #     try:
            #         with open(cumulative_json, 'r') as f:
            #             cumulative_data = json.load(f)
            #     except json.JSONDecodeError:
            #         self.logger.warning("JSONDecodeError: Resetting cumulative JSON data")
            #         cumulative_data = {'runs': []}
            # else:
            #     self.logger.info(f"Creating new cumulative JSON: {cumulative_json}")  # Log step
            #     cumulative_data = {'runs': []}
            #
            # cumulative_data['runs'].append(run_data)
            #
            # self.logger.info(f"Writing updated cumulative JSON to: {cumulative_json}")  # Log step
            # with open(cumulative_json, 'w') as f:
            #     json.dump(cumulative_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error updating cumulative files: {str(e)}")

    def run(self):
        """Main loop for continuous generation"""
        self.logger.info("Starting continuous idea generation...")
        initial_report = self.generate_progress_report(initial_report=True)
        self.logger.info("\n" + initial_report)
        self.save_progress_report(initial_report)

        end_time = None
        if self.run_duration:
            end_time = time.time() + self.run_duration

        try:
            while not self.exit_event.is_set():
                if end_time and time.time() >= end_time:
                    self.logger.info("Run duration reached. Shutting down...")
                    break

                if self.generate_batch():
                    self.exit_event.wait(timeout=self.batch_interval)
                else:
                    # If generation failed, wait a bit longer before retrying
                    self.logger.info("Waiting before retry...")
                    self.exit_event.wait(timeout=self.batch_interval * 2)

        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal...")
        finally:
            # Generate final report
            final_report = self.generate_progress_report()
            self.logger.info("\nFinal Report:\n" + final_report)
            self.save_progress_report(final_report)
            self.logger.info("Generator shutting down...")

if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "continuous":
        # Initialize the ContinuousIdeaGenerator with the parsed args
        generator = ContinuousIdeaGenerator(
            model=args.model,
            temperature=args.temperature,
            ideas_per_batch=args.batch_size,
            batch_interval=args.interval / 60.0,  # Convert seconds to minutes
        )
        generator.run()

    elif args.command == "create":
        # Handle single batch generation
        # print args as of now
        logging.info(args)
        generator = ContinuousIdeaGenerator(
            model=args.model,
            temperature=args.temperature,
            ideas_per_batch=args.number_of_ideas,
            custom_prompt=args.custom_prompt,
            api_type=args.api_type,  # Add this line to pass the custom_prompt
        )

        # Just generate one batch
        generator.generate_batch()

    elif args.command == "expand":
        # Handle single batch generation
        generator = ContinuousIdeaGenerator(
            model=args.model,
            temperature=args.temperature,
            ideas_per_batch=args.number_of_ideas
        )

        # Just generate one batch
        generator.generate_batch()

    else:
        parser.print_help()
        sys.exit(1)
