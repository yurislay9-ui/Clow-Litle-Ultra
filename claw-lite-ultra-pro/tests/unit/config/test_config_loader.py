"""
Unit tests for the configuration loader.
"""

import unittest
from unittest.mock import patch, mock_open
import os

# Add the src directory to the Python path to allow for absolute imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from config.config_loader import load_config, _deep_merge

class TestConfigLoader(unittest.TestCase):
    """
    Tests the functionality of the config loader.
    """

    def test_deep_merge(self):
        """Test the deep merge functionality."""
        dest = {'a': 1, 'b': {'c': 2, 'd': 3}}
        source = {'b': {'c': 4, 'e': 5}, 'f': 6}
        expected = {'a': 1, 'b': {'c': 4, 'd': 3, 'e': 5}, 'f': 6}
        self.assertEqual(_deep_merge(source, dest), expected)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_base_config_only(self, mock_file, mock_exists):
        """Test loading only the base configuration file."""
        # Mock that the base file exists, but the env file does not
        def exists_side_effect(path):
            if 'defaults.toml' in path:
                return True
            return False
        mock_exists.side_effect = exists_side_effect

        base_config_content = '[database]\nhost = "localhost"\n'
        mock_file.return_value.read.return_value = base_config_content
        
        config = load_config()
        
        self.assertEqual(config['database']['host'], 'localhost')
        # Ensure the mock file was opened at the correct path
        mock_file.assert_called_once_with(os.path.join(os.path.dirname(__file__), '..", "..", "src", "config", 'defaults.toml'), 'r', encoding='utf-8')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    def test_load_with_env_override(self, mock_file, mock_exists):
        """Test that environment config correctly overrides the base config."""
        base_config_content = '[database]\nhost = "localhost"\nport = 5432\n'
        prod_config_content = '[database]\nhost = "prod-db.example.com"\n'

        # Mock reading the base file first, then the prod file
        mock_file().read.side_effect = [base_config_content, prod_config_content]

        with patch.dict(os.environ, {'APP_ENV': 'production'}):
            config = load_config()
        
        self.assertEqual(config['database']['host'], 'prod-db.example.com')
        self.assertEqual(config['database']['port'], 5432) # Should persist from base

    @patch('os.path.exists', return_value=False)
    def test_base_config_not_found(self, mock_exists):
        """Test that a FileNotFoundError is raised if the base config is missing."""
        with self.assertRaises(FileNotFoundError):
            load_config()

if __name__ == '__main__':
    unittest.main()
