import argparse
from src.ideas.cli import create_parser
import logging
import re
import ssl
import traceback
import csv
from uuid import uuid4
import openai
import ollama
import pandas as pd
import json
from typing import List, Dict, Optional, Union
from tqdm import tqdm
from datetime import datetime
import random
import nltk
from nltk.corpus import words



# Reset logging configuration
logging.getLogger().handlers = []
logging.getLogger("httpx").setLevel(logging.WARNING)


# Setup basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class Models2BookIdeas:
    """
    A class to generate expanded book ideas using either the Ollama API or OpenAI-compatible models.
    """

    base_idea = None

    def __init__(self, model: str = "deepseek-r1:latest", temperature: float = 0.7,
    api_type: str = "ollama", ollama_host: str = "http://localhost:11434"):
        """
        Initialize the idea expander.

        Args:
            model: The model name (for OpenAI or Ollama).
            temperature: The creativity setting for AI responses.
            api_type: The API type to use ("ollama" or "openai").
            ollama_host: The base URL for Ollama API (e.g., http://localhost:11434)
        """

        # Initialize logger first
        self.logger = logging.getLogger(self.__class__.__name__)

        # initialize model
        self.model = model
        self.temperature = temperature
        self.api_type = api_type.lower()
        self.ollama_host = ollama_host.rstrip('/')
        self.api_url = f"{self.ollama_host}/api/generate"  # Construct full Ollama API URL
        # initialize prompts
        # self.create_book_idea_base_prompt = """You are a book publisher, editor, and author with exhaustive knowledge of all genres of publishing.  You are familiar with all the genres, themes, plots and structures that have ever been used.  You are extremely knowledgeable about today's market for books and what makes a successful book in the modern era.
        #
        # Your initial task here is to create a single promising book idea.  The idea should be both creatively excellent and commercially viable.
        #
        # Your response should be valid JSON with ONLY these two keys: title and logline. The logline must include but not be limited to information such as protagonist(s) w/role, identity, & inner conflicts; antagonists (same); story & character arc; twists/revelations; settings & sometimes McGuffins. Do NOT include any other keys.  No introductions, pleasantries, or concluding remarks."""
        self.create_book_idea_base_prompt = """
You are a book publisher, editor, and author with exhaustive knowledge of all genres of publishing.  You are familiar with all the genres, themes, plots and structures that have ever been used.  You are extremely knowledgeable about today's market for books and what makes a successful book in the modern era. 

Your initial task here is to create a single promising book idea.  The idea should be both creatively excellent and commercially viable.

Your response should be valid JSON with ONLY these two keys: title and logline. Do NOT include any other keys.  No introductions, pleasantries, or concluding remarks."""
        self.number_of_variations_per_expansion = 4

    def create_idea(self, custom_prompt: str = None) -> str:
        """
        Create a single new book idea.

        :param custom_idea_prompt:
        :param idea:
        :param custom_prompt:
        :return:
        """
        random_words = self.get_words(3,   5, 10, True, True, 8000)

        # convert random words into comma-delimited string
        random_words_str = ', '.join(random_words)
        self.logger.debug(f"random words: {random_words_str}")
        if not custom_prompt and random_words:
            prompt = self.create_book_idea_base_prompt + "Draw inspiration from the three following words: " + random_words_str + "."
            self.logger.debug(f"Prompt with seed ... {prompt[-40:]}...")
        elif custom_prompt:

            prompt = self.create_book_idea_base_prompt +"\n\n" + custom_prompt + "\n\n" + "Draw inspiration from the three following words: " + random_words_str + "."
            # print(f"with custom prompt:\n\n{prompt}")
            self.logger.debug(f"Custom prompt: {prompt[-40:]}...")

        new_idea = self._create_with_ollama(prompt, self.model, self.temperature)
        self.logger.debug(f"Created new idea with ollama: {new_idea}")

        return new_idea

    def _create_with_ollama(self, prompt, model, temperature):
        self.logger.info(f"submitting {prompt}")
        try:
            response = ollama.generate(
                model=model,
                prompt=prompt,
                format="json",
                options={
                    "temperature": temperature
                }
            )
            string_response = response['response']
            logger.debug(f"Generated idea: {string_response[:25]}")
            created_idea = json.loads(string_response)
            return created_idea
        
        except Exception as e:
            logger.error(f"Error generating ideas with Ollama: {traceback.format_exc()}")
            return []

    def get_words(self,
                  n: int = 1,
              min_length: Optional[int] = None,
              max_length: Optional[int] = None,
              unique: bool = True,
              common_only: bool = False,
              top_n: Optional[int] = None) -> Union[str, List[str]]:
        """
        Returns random word(s) from NLTK's corpus, with options for common words.

        Args:
            n (int): Number of words to return. Defaults to 1.
            min_length (int, optional): Minimum length of the words
            max_length (int, optional): Maximum length of the words
            unique (bool): Whether to return unique words. Defaults to True.
            common_only (bool): If True, selects from most frequent words. Defaults to False.
            top_n (int, optional): If common_only is True, selects from top N frequent words.

        Returns:
            Union[str, List[str]]: If n=1, returns a single word as string.
                                  If n>1, returns a list of words.
        """
        try:
            # Handle SSL certificate verification
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                pass
            else:
                ssl._create_default_https_context = _create_unverified_https_context

            # Download required NLTK data
            nltk.download('words', quiet=True)

            if common_only:
                nltk.download('brown', quiet=True)
                from nltk.corpus import brown
                word_freq = nltk.FreqDist(word.lower() for word in brown.words())
                top_n = top_n or 3000  # Default to top 3000 if not specified
                word_list = [word for word, _ in word_freq.most_common(top_n * 2)
                             if word.isalpha() and len(word) > 1][:top_n]
            else:
                from nltk.corpus import words
                word_list = words.words()

            # Apply length filters if specified
            if min_length is not None or max_length is not None:
                min_len = min_length if min_length is not None else 0
                max_len = max_length if max_length is not None else float('inf')
                word_list = [word for word in word_list
                             if min_len <= len(word) <= max_len]

            if not word_list:
                raise ValueError("No words found matching the criteria")

            if unique and n > len(word_list):
                raise ValueError(
                    f"Requested {n} unique words but only {len(word_list)} words "
                    f"match the criteria"
                )

            # Return results
            if n == 1:
                return random.choice(word_list)
            else:
                if unique:
                    return random.sample(word_list, n)
                else:
                    return [random.choice(word_list) for _ in range(n)]

        except LookupError:
            raise LookupError("Unable to download required NLTK data")
        except Exception as e:
            raise Exception(f"Error getting words: {str(e)}")

    def _expand_with_ollama(self, prompt: str, idea: str) -> List[str]:

        logger.info(f"submitting to ollama with {self.model} and {self.temperature}")
        try:
            response = ollama.generate(
                model=self.model,
                prompt=f"""
                Return a JSON array of 4 variations for the following idea: {prompt}

                Each variation must have these fields:
                - title
                - two- or three-sentence logline
                
                The logline must include but not be limited to information such as protagonist(s) w/role, identity, & inner conflicts; antagonists (same); story & character arc; twists/revelations; settings & sometimes mcguffins.

                Respond ONLY with a JSON array. No additional text or markdown.
                """,
                options={
                    "temperature": self.temperature
                }
            )
            self.logger.debug("inside _expand_with_ollama")
            self.logger.debug(response['response'])

            full_text = response['response']
            self.logger.info('full text')
            self.logger.info(full_text)

            result_dict = {
                "metadata": response['response'],
                "original_idea": idea,
                "variations": []
            }

            # Extract JSON between ``` markers if present
            if '```json' in full_text and '```' in full_text[full_text.find('```json') + 7:]:
                json_start = full_text.find('```json') + 7
                json_end = full_text.find('```', json_start)
                full_text = full_text[json_start:json_end].strip()

                # extract variations
                variations = json.loads(full_text)

                # Update the result dict with full metadata
                result_dict = {
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "model": self.model,
                        "temperature": self.temperature,
                        "api_type": self.api_type
                    },
                    "original_idea": idea,
                    "variations": variations
                }

            return result_dict

        except Exception as e:
            print(f"Error generating ideas with Ollama: {e}")
            # Return the basic dictionary structure even on error
            return {
                "metadata": str(e),
                "original_idea": idea,
                "variations": []
            }

    def remove_thinking(self, text):
        # remove all text beginning with <think* and ending with </think>
        return re.sub(r'<think.*?>(.*?)</think>', '', text, flags=re.DOTALL)


    def _expand_with_openai(self, prompt: str) -> List[str]:
        """
        Generate ideas using OpenAI-compatible API.

        Args:
            prompt: The prompt to send to the model.
        Returns:
            List of generated ideas.
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a creative writing assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=500
            )
            expanded_ideas = response["choices"][0]["message"]["content"].split("\n")
            return [idea.strip() for idea in expanded_ideas if idea.strip()]
        except Exception as e:
            print(f"Error generating ideas with OpenAI: {e}")
            return []

    def expand_idea(self, idea, num_variations, custom_prompt: str = None, custom_prompt_file_path=None) -> str:
        """
        Expand a single book idea into many variation
        """



        new_idea = self._create_with_ollama(prompt, self.model, self.temperature)
        self.logger.debug(f"Created new idea with ollama: {new_idea}")

        return new_idea

    def expand_ideas_batch(self, ideas: List[str], num_variations: int = 5, prompt_template: str = None) -> Dict[
        str, List[str]]:
        """
        Expand a batch of book ideas.

        Args:
            ideas: List of initial book ideas.
            num_variations: Number of variations per idea.
            prompt_template: Custom prompt template to use.
        Returns:
            Dictionary mapping original ideas to expanded ideas.
        """
        results = {}
        for idea in tqdm(ideas, desc="Expanding ideas", unit="idea"):
            print(idea, num_variations, prompt_template)
            results[idea] = self.expand_idea(idea, num_variations, prompt_template)
            logger.info('---')
            logger.info(results[idea])
            logger.info('---')
        return results


    def save_to_json(self, data: Dict[str, List[str]], output_file: str) -> None:
        """
        Save the expanded ideas to a JSON file.
    
        Args:
            data: Dictionary containing original ideas and their variations
            output_file: Path to the output JSON file
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def save_to_csv(self, seed_dict: Dict[str, List[str]], output_file: str):
        try:
            df = pd.DataFrame.from_dict(seed_dict, orient='index')
            df.to_csv(output_file)
            print(f"Saved CSV file to: {output_file}")  # Using print for now to avoid any logging issues

        except Exception as e:
            print(f"Error saving to CSV: {str(e)}")  # Using print for now
            raise



if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    # Initialize the expander with command line arguments
    expander = Models2BookIdeas(
        model=args.model,
        temperature=args.temperature,
        api_type=args.api_type,
        ollama_host=args.ollama_host
    )


    # Determine whether to use batch mode or single idea mode
    if args.batch:
        try:
            with open(args.batch, 'r') as file:
                # if file ends with txt:
                if args.batch.endswith('.txt'):
                    ideas = [line.strip() for line in file]
                # if file ends with csv:
                elif args.batch.endswith('.csv'):
                    df = pd.read_csv(args.batch)
                    ideas = df['idea'].tolist()
                # if ends with json:
                elif args.batch.endswith('.json'):
                    with open(args.batch, 'r') as f:
                        data = json.load(f)
                        ideas = [f"{item['title']} - {item['logline']}" for item in data if
                                 'title' in item and 'logline' in item]

            if not ideas:
                print(f"No ideas found in {args.batch}")
                exit(1)

            expanded_dict = expander.expand_ideas_batch(ideas, args.variations, args.prompt)

            # Save to file if output path is provided
            if args.output:
                if args.format == 'json':
                    expander.save_to_json(expanded_dict, args.output)
                else:  # csv
                    expander.save_to_csv(expanded_dict, args.output)
            else:
                # Print results to console
                for original, variations in expanded_dict.items():
                    print(f"\nOriginal idea: {original}")
                    print("\nExpanded variations:")
                    for i, variation in enumerate(variations, 1):
                        print(f"{i}. {variation}")
                    print("-" * 50)

        except FileNotFoundError:
            print(f"Error: File '{args.batch}' not found.")
            exit(1)

    elif args.idea:
        # Single idea mode
        expanded = expander.expand_idea(args.idea, args.variations, args.prompt)
        print(f"Expanded: {expanded}")
        # Save to file if output path is provided
        if args.output:
            if args.format == 'json':
            # write expanded as json file
                expander.save_to_json(expanded, args.output)

            else:  # csv
                expander.save_to_csv({args.idea: expanded}, args.output)
        else:
            # Print results to console
            print(f"\nOriginal idea: {args.idea}")
            print("\nExpanded variations:")
            for i, variation in enumerate(expanded, 1):
                print(f"{i}. {variation}")

    else:
        print("Error: Please provide either an idea or a batch file path.")
        exit(1)
