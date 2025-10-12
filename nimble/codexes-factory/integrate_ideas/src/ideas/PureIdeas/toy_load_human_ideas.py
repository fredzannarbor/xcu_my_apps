# test_idea_collector_poc.py
from src.ideas.PureIdeas.Idea import Idea, IdeaSet


def create_test_file():
    """Create a test file with some sample ideas"""
    test_ideas = [
        "A mystery novel set in a library with missing books as clues",
        "A cookbook that tells stories through recipes",
        "A gardening guide for growing magical plants"
    ]

    with open("test_ideas.txt", "w") as f:
        for idea in test_ideas:
            f.write(idea + "\n")


def main():
    # First create our test file
    create_test_file()

    # Read ideas from file
    ideas = []
    with open("test_ideas.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line:
                idea = Idea(line)
                ideas.append(idea)

    # Create an IdeaSet from the ideas
    idea_set = IdeaSet(ideas)

    # Print the results
    print("\nCollected Ideas:")
    print("===============")
    for i, idea in enumerate(idea_set.ideas, 1):
        print(f"{i}. {idea}")

    # Print some basic validation
    print(f"\nTotal ideas collected: {len(idea_set.ideas)}")


if __name__ == "__main__":
    main()
