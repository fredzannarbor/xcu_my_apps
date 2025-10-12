import argparse
import logging
import uuid
import os
import time
from src.ideas.Tournament.Tournament import Tournament, ShowTournamentResults
from src.ideas.BookClasses.BookIdea import BookIdea
from src.ideas.BookClasses.BookIdeaSet import BookIdeaSet
import random

logging.getLogger().handlers = []

# Setup basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def generate_run_id():
    return str(uuid.uuid4())[:8]


def main():
    parser = argparse.ArgumentParser(description="Run a tournament of ideas.")
    parser.add_argument("--idea_file_path", "-i", type=str,
                        default="/Users/fred/xcu_my_apps/nimble/Ideas/resources/64.csv",
                        help="Path to the CSV file containing ideas.")
    parser.add_argument("--output_file_path", "-o", type=str, default="output/tournament_results.csv",
                        help="Path to save the tournament results CSV.")
    parser.add_argument("--num_ideas", type=int, default=1024,
                        help="Number of ideas to randomly pick from the input file (for testing).")
    parser.add_argument("--model", "-m", type=str, default="deepseek-r1:latest", help="model name")


    args = parser.parse_args()

    run_id = generate_run_id()
    output_dir = os.path.join("output", run_id)  # Create a subdirectory for each run
    os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

    start_time = time.time()
    idea_set = BookIdeaSet()
    ideas = idea_set.load_from_format(args.idea_file_path, format_type='csv')
    #print(ideas)

    if args.num_ideas:
        ideas = random.sample(ideas, min(args.num_ideas, len(ideas)))  # Pick a random subset

    num_ideas = len(ideas)
    logger.info(f"Number of ideas loaded: {num_ideas}")

    unique_ideas = set(ideas)
    #logger.debug(f"Unique ideas: {unique_ideas}")

    tournament = Tournament(unique_ideas, model=args.model)
    tournament.create_brackets()
    logger.debug(f"Tournament rounds: {tournament.rounds}")

    output_file_path = os.path.join(output_dir, "tournament_results.csv")
    results_display = ShowTournamentResults(tournament.rounds, tournament.total_ideas)
    results_display.generate_readable_results()
    results_display.save_results_to_csv(output_file_path)  # Save to the run-specific directory
    output_file_path_match_data = os.path.join(output_dir, "all_matches_in_tournament.json")
    tournament.save_match_data_as_json(output_file_path_match_data)

    elapsed_time = time.time() - start_time
    seconds_per_idea = elapsed_time / num_ideas
    seconds_per_match = elapsed_time / tournament.total_matches
    logger.info(f"Ideas evaluated: {num_ideas}")
    logger.info(f"Tournament rounds completed: {len(tournament.rounds)}")
    logger.info(f"Matches played: {tournament.total_matches}")
    logger.info(f"Seconds per idea: {seconds_per_idea:.2f}")
    logger.info(f"Seconds per match: {seconds_per_match:.2f}")
    logger.info(f"Script completed in {elapsed_time:.2f} seconds")
    logger.info(f"Results saved to: {output_file_path}")
    logger.info(f"Model was {tournament.model}")

if __name__ == "__main__":
    main()
