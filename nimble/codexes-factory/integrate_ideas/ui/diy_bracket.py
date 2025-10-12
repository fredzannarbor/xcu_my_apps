import streamlit as st
import json
import argparse


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', help='Input file containing book ideas')
    args = parser.parse_args()

    # Load ideas
    with open(args.input, 'r') as f:
        ideas = json.load(f)

    # Create the bracket interface
    create_bracket_interface(ideas)


if __name__ == '__main__':
    main()
