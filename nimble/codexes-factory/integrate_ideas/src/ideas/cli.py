import argparse

def create_parser():
    # Create main parser with help enabled
    parser = argparse.ArgumentParser(description="Book Ideas Generation and Management Tool")

    # Common arguments
    parser.add_argument("--model", default="gpt-3.5-turbo", help="AI model to use")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for generation")
    parser.add_argument("--output_file_path", type=str, default="output/tournament_results.csv",
                        help="Path to output file")

    # Create a parent parser for common arguments (WITHOUT help)
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--model", default="gpt-3.5-turbo", help="AI model to use")
    parent_parser.add_argument("--api_type", default="openai", help="API type to use")
    parent_parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for generation")
    parent_parser.add_argument("--output_file_path", type=str, default="output/tournament_results.csv",
                               help="Path to output file")

    # Create subparsers
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create subparsers with the parent_parser instead of the main parser
    create_parser = subparsers.add_parser("create", help="Create new book ideas", parents=[parent_parser])
    create_parser.add_argument("--number_of_ideas", "-n", type=int, default=1, help="Number of ideas to generate")
    create_parser.add_argument("--custom_prompt", "-p", type=str, help="Custom prompt for idea generation")

    # Add other subparsers similarly
    tournament_parser = subparsers.add_parser("tournament", help="Run idea tournament", parents=[parent_parser])
    tournament_parser.add_argument("--idea_file_path", "-i", type=str, help="Path to input ideas file")
    tournament_parser.add_argument("--rounds", "-r", type=int, default=3, help="Number of tournament rounds")

    continuous_parser = subparsers.add_parser("continuous", help="Continuously generate ideas", parents=[parent_parser])
    continuous_parser.add_argument("--batch_size", type=int, default=5, help="Number of ideas per batch")
    continuous_parser.add_argument("--interval", type=int, default=300, help="Interval between batches in seconds")

    expand_parser = subparsers.add_parser("expand", help="Expand existing ideas using AI", parents=[parent_parser])
    expand_parser.add_argument("--lines_to_process", "-l", type=int, help="Number of lines to process")
    expand_parser.add_argument("--input_file", type=str, help="Input file with ideas to expand")

    bracket_parser = subparsers.add_parser('diy-bracket', parents=[parent_parser])
    bracket_parser.add_argument('--input', help='Input file containing book ideas', required=True)

    return parser