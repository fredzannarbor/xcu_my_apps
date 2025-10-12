"""
Continuous idea generation system with codexes-factory integration.
Enhanced version of the original ContinuousIdeaGenerator.
"""

import json
import logging
import sys
import traceback
import uuid
import time
from datetime import datetime
from pathlib import Path
import random
from threading import Event
from typing import Dict, List, Optional, Any

import pandas as pd

from .book_idea import BookIdea, IdeaSet
from .legacy_tournament import Tournament, TournamentManager
from ...core.llm_integration import LLMCaller

logger = logging.getLogger(__name__)


class Models2BookIdeas:
    """Interface for LLM-based book idea generation using codexes-factory infrastructure."""
    
    def __init__(self, llm_caller: LLMCaller, model: str = "ollama/mistral", temperature: float = 0.7):
        self.llm_caller = llm_caller
        self.model = model
        self.temperature = temperature
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_idea(self, custom_prompt: Optional[str] = None) -> Dict[str, str]:
        """Create a single book idea using LLM."""
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = """
            You are an AI book publisher and editor with exhaustive knowledge of all genres of publishing.
            Create a compelling book idea that would be commercially viable in today's market.
            
            Respond with a JSON object containing:
            {
                "title": "An engaging book title",
                "logline": "A one-sentence description of the book's core concept"
            }
            
            Make the idea original, marketable, and appealing to modern readers.
            """

        try:
            response = self.llm_caller.call_llm(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                format='json'
            )
            print(response)
            if response and len(response) > 0:
                content = response.strip()
                
                # Try to parse as JSON first
                try:
                    idea_data = json.loads(content)

                    # Check if response has "ideas" array (common LLM response format)
                    if isinstance(idea_data, dict) and 'ideas' in idea_data:
                        ideas_list = idea_data['ideas']
                        if isinstance(ideas_list, list) and len(ideas_list) > 0:
                            # Return the first idea from the array
                            first_idea = ideas_list[0]
                            if isinstance(first_idea, dict) and 'title' in first_idea:
                                return first_idea

                    # Check for direct title/logline format
                    if isinstance(idea_data, dict) and 'title' in idea_data and 'logline' in idea_data:
                        return idea_data
                except json.JSONDecodeError:
                    pass
                
                # Fallback: parse text format
                return self._parse_text_response(content)
                
        except Exception as e:
            self.logger.error(f"Error creating idea with LLM: {e}")
            
        # Ultimate fallback
        return {
            'title': f"Generated Idea {uuid.uuid4().hex[:8]}",
            'logline': "A compelling story waiting to be told."
        }

    def _parse_text_response(self, content: str) -> Dict[str, str]:
        """Parse text response into title/logline format."""
        lines = content.strip().split('\n')
        title = ""
        logline = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('Title:') or line.startswith('"title":'):
                title = line.split(':', 1)[1].strip().strip('"')
            elif line.startswith('Logline:') or line.startswith('"logline":'):
                logline = line.split(':', 1)[1].strip().strip('"')
            elif not title and line:  # First non-empty line as title
                title = line
            elif title and not logline and line:  # Second line as logline
                logline = line
                break
        
        return {
            'title': title or f"Generated Idea {uuid.uuid4().hex[:8]}",
            'logline': logline or "A compelling story waiting to be told."
        }

    def save_to_csv(self, ideas: Dict[str, Dict[str, Any]], file_path: str):
        """Save ideas to CSV format."""
        if not ideas:
            self.logger.warning("No ideas to save to CSV")
            return
            
        data = []
        for idea_id, idea_data in ideas.items():
            row = {
                'idea_id': idea_id,
                'title': idea_data.get('title', ''),
                'logline': idea_data.get('logline', ''),
                'model': idea_data.get('model', self.model),
                'temperature': idea_data.get('temperature', self.temperature),
                'created_at': datetime.now().isoformat()
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(file_path, index=False)


class ContinuousIdeaGenerator:
    """Enhanced continuous idea generation system with codexes-factory integration."""
    
    def __init__(self, llm_caller: LLMCaller, ideas_per_batch: int = 5, 
                 batch_interval: int = 300, model: str = "mistral", 
                 temperature: float = 0.7, run_duration: Optional[int] = None,
                 base_dir: str = "output", custom_prompt: Optional[str] = None):
        
        self.llm_caller = llm_caller
        self.ideas_per_batch = ideas_per_batch
        self.batch_interval = batch_interval
        self.model = model
        self.temperature = temperature
        self.run_duration = run_duration
        self.custom_prompt = custom_prompt
        self.base_dir = Path(base_dir)
        
        # Initialize components
        self.model_runner = Models2BookIdeas(llm_caller, model, temperature)
        self.tournament_manager = TournamentManager(llm_caller)
        
        # Setup attributes
        self.run_id = None
        self.idea_id = None
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
        self.REPORT_INTERVAL = 10
        
        # Setup directories and logging
        self.setup_directories()
        self.setup_logging()

    def setup_directories(self):
        """Create necessary directories."""
        self.resources_dir = self.base_dir / "resources"
        for directory in [self.base_dir, self.resources_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """Setup logging configuration."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_single_batch(self, count: Optional[int] = None, progress_callback=None) -> Optional[Dict[str, BookIdea]]:
        """Generate a single batch of ideas.

        Args:
            count: Number of ideas to generate (defaults to ideas_per_batch)
            progress_callback: Optional callback function(current, total) for progress updates
        """
        batch_size = count if count is not None else self.ideas_per_batch
        self.run_id = str(uuid.uuid4())[:8]

        try:
            # Create run-specific directory
            batch_dir = self.base_dir / self.run_id
            batch_dir.mkdir(exist_ok=True)

            seed_ideas = {}
            book_ideas = []

            # Generate ideas
            for i in range(batch_size):
                self.idea_id = str(uuid.uuid4())[:8]

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(i + 1, batch_size)

                try:
                    seed_idea = self.model_runner.create_idea(custom_prompt=self.custom_prompt)
                    
                    if isinstance(seed_idea, dict) and 'title' in seed_idea and 'logline' in seed_idea:
                        # Create BookIdea object
                        book_idea = BookIdea(
                            title=seed_idea['title'],
                            logline=seed_idea['logline'],
                            generation_metadata={
                                'model': self.model,
                                'temperature': self.temperature,
                                'idea_id': self.idea_id,
                                'run_id': self.run_id,
                                'generated_at': datetime.now().isoformat()
                            }
                        )
                        
                        book_ideas.append(book_idea)
                        seed_ideas[self.idea_id] = {
                            'title': seed_idea['title'],
                            'logline': seed_idea['logline'],
                            'model': self.model,
                            'temperature': self.temperature
                        }
                        
                        self.logger.info(f"Generated idea {i+1}/{batch_size}: {seed_idea['title']}")
                        
                except Exception as e:
                    self.logger.error(f"Error generating idea {i+1}: {e}")
                    continue
            
            if not seed_ideas:
                self.logger.error("No ideas were successfully generated")
                return None
            
            # Save batch results
            csv_path = batch_dir / "generated_book_ideas.csv"
            json_path = batch_dir / "generated_book_ideas.json"
            
            self.model_runner.save_to_csv(seed_ideas, str(csv_path))
            
            # Save as IdeaSet
            idea_set = IdeaSet(book_ideas)
            idea_set.metadata = {
                'run_id': self.run_id,
                'batch_size': batch_size,
                'model': self.model,
                'temperature': self.temperature
            }
            idea_set.save_to_json(str(json_path))
            
            # Update cumulative files
            self.update_cumulative_files(csv_path, json_path, self.run_id)
            
            # Run tournament if enough ideas
            if len(book_ideas) > 1:
                self.send_batch_results_to_tournament(batch_dir, book_ideas)
            
            # Convert to dict format for compatibility
            result = {}
            for idea in book_ideas:
                result[idea.generation_metadata.get('idea_id', str(uuid.uuid4())[:8])] = idea
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating batch: {traceback.format_exc()}")
            return None

    def send_batch_results_to_tournament(self, batch_dir: Path, book_ideas: List[BookIdea]):
        """Send batch results to tournament evaluation."""
        try:
            num_ideas = len(book_ideas)
            
            # Calculate tournament size (power of 2)
            tournament_size = 2 ** ((num_ideas).bit_length() - 1)
            tournament_size = min(tournament_size, num_ideas)
            
            self.logger.info(f"Running tournament with {tournament_size} ideas out of {num_ideas}")
            
            # Randomly select ideas for tournament
            selected_ideas = random.sample(book_ideas, tournament_size)
            
            # Create and run tournament
            tournament = self.tournament_manager.create_tournament(selected_ideas)
            results = self.tournament_manager.run_tournament(tournament)
            
            # Save tournament results
            tournament.save_summary_as_json(str(batch_dir / "tournament_summary.json"))
            tournament.save_match_data_as_json(str(batch_dir / "tournament_matches.json"))
            
            # Save results display
            results_display = ShowTournamentResults(tournament.rounds, tournament.total_ideas)
            results_display.save_results_to_csv(str(batch_dir / "tournament_results.csv"))
            
            self.logger.info(f"Tournament completed. Winner: {results['winner'].title if results['winner'] else 'None'}")
            
        except Exception as e:
            self.logger.error(f"Error during tournament: {traceback.format_exc()}")

    def update_cumulative_files(self, csv_path: Path, json_path: Path, run_id: str):
        """Update cumulative files with new batch results."""
        cumulative_csv = self.resources_dir / "cumulative.csv"
        
        try:
            # Read new data
            new_data = pd.read_csv(csv_path)
            new_data['run_id'] = run_id
            new_data['timestamp'] = datetime.now().isoformat()
            
            # Update cumulative CSV
            if cumulative_csv.exists():
                new_data.to_csv(cumulative_csv, mode='a', header=False, index=False)
            else:
                new_data.to_csv(cumulative_csv, index=False)
                
            self.logger.info(f"Updated cumulative files with {len(new_data)} ideas")
            
        except Exception as e:
            self.logger.error(f"Error updating cumulative files: {e}")

    def generate_progress_report(self, initial_report: bool = False) -> str:
        """Generate detailed progress report."""
        current_time = datetime.now()
        running_time = current_time - self.start_time
        
        total_ideas = self.successful_generations * self.ideas_per_batch
        ideas_per_hour = (total_ideas / running_time.total_seconds()) * 3600 if running_time.total_seconds() > 0 else 0
        success_rate = (self.successful_generations / (self.successful_generations + self.failed_generations)) * 100 if (self.successful_generations + self.failed_generations) > 0 else 0
        
        csv_size = self.get_file_size(self.resources_dir / "cumulative.csv")
        
        report = f"""
=== Progress Report ===
Generations Completed: {self.generation_count}
Time Running: {str(running_time).split('.')[0]}
"""
        
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
- Cumulative CSV Size: {csv_size}
====================
"""
        return report

    def get_file_size(self, file_path: Path) -> str:
        """Get human-readable file size."""
        if not file_path.exists():
            return "0 B"
        
        size = file_path.stat().st_size
        for unit in ['B', 'KB', 'MB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} GB"

    def save_progress_report(self, report: str):
        """Save progress report to log file."""
        report_file = self.resources_dir / "progress_reports.log"
        with open(report_file, 'a') as f:
            f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(report)

    def generate_batch(self) -> bool:
        """Generate a batch for continuous operation."""
        try:
            seed_ideas = self.generate_single_batch()
            if seed_ideas:
                self.generation_count += 1
                self.successful_generations += 1
                
                completion_message = f"Generation {self.generation_count} completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                self.logger.info(completion_message)
                
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
            return False

    def run(self):
        """Main loop for continuous generation."""
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
                    self.logger.info("Generation failed, waiting before retry...")
                    self.exit_event.wait(timeout=self.batch_interval * 2)
                    
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal...")
        finally:
            final_report = self.generate_progress_report()
            self.logger.info("\nFinal Report:\n" + final_report)
            self.save_progress_report(final_report)
            self.logger.info("Generator shutting down...")

    def stop(self):
        """Stop continuous generation."""
        self.exit_event.set()


class IntegratedIdeaGenerator:
    """Enhanced idea generator with imprint-specific customization."""
    
    def __init__(self, llm_caller: LLMCaller, imprint_config: Optional[Dict[str, Any]] = None):
        self.llm_caller = llm_caller
        self.imprint_config = imprint_config or {}
        self.tournament_manager = TournamentManager(llm_caller)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Active generators by imprint
        self.active_generators: Dict[str, ContinuousIdeaGenerator] = {}

    def create_imprint_generator(self, imprint_name: str, 
                               generator_config: Optional[Dict[str, Any]] = None) -> ContinuousIdeaGenerator:
        """Create a generator customized for a specific imprint."""
        config = generator_config or {}
        
        # Get imprint-specific settings
        imprint_settings = self.imprint_config.get(imprint_name, {})
        
        # Create custom prompt based on imprint focus
        custom_prompt = self._create_imprint_prompt(imprint_name, imprint_settings)
        
        generator = ContinuousIdeaGenerator(
            llm_caller=self.llm_caller,
            ideas_per_batch=config.get('ideas_per_batch', 5),
            batch_interval=config.get('batch_interval', 300),
            model=config.get('model', 'mistral'),
            temperature=config.get('temperature', 0.7),
            base_dir=f"output/{imprint_name}_ideas",
            custom_prompt=custom_prompt
        )
        
        self.active_generators[imprint_name] = generator
        return generator

    def _create_imprint_prompt(self, imprint_name: str, imprint_settings: Dict[str, Any]) -> str:
        """Create a custom prompt based on imprint characteristics."""
        base_prompt = """
        You are an AI book publisher and editor specializing in creating ideas for the {imprint_name} imprint.
        
        {imprint_description}
        
        Create a compelling book idea that aligns with this imprint's focus and would be commercially viable.
        
        Respond with a JSON object containing:
        {{
            "title": "An engaging book title that fits the imprint's style",
            "logline": "A one-sentence description of the book's core concept"
        }}
        
        Ensure the idea is original, marketable, and perfectly suited for the {imprint_name} audience.
        """
        
        # Customize based on imprint settings
        focus_areas = imprint_settings.get('publishing_focus', {}).get('primary_genres', [])
        target_audience = imprint_settings.get('publishing_focus', {}).get('target_audience', 'General')
        specialization = imprint_settings.get('publishing_focus', {}).get('specialization', '')
        
        description_parts = []
        if focus_areas:
            description_parts.append(f"Primary genres: {', '.join(focus_areas)}")
        if target_audience:
            description_parts.append(f"Target audience: {target_audience}")
        if specialization:
            description_parts.append(f"Specialization: {specialization}")
        
        imprint_description = "This imprint focuses on: " + "; ".join(description_parts) if description_parts else "This is a general interest imprint."
        
        return base_prompt.format(
            imprint_name=imprint_name,
            imprint_description=imprint_description
        )

    def start_continuous_generation(self, imprint_name: str, 
                                  schedule_config: Optional[Dict[str, Any]] = None):
        """Start continuous generation for an imprint."""
        if imprint_name not in self.active_generators:
            self.create_imprint_generator(imprint_name, schedule_config)
        
        generator = self.active_generators[imprint_name]
        
        # Start in a separate thread for non-blocking operation
        import threading
        thread = threading.Thread(target=generator.run, daemon=True)
        thread.start()
        
        self.logger.info(f"Started continuous generation for {imprint_name}")

    def stop_continuous_generation(self, imprint_name: str):
        """Stop continuous generation for an imprint."""
        if imprint_name in self.active_generators:
            self.active_generators[imprint_name].stop()
            self.logger.info(f"Stopped continuous generation for {imprint_name}")

    def get_generator_status(self, imprint_name: str) -> Dict[str, Any]:
        """Get status of a generator."""
        if imprint_name not in self.active_generators:
            return {'status': 'not_running'}
        
        generator = self.active_generators[imprint_name]
        return {
            'status': 'running' if not generator.exit_event.is_set() else 'stopped',
            'generation_count': generator.generation_count,
            'successful_generations': generator.successful_generations,
            'failed_generations': generator.failed_generations,
            'start_time': generator.start_time.isoformat(),
            'ideas_per_batch': generator.ideas_per_batch,
            'batch_interval': generator.batch_interval
        }