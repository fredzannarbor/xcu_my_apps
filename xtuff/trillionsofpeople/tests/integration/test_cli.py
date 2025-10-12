"""
Integration tests for CLI functionality.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
import tempfile
import os

from trillions_of_people.cli.main import main


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create Click test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_env(self):
        """Create temporary environment with API key."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test' + 'x' * 45}):
            yield

    def test_main_help(self, runner):
        """Test main help command."""
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "Trillions of People" in result.output
        assert "Generate synthetic people data" in result.output

    def test_main_version(self, runner):
        """Test version command."""
        result = runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert "version 1.0.0" in result.output

    def test_status_command(self, runner):
        """Test status command."""
        result = runner.invoke(main, ['status'])
        assert result.exit_code == 0
        assert "System Status" in result.output

    def test_countries_command(self, runner):
        """Test countries listing command."""
        result = runner.invoke(main, ['countries'])
        assert result.exit_code == 0
        assert "Available countries:" in result.output
        assert "United States" in result.output

    def test_browse_command_empty(self, runner):
        """Test browse command with no data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('trillions_of_people.modules.people_utilities.PeopleManager') as mock_manager:
                mock_instance = Mock()
                mock_manager.return_value = mock_instance
                mock_instance.browse_people.return_value = Mock(empty=True)

                result = runner.invoke(main, ['browse'])
                assert result.exit_code == 0
                assert "No personas found" in result.output

    @patch('trillions_of_people.modules.people_utilities.PeopleManager')
    def test_browse_command_with_data(self, mock_manager, runner):
        """Test browse command with existing data."""
        import pandas as pd

        mock_instance = Mock()
        mock_manager.return_value = mock_instance

        # Mock DataFrame with data
        test_data = pd.DataFrame({
            'name': ['John Doe', 'Jane Smith'],
            'age': [30, 25],
            'country': ['US', 'CA']
        })
        mock_instance.browse_people.return_value = test_data

        result = runner.invoke(main, ['browse'])
        assert result.exit_code == 0
        assert "Found 2 personas" in result.output
        assert "John Doe" in result.output

    def test_generate_no_api_key(self, runner):
        """Test generate command without API key."""
        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        assert "API key required" in result.output

    @patch('trillions_of_people.modules.people_utilities.PeopleManager')
    def test_generate_with_api_key(self, mock_manager, runner, temp_env):
        """Test generate command with API key."""
        import pandas as pd

        mock_instance = Mock()
        mock_manager.return_value = mock_instance

        # Mock successful generation
        mock_people_df = pd.DataFrame({'name': ['Test Person'], 'age': [30]})
        mock_card_df = pd.DataFrame({'Attributes': ['Name'], 'Values': ['Test Person']})
        mock_instance.create_new_people.return_value = (mock_people_df, mock_card_df)
        mock_instance.load_countries.return_value = {'United States': 'US', 'Random': 'RANDOM'}
        mock_instance.save_people.return_value = True

        result = runner.invoke(main, ['generate', '--country', 'United States', '--count', '1'])
        assert result.exit_code == 0
        assert "Generating 1 persona(s)" in result.output

    @patch('trillions_of_people.modules.people_utilities.PeopleManager')
    def test_generate_random_country(self, mock_manager, runner, temp_env):
        """Test generate command with random country."""
        mock_instance = Mock()
        mock_manager.return_value = mock_instance

        # Mock data
        mock_countries = {'United States': 'US', 'Canada': 'CA', 'Random': 'RANDOM'}
        mock_instance.load_countries.return_value = mock_countries

        # Mock generation failure to keep test simple
        mock_instance.create_new_people.return_value = (Mock(empty=True), Mock())

        result = runner.invoke(main, ['generate', '--country', 'Random'])
        assert result.exit_code == 0
        assert "Randomly selected country:" in result.output

    def test_generate_with_output_file(self, runner, temp_env):
        """Test generate command with output file."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            output_file = f.name

        try:
            with patch('trillions_of_people.modules.people_utilities.PeopleManager') as mock_manager:
                import pandas as pd

                mock_instance = Mock()
                mock_manager.return_value = mock_instance

                # Mock successful generation
                mock_people_df = pd.DataFrame({'name': ['Test Person']})
                mock_card_df = pd.DataFrame({'Attributes': ['Name'], 'Values': ['Test Person']})
                mock_instance.create_new_people.return_value = (mock_people_df, mock_card_df)
                mock_instance.load_countries.return_value = {'United States': 'US'}

                result = runner.invoke(main, [
                    'generate',
                    '--country', 'United States',
                    '--output', output_file
                ])
                assert result.exit_code == 0
                assert f"Saved 1 personas to {output_file}" in result.output

        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_browse_json_format(self, runner):
        """Test browse command with JSON format."""
        with patch('trillions_of_people.modules.people_utilities.PeopleManager') as mock_manager:
            import pandas as pd

            mock_instance = Mock()
            mock_manager.return_value = mock_instance

            test_data = pd.DataFrame({'name': ['John Doe'], 'age': [30]})
            mock_instance.browse_people.return_value = test_data

            result = runner.invoke(main, ['browse', '--format', 'json'])
            assert result.exit_code == 0
            assert '"name": "John Doe"' in result.output or 'John Doe' in result.output

    def test_browse_with_limit(self, runner):
        """Test browse command with limit."""
        with patch('trillions_of_people.modules.people_utilities.PeopleManager') as mock_manager:
            import pandas as pd

            mock_instance = Mock()
            mock_manager.return_value = mock_instance

            test_data = pd.DataFrame({
                'name': ['Person1', 'Person2'],
                'age': [20, 30]
            })
            mock_instance.browse_people.return_value = test_data

            result = runner.invoke(main, ['browse', '--limit', '1'])
            assert result.exit_code == 0
            mock_instance.browse_people.assert_called_with(limit=1)

    @patch('trillions_of_people.modules.people_utilities.PeopleManager')
    def test_generate_error_handling(self, mock_manager, runner, temp_env):
        """Test generate command error handling."""
        mock_instance = Mock()
        mock_manager.return_value = mock_instance

        # Mock error
        mock_instance.load_countries.side_effect = Exception("Test error")

        result = runner.invoke(main, ['generate'])
        assert result.exit_code == 0
        assert "Error:" in result.output