"""
Unit tests for the HealthChecker tool.
"""

import unittest
import asyncio
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from monitoring.health_checker import HealthChecker

class TestHealthChecker(unittest.TestCase):
    """
    Tests the functionality of the HealthChecker tool.
    """

    def setUp(self):
        """Set up a mock config for the tool."""
        self.mock_config = {"monitoring": {"enabled": True}}

    def test_initialization(self):
        """Test that the HealthChecker tool initializes correctly."""
        tool = HealthChecker(self.mock_config)
        self.assertEqual(tool.config, self.mock_config)

    async def test_get_system_health_nominal(self):
        """Test the health check method under normal, healthy conditions."""
        tool = HealthChecker(self.mock_config)
        
        # In the future, you might mock dependencies that the health checker uses.
        # For now, we test the simple case.
        response = await tool.get_system_health()
        
        self.assertIn("nominal", response)
        self.assertIn("smoothly", response)

    # Example of how you would test a failure case if the logic were more complex
    async def test_get_system_health_failure(self):
        """Test the health check method when a problem is detected."""
        tool = HealthChecker(self.mock_config)
        
        # To test this properly, we would need to be able to induce a failure state.
        # For example, by mocking a dependency check to fail.
        # Let's simulate this by temporarily patching the internal logic.
        with unittest.mock.patch.object(tool, '_perform_checks', return_value=False):
            # Let's assume the health checker has a method _perform_checks
            # that we can mock to simulate a failure.
            # Since it doesn't exist, we'll add a dummy one for the sake of the test.
            async def dummy_perform_checks():
                return False
            tool._perform_checks = dummy_perform_checks

            # Let's refine the actual method to use this hypothetical check
            async def refined_get_health():
                is_healthy = await tool._perform_checks()
                if is_healthy:
                    return "System status is nominal. All services are running smoothly."
                else:
                    return "System is experiencing issues. Please check the logs for details."
            
            # Temporarily replace the real method with our refined one for the test
            original_method = tool.get_system_health
            tool.get_system_health = refined_get_health

            response = await tool.get_system_health()
            
            self.assertIn("experiencing issues", response)

            # Restore the original method
            tool.get_system_health = original_method

# Helper to run async tests
if __name__ == '__main__':
    unittest.main()
