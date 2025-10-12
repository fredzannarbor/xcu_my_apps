import csv
import datetime
import logging
import math
import random
import json
from typing import List, Dict, Any, Set, TextIO, Union
import streamlit as st
import pandas as pd

import ollama
import openai

logging.getLogger().handlers = []

# Setup basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class Tournament:
    """
    Represents a tournament for arranging, managing, and simulating competition
    between a set of ideas. It organizes matchups, ranks ideas, and keeps track
    of the tournament's progress, rounds, and results.

    This class allows users to seamlessly manage the lifecycle of a tournament,
    from initializing participant ideas, assigning seeds, creating brackets,
    determining winners, and generating results summaries. The methods
    provided ensure flexible and efficient operations for various tournament use
    cases, including saving results as JSON and generating friendly round names.

    :ivar original_ideas: The original set of ideas for the tournament.
    :type original_ideas: set[Dict[str, Any]]
    :ivar seeded_ideas: List of ideas with assigned random seeds.
    :type seeded_ideas: list[Dict[str, Any]]
    :ivar total_matches: Total number of matches required to complete the tournament.
    :type total_matches: int
    :ivar rounds: A list containing all rounds of the tournament.
    :type rounds: list[Dict[str, Any]]
    :ivar total_ideas: The total number of participating ideas.
    :type total_ideas: int
    :ivar total_teams: The total number of teams after adding any necessary byes.
    :type total_teams: int
    :ivar model: The name of the AI model used for determining winning ideas.
    :type model: str
    :ivar temperature: Temperature setting used for the AI model.
    :type temperature: float
    :ivar api_type: The API type used for processing ideas.
    :type api_type: str
    """
    def __init__(self, ideas: set[Dict[str, Any]], model: str = "deepseek-r1:latest", temperature: float = 0.7,
                 api_type="ollama"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.original_ideas = ideas
        self.seeded_ideas = self.assign_random_seeds_to_ideas(ideas)
        self.total_matches = self._next_power_of_two(len(ideas)) - 1
        self.rounds = []
        self.total_ideas = len(ideas)
        self.total_teams = len(self.seeded_ideas)
        self.model = model
        self.temperature = temperature
        self.api_type = api_type


    @staticmethod
    def assign_random_seeds_to_ideas(original_ideas):
        seeded = []
        seeds = list(range(1, len(original_ideas) + 1))
        random.shuffle(seeds)
        for index, idea in enumerate(original_ideas):
            if isinstance(idea, dict):
                seeded.append({
                    "title": idea.get("title", "Untitled"),
                    "logline": idea.get("logline", "No logline provided"),
                    "seed": seeds[index]
                })
            elif hasattr(idea, 'title') and hasattr(idea, 'logline'):
                seeded.append({
                    "title": idea.title,
                    "logline": idea.logline,
                    "seed": seeds[index]
                })
            elif isinstance(idea, str):
                seeded.append({
                    "title": idea,
                    "logline": "No logline provided",
                    "seed": seeds[index]
                })
            else:
                raise TypeError(f"Unexpected type for idea: {type(idea)}")
        return seeded

    @staticmethod
    def _next_power_of_two(x):
        return 1 if x == 0 else 2 ** (x - 1).bit_length()

    def _add_byes(self):
        actual_count = len(self.seeded_ideas)
        next_power_two = self._next_power_of_two(actual_count)
        byes_needed = next_power_two - actual_count

        for _ in range(byes_needed):
            bye_idea = {
                "title": "BYE",
                "logline": "Automatic advancement due to insufficient teams.",
                "seed": float('inf')
            }
            self.seeded_ideas.append(bye_idea)

    def generate_summary(self):
        """
        Generates a textual summary of the tournament bracket, displaying all winners for each round.
        Returns:
            str: A formatted summary of the tournament results.
        """
        if not self.rounds:
            return "No rounds have been played yet."

        summary = []
        for round_data in self.rounds:
            round_name = self.get_friendly_round_name(round_data["round_number"], self.total_ideas)
            summary.append(f"**{round_name}**")
            summary.append("=" * len(round_name))

            for idx, match in enumerate(round_data["matches"], start=1):
                idea_a = match["idea_a"]["title"]
                idea_b = match["idea_b"]["title"]
                winner = match["winner"]["title"]
                summary.append(f"Match {idx}: {idea_a} vs {idea_b} -> Winner: {winner}")

            summary.append("\n")

        return "\n".join(summary)

    def save_summary_as_json(self, file_name: str = "output/tournament_summary.json"):
        """
        Saves the tournament summary as a JSON file.
        Args:
            file_name (str): The name of the file to save the summary to. Defaults to 'tournament_summary.json'.
        """
        summary = self.generate_summary()

        data = {
            "total_teams": self.total_teams,
            "rounds": self.rounds,
            "summary": summary
        }

        with open(file_name, "w") as json_file:
            json.dump(data, json_file, indent=4)

    def save_match_data_as_json(self, file_name: str = "output/tournament_match_data.json"):
        """
        Saves the raw grading responses along with idea_a, idea_b, winner, and round number to a JSON file.
        Args:
            file_name (str): The name of the file to save the data to. Defaults to 'tournament_match_data.json'.
        """
        match_data = []
        for round_data in self.rounds:
            for match in round_data["matches"]:
                match_entry = {
                    "round_number": match["round_number"],
                    "idea_a": {
                        "title": match["idea_a"]["title"],
                        "logline": match["idea_a"]["logline"],
                        "seed": match["idea_a"]["seed"]
                    },
                    "idea_b": {
                        "title": match["idea_b"]["title"],
                        "logline": match["idea_b"]["logline"],
                        "seed": match["idea_b"]["seed"]
                    },
                    "winner": {
                        "title": match["winner"]["title"],
                        "logline": match["winner"]["logline"],
                        "seed": match["winner"]["seed"]
                    },
                    "raw_grading_response": match["raw_grading_response"]
                }
                match_data.append(match_entry)

        with open(file_name, "w") as json_file:
            json.dump(match_data, json_file, indent=4)

        print(f"Match data saved to {file_name}")

    def create_brackets(self):
        # Ensure we have a power of two
        self._add_byes()
        current_round = self.seeded_ideas

        round_number = 1
        while len(current_round) > 1:
            matches = []
            winners = []
            for i in range(0, len(current_round), 2):
                idea_a = current_round[i]
                idea_b = current_round[i + 1]
                self.logger.debug(idea_a, idea_b)
                # Skip match if 'BYE'
                if idea_a["title"] == "BYE":
                    winner = idea_b
                    raw_response = "BYE - No grading needed"
                elif idea_b["title"] == "BYE":
                    winner = idea_a
                    raw_response = "BYE - No grading needed"
                else:
                    winner, raw_response = self.determine_winner_with_prompt(idea_a, idea_b)

                matches.append({
                    "idea_a": idea_a,
                    "idea_b": idea_b,
                    "winner": winner,
                    "raw_grading_response": raw_response,
                    "round_number": round_number
                })
                winners.append(winner)

            self.rounds.append({
                "round_number": round_number,
                "matches": matches,
                "winners": winners
            })

            current_round = winners
            round_number += 1

    def create_bracket_packet(self, ideas, bracket_output_file=None):
        """
        Creates a markdown-formatted bracket packet for manual scoring.

        Args:
            ideas: List of BookIdea objects or dict containing ideas to bracket
            output_file: Optional file path to save the markdown output

        Returns:
            str: Markdown formatted bracket packet
        """
        # Start building the markdown content
        markdown = []

        # Add title
        markdown.append("# Tournament Bracket Packet\n")

        # Create reference key section
        markdown.append("## Reference Key\n")
        markdown.append("| ID | Title | Logline |\n")
        markdown.append("|:---|:------|:--------|\n")

        # Add each idea to the reference key
        for idx, idea in enumerate(ideas, 1):
            title = idea.title if hasattr(idea, 'title') else idea.get('title')
            logline = idea.logline if hasattr(idea, 'logline') else idea.get('logline')
            markdown.append(f"| {idx} | {title} | {logline} |\n")

        markdown.append("\n## Bracket Matchups\n")

        # Create bracket matchups
        num_ideas = len(ideas)
        rounds = (num_ideas + 1) // 2

        for round_num in range(rounds):
            markdown.append(f"\n### Round {round_num + 1}\n")
            markdown.append("| Match | Idea A | Idea B | Winner | Notes |\n")
            markdown.append("|:------|:-------|:-------|:-------|:------|\n")

            # Calculate matchups for this round
            start_idx = round_num * 2
            if start_idx + 1 < num_ideas:
                markdown.append(f"| {round_num + 1} | {start_idx + 1} | {start_idx + 2} | | |\n")

        # Convert to string
        packet = "".join(markdown)

        # Save to file if output_file provided
        if bracket_output_file:
            with open(bracket_output_file, 'w') as f:
                f.write(packet)

        return packet

    def create_bracket_interface(ideas: List[Union[Dict, object]]):
        """
        Creates an interactive Streamlit interface for filling out brackets.

        Args:
            ideas: List of BookIdea objects or dictionaries containing ideas
        """
        st.title("Book Idea Tournament Bracket")

        # Convert ideas to a more manageable format
        idea_data = []
        for idx, idea in enumerate(ideas, 1):
            title = idea.title if hasattr(idea, 'title') else idea.get('title')
            logline = idea.logline if hasattr(idea, 'logline') else idea.get('logline')
            idea_data.append({
                'id': idx,
                'title': title,
                'logline': logline
            })

        # Create rounds
        num_ideas = len(idea_data)
        rounds = (num_ideas + 1) // 2

        # Store results in session state
        if 'winners' not in st.session_state:
            st.session_state.winners = {}

        # Display rounds
        for round_num in range(rounds):
            st.header(f"Round {round_num + 1}")

            # Calculate matchups for this round
            start_idx = round_num * 2
            if start_idx + 1 < num_ideas:
                idea_a = idea_data[start_idx]
                idea_b = idea_data[start_idx + 1]

                # Create columns for side-by-side comparison
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader(f"Idea A: {idea_a['title']}")
                    st.write(f"*{idea_a['logline']}*")

                with col2:
                    st.subheader(f"Idea B: {idea_b['title']}")
                    st.write(f"*{idea_b['logline']}*")

                # Create a unique key for this matchup
                match_key = f"match_{round_num}"

                # Radio button for selection
                winner = st.radio(
                    "Select the winning idea:",
                    [idea_a['title'], idea_b['title']],
                    key=match_key,
                    index=None  # No default selection
                )

                # Store the winner in session state
                if winner:
                    st.session_state.winners[match_key] = winner

                # Optional notes field
                notes = st.text_area(
                    "Notes for this matchup:",
                    key=f"notes_{round_num}",
                    height=100
                )

                st.divider()

        # Export results button
        if st.button("Export Results"):
            results = []
            for round_num in range(rounds):
                match_key = f"match_{round_num}"
                winner = st.session_state.winners.get(match_key, "No decision")
                notes = st.session_state.get(f"notes_{round_num}", "")

                results.append({
                    "Round": round_num + 1,
                    "Winner": winner,
                    "Notes": notes
                })

            # Convert results to DataFrame
            df = pd.DataFrame(results)

            # Create a download button for the results
            st.download_button(
                label="Download Results CSV",
                data=df.to_csv(index=False),
                file_name="bracket_results.csv",
                mime="text/csv"
            )

        # Display current standings
        if st.session_state.winners:
            st.sidebar.header("Current Standings")
            for match, winner in st.session_state.winners.items():
                st.sidebar.write(f"{match}: {winner}")

    def get_friendly_round_name(self, round_number, total_teams):
        def next_power_of_two(n):
            return 2 ** math.ceil(math.log2(n))

        # Calculate initial round size (starting round)
        current_size = next_power_of_two(total_teams)

        # Handle play-in situation separately
        is_playin = total_teams != current_size
        if is_playin:
            if round_number == 1:
                return "Play-in"
            round_number -= 1

        # Obtain number of teams left in this round accurately:
        teams_in_round = current_size // (2 ** (round_number - 1))

        # Clearly mapped standard round names
        round_names = {
            2: "Championship",
            4: "Final Four",
            8: "Elite Eight",
            16: "Sweet Sixteen",
            32: "Round of 32",
            64: "Round of 64",
            128: "Round of 128",
            256: "Round of 256"
        }

        friendly_name = round_names.get(teams_in_round, f"Round of {teams_in_round}")
        return friendly_name

    def get_rounds_results(self):
        """
        Returns a detailed list of all rounds in the tournament, including matches and winners.
        """
        return self.rounds

    @staticmethod
    def determine_winner_randomly(idea_a: Dict[str, Any], idea_b: Dict[str, Any]) -> Dict[str, Any]:
        # Temporary logic: randomly choose a winner
        return random.choice([idea_a, idea_b])

    def determine_winner_with_prompt(self, idea_a: Dict[str, Any], idea_b: Dict[str, Any]):
        """
        Determines the winner between two ideas using a prompt-based approach and returns the raw response.
        Args:
            idea_a: The first idea.
            idea_b: The second idea.
        Returns:
            Tuple: (winning idea, raw grading response)
        """
        if self.api_type == "ollama":
            raw_grading_response = self._grade_with_ollama_(idea_a, idea_b, self.model, self.temperature)
        elif self.api_type == "openai":
            raw_grading_response = self.grade_with_open_ai_compatible_apis(idea_a, idea_b, self.model, self.temperature)
        else:
            self.logger.error(f"Unsupported API type: {self.api_type}")
            return
        self.logger.debug(f"raw_grading_response is {raw_grading_response}")

        if raw_grading_response:
            # Remove everything between <think> and </think>
            if "<think>" in raw_grading_response and "</think>" in raw_grading_response:
                self.logger.debug("removing think tags")
                raw_grading_response_clean = raw_grading_response.split("<think>")[0] + raw_grading_response.split("</think>")[1]
            else:
                raw_grading_response_clean = raw_grading_response

            # Strip leading/trailing spaces
            raw_grading_response_clean = raw_grading_response_clean.strip()

            # Check if the response is a single character
            if len(raw_grading_response_clean) == 1:
                winner_letter = raw_grading_response_clean
                self.logger.debug(f'winner letter is {winner_letter}')
                if winner_letter == "A":
                    return idea_a, raw_grading_response
                elif winner_letter == "B":
                    return idea_b, raw_grading_response

            # If response is unexpected, fall back to random choice
            self.logger.warning(f"Unexpected response from model in match between {idea_a} and {idea_b}, falling back to RANDOM choice: {raw_grading_response}")
            return random.choice([idea_a, idea_b]), raw_grading_response

        else:
            self.logger.error("Error: No response from model.")
            return random.choice([idea_a, idea_b]), "Error: No response from model."

    def _grade_with_ollama_(self, idea_a: Dict[str, Any], idea_b: Dict[str, Any], model: str, temperature: float) -> str:
        """
        Determines the winner between two ideas using a prompt-based approach.
        Args:
            idea_a: The first idea.
            idea_b: The second idea.
            model: The model to use for the prompt.
            temperature: The temperature for the model.
        Returns:
            The raw grading response from the model.
        """
        prompt = f"""
        You are an expert book editor and publisher. You are extremely knowledgeable about today's market for books and what makes a successful book in the modern era.
        You are familiar with all the genres, themes, plots and structures that have ever been used.
        Given the following two book ideas, determine which one is more likely to be successful in today's market.
        Idea A:
        Title: {idea_a['title']}
        Logline: {idea_a['logline']}
        Idea B:
        Title: {idea_b['title']}
        Logline: {idea_b['logline']}
        Respond ONLY with the letter of the winning idea, either A or B. No additional text or markdown.
        """
        self.logger.debug("prompt is")
        self.logger.debug(prompt)
        try:
            response = ollama.generate(
                model=model,
                prompt=prompt,
                options={
                    "temperature": temperature
                }
            )

            full_text = response['response']
            self.logger.debug("full text:")
            self.logger.debug(full_text)
            return full_text

        except Exception as e:
            self.logger.error(f"Error generating ideas with Ollama: {e}")
            return ""

    def grade_with_open_ai_compatible_apis(self, idea_a, idea_b, model, temperature, grading_prompt=None):

        """
        Generate ideas using OpenAI-compatible API.

        Args:
            grading_prompt: The prompt to send to the model.
        Returns:
            Grading response from the model.
        """
        grading_prompt = prompt = f"""
        You are an expert book editor and publisher. You are extremely knowledgeable about today's market for books and what makes a successful book in the modern era.
        You are familiar with all the genres, themes, plots and structures that have ever been used.
        Given the following two book ideas, determine which one is more likely to be successful in today's market.
        Idea A:
        Title: {idea_a['title']}
        Logline: {idea_a['title']}
        Idea B:
        Title: {idea_b['title']}
        Logline: {idea_a['logline']}

        Respond ONLY with the letter of the winning idea, either A or B. No additional text or markdown.
        """

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a creative writing assistant."},
                    {"role": "user", "content": grading_prompt}
                ],
                temperature=self.temperature,
                max_tokens=500
            )
            raw_grading_response = response["choices"][0]["message"]["content"].split("\n")
            return raw_grading_response #[idea.strip() for idea in expanded_ideas if idea.strip()]
        except Exception as e:
            print(f"Error generating ideas with OpenAI: {e}")
            return []

class ShowTournamentResults(Tournament):
    """
    Represents a class for displaying and managing tournament results.

    This class inherits from the Tournament class and provides functionality to
    generate a readable summary of the tournament results and save the results
    to a CSV file.

    :ivar rounds: List of dictionaries representing the rounds of the tournament.
                  Each dictionary contains information like matches and winners
                  for a specific round.
    :type rounds: list
    :ivar number_of_ideas: The total number of ideas/participants in the tournament.
    :type number_of_ideas: int
    """
    def __init__(self, rounds, number_of_ideas):
        self.rounds = rounds
        self.number_of_ideas = number_of_ideas

    # Generate an alternative readable view of the results
    def generate_readable_results(self):
        results = self.rounds
        readable_summary = []
        readable_summary.append(f"Tournament Results Summary\n{'=' * 30}")
        readable_summary.append(f"Total Ideas: {self.number_of_ideas}")

        for round_result in results:
            round_name = self.get_friendly_round_name(round_result['round_number'], self.number_of_ideas)
            readable_summary.append(f"\n{round_name}\n{'-' * len(round_name)}")
            for match in round_result.get('matches', []):
                title1 = match['idea_a']['title'].split(' - ')[0]
                title2 = match['idea_b']['title'].split(' - ')[0]
                seed1 = match['idea_a'].get('seed', '?')
                seed2 = match['idea_b'].get('seed', '?')

                # Safely check for winner
                winner = match.get('winner')
                if winner:
                    if match['idea_a'] == winner:
                        seed1 = f"W/{seed1}"
                    if match['idea_b'] == winner:
                        seed2 = f"W/{seed2}"

                readable_summary.append(f"{title1} ({seed1}) v. {title2} ({seed2})")

        # Safely check for final winner
        final_winner = None
        if results and results[-1].get('winners') and len(results[-1]['winners']) == 1:
            final_winner = results[-1]['winners'][0]['title'].split(' - ')[0]

        if final_winner:
            readable_summary.append(f"\nChampion of the Tournament: {final_winner}")

        return '\n'.join(readable_summary)

    def save_results_to_csv(self, filename):
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['round_number', 'title1', 'title2', 'seed1', 'seed2', 'winner']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for round_result in self.rounds:
                round_num = round_result.get('round_number')
                if not isinstance(round_num, (int, str)):
                    raise ValueError("Invalid round number")

                for match in round_result.get('matches', []):
                    try:
                        # Extract required data safely
                        idea_a = match.get('idea_a', {})
                        idea_b = match.get('idea_b', {})

                        if not idea_a or not idea_b:
                            raise ValueError("Match missing idea_a or idea_b")

                        title1 = idea_a['title'].split(' - ')[0]
                        title2 = idea_b['title'].split(' - ')[0]
                        seed1 = idea_a.get('seed', '')
                        seed2 = idea_b.get('seed', '')

                        # Handle case when winner might not exist
                        winner = ''
                        if 'winner' in match:
                            winner = match['winner']['title'].split(' - ')[0]

                        writer.writerow({
                            'round_number': round_num,
                            'title1': title1,
                            'title2': title2,
                            'seed1': seed1,
                            'seed2': seed2,
                            'winner': winner
                        })
                    except (KeyError, TypeError) as e:
                        raise ValueError(f"Invalid match data structure: {str(e)}")

