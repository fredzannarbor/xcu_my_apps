from datetime import datetime


class Utilities:
    """
    Utility class containing helper functions for the Ideas project.
    """

    @staticmethod
    def generate_run_id():
        """
        Generate a unique run ID based on timestamp.

        Returns:
            str: A unique identifier string
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")


if __name__ == '__main__':
    # Example usage
    utils = Utilities()
    run_id = utils.generate_run_id()
    print(f"Generated run ID: {run_id}")
