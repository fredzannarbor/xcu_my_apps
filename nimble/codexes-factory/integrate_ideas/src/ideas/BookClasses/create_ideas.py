
"""
This script is designed to generate and manage book ideas. It provides functionalities to:

1.  Generate unique run identifiers for tracking.
2.  Create new book ideas from scratch or expand upon existing ones.
3.  Utilize different language models for idea generation.
4.  Organize and store book ideas in a structured format.
5.  Conduct a tournament-style evaluation of the generated ideas.
6.  Save the results of the idea generation and evaluation to CSV files.

The script supports different modes of operation, including creating new ideas,
expanding existing ideas, and generating a specific number of ideas. It also allows
for customization of prompts used for idea generation and the number of ideas
generated in each batch.
"""

import argparse
import uuid
import os
import time

from src.ideas.BookClasses.BookIdea import BookIdea

from src.ideas.Tournament.Tournament import Tournament
from src.ideas.BookClasses.Model2BookIdeas import Models2BookIdeas
from src.ideas.BookClasses.BookIdeaSet import BookIdeaSet, logger


def generate_run_id():
    """
    Generates a unique run identifier.


    This function creates a unique identifier string by generating a UUID
    and taking only the first 8 characters of the UUID. It can be used for
    tracking or tagging specific runs or sessions in an application.

    :return: A unique 8-character string used as a run identifier.
    :rtype: str
    """
    return str(uuid.uuid4())[:8]

def main():
    """
    Parses command-line arguments, generates book ideas using a given model and prompt, evaluates them in a tournament,
    and saves the results as a CSV file. This script supports creating or expanding book ideas in various modes, as
    specified in the input arguments.

    :raises SystemExit: If command-line arguments are invalid or missing.

    :argument output_file_path: str
        Path to save the tournament results CSV file. Default is "output/tournament_results.csv".

    :argument num_ideas: int
        Number of ideas to randomly pick from the input file or generate for testing. Default is 4.

    :argument model: str
        Name of the model to be used for generating book ideas. Default is "deepseek-r1:latest".

    :argument batch_size: int
        Number of ideas to generate in each batch. Default is 1.

    :argument prompt_template: str
        Template for the prompt to be used during idea generation. Default is an empty string.

    :argument mode: str
        Mode to run:
        - create: Uses the default prompt or creating new ideas.
        - create32: Variant of 'create' with a specific configuration.
        - expand: Uses the default prompt for expanding existing ideas.

        Choices are limited to 'create', 'create32', or 'expand'.

    :return: None
    """
    parser = argparse.ArgumentParser(description="Create book ideas ab novo, or expand existing ones.")
    parser.add_argument("--output_file_path", "-o", type=str, default="output/tournament_results.csv",
                        help="Path to save the tournament results CSV.")
    parser.add_argument("--num_ideas", "-n",type=int, default=4,
                        help="Number of ideas to randomly pick from the input file (for testing).")
    parser.add_argument("--model", "-m", type=str, default="deepseek-r1:latest", help="model name")
    parser.add_argument("--batch_size", "-b", type=int, default=1,
                        help="Number of ideas to generate in each batch.")

    parser.add_argument("--prompt_template", "-p", type=str, default="")

    parser.add_argument("--mode", "-s",
                        choices=['create', 'create32','expand'],
                        help="Mode to run: 'create' uses default prompt for creating new ideas, 'expand' uses default prompt for expanding existing ideas.")

    args = parser.parse_args()

    run_id = generate_run_id()
    output_dir = os.path.join("output", run_id)
    os.makedirs(output_dir, exist_ok=True)

    start_time = time.time()
    # Initialize BookIdeaSet with a base empty idea
    base_idea = BookIdea(
        description_of_idea="Empty idea",  # This is required from parent class
        title="Empty title",
        logline="Empty logline",
        genre="",  # Optional with default
        target_audience="",  # Optional with default
    )

    idea_set = BookIdeaSet()

    send_to_model = Models2BookIdeas()
    prompt_by_mode = set_mode_prompt(args.mode)
    print(
        f"Generating ideas with model {args.model} and prompt template: {prompt_by_mode}"
    )
    for batch in range(0, args.num_ideas, args.batch_size):
        batch_size = min(args.batch_size, args.num_ideas - batch)
        new_ideas = send_to_model.expand_idea(send_to_model.base_idea, num_variations=batch_size, prompt_template=prompt_by_mode)

        # Handle the new ideas
        if isinstance(new_ideas, list):
            for idea in new_ideas:
                # Assuming new_ideas contains dictionaries with 'title' and 'logline'
                book_idea = BookIdea(description_of_idea="Test")
                book_idea.title = "Title"
                book_idea.logline = "Logline"
                idea_set.add_idea(book_idea)
        else:
        # Handle single idea case
            if isinstance(new_ideas, dict):
                book_idea = BookIdea(
                    description_of_idea="",  # Add this required parameter
                    title=new_ideas.get('title', ''),
                    logline=new_ideas.get('logline', '')
                )
            elif isinstance(new_ideas, str):
                # Handle string case - possibly parse it or use it as is
                book_idea = BookIdea(
                    description_of_idea=new_ideas,
                    title="Generated Idea",  # Use a default title
                    logline=""  # Empty logline
                )
            else:
                logger.error(f"Unexpected type for new_ideas: {type(new_ideas)}")
                continue

            idea_set.add_idea(book_idea)

    print(idea_set)
    output_file_path = os.path.join(output_dir, "idea_set.csv")
    idea_set.save_idea_set_as_csv(idea_set.ideas, output_file_path)

    tournament = Tournament(idea_set.ideas)


    elapsed_time = time.time() - start_time
    seconds_per_idea = elapsed_time / idea_set.num_ideas
    seconds_per_match = elapsed_time / tournament.total_matches
    print(f"Ideas evaluated: {idea_set.num_ideas}")
    print(f"Tournament rounds completed: {len(tournament.rounds)}")
    print(f"Matches played: {tournament.total_matches}")
    print(f"Seconds per idea: {seconds_per_idea:.2f}")
    print(f"Seconds per match: {seconds_per_match:.2f}")
    print(f"Script completed in {elapsed_time:.2f} seconds")
    print(f"Results saved to: {output_file_path}")
    print(f"Model was {tournament.model}")

def set_mode_prompt(mode):
    if mode=="create":
        prompt_template=f"""You are an expert book editor and publisher. You are extremely knowledgeable about today's market for books and what makes a successful book in the modern era. You are familiar with all the genres, themes, plots and structures that have ever been used.  You are constantly working to come up with distinct and original book ideas.  
        
        Your task at this stage is to generate a set of 32 distinct, original, and unique ideas that will attract a coherent audience of readers.  Each idea should include a title and a logline.  THe logline is 2-3 sentences that includes key details such as but not limited to protagonist name, role, inner conflict; antagonist same; genre; plot points; revelations; mcguffins; and settings.
        
        The set of ideas should be a randomly chosen mix drawn from all genres, styles, and audiences reached by US publishers.  Your goal is for the mix to represent a healthy diversity that will be likely to succeed in the business and cultural conditions in the next 18 months.
        
        Please deliver the ideas as a csv with columns title,logline and 32 additional rows. No pleasantries, introductions, or concluding remarks."""

    elif mode == "create32":
        prompt_template="""
        You are an expert book editor and publisher. You are extremely knowledgeable about today's market for books and what makes a successful book in the modern era. You are familiar with all the genres, themes, plots and structures that have ever been used.  You are constantly working to come up with distinct and original book ideas.  
        
        Your task at this stage is to generate a set of 32 distinct, original, and unique ideas that will attract a coherent audience of readers.  Each idea should include a title and a logline.  THe logline is 2-3 sentences that includes key details such as but not limited to protagonist name, role, inner conflict; antagonist same; genre; plot points; revelations; mcguffins; and settings.
        
        The set of ideas should be a randomly chosen mix drawn from all genres, styles, and audiences reached by US publishers.  Your goal is for the mix to represent a healthy diversity that will be likely to succeed in the business and cultural conditions in the next 18 months.
        
        Please deliver the ideas as a csv with columns title,logline and 32 additional rows. No pleasantries, introductions, or concluding remarks."""

        if mode == "variations":
            prompt_template=f"""
        Return a JSON array of 4 variations for the given idea.

        Each variation must have these fields:
        - title
        - two- or three-sentence logline
        
        The logline must include but not be limited to information such as protagonist(s) w/role, identity, & inner conflicts; antagonists (same); story & character arc; twists/revelations; settings & sometimes mcguffins.

        Respond ONLY with a JSON array. No additional text or markdown.
        """,
    else:
        raise ValueError (f"Invalid mode: {mode}")
    return prompt_template

if __name__ == "__main__":
    main()
