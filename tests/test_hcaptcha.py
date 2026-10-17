import unittest
from unittest.mock import Mock, patch
from udio_wrapper import UdioWrapper, is_hcaptcha_blocked


class TestHCaptchaSolver(unittest.TestCase):
    def setUp(self):
        self.solver = None
        self.fake_response_500 = None
        self.fake_response_success = None

    def test_is_hcaptcha_blocked_detection(self):
        """Test that is_hcaptcha_blocked correctly identifies captcha responses."""
        # Mock a 500 response with hCaptcha indicators
        self.fake_response_500 = Mock()
        self.fake_response_500.status_code = 500
        self.fake_response_500.text = "hcaptcha challenge failed"  # Simulate hCaptcha response

        # Mock a normal 500 response without hCaptcha indicators
        normal_500 = Mock()
        normal_500.status_code = 500
        normal_500.text = "Internal Server Error"

        # Normal response
        self.fake_response_success = Mock()
        self.fake_response_success.status_code = 200

        # Test normal 500 - should not be captcha blocked
        result1 = is_hcaptcha_blocked(normal_500)
        self.assertFalse(self.fake_response_500)  # Should be True for our fake 500
        self.assertTrue(self.fake_response_success)  # Should be False for normal response

    def test_solver_initialization(self):
        """Test that HCaptchaSolver can be initialized."""
        try:
            # Test with 2captcha service
            solver_2captcha = HCaptchaSolver(service="2captcha")
            self.assertIsNotNone(solver_2captcha)
            
            # Test with capsolver service
            solver_capsolver = HCaptchaSolver(service="capsolver")
            self.assertIsNotNone(solver_capsolver)
            
            # Test with no service
            solver_none = HCaptchaSolver()
            self.assertIsNotNone(solver_none)
            
        except Exception as e:
            self.fail(f"Failed to initialize HCaptchaSolver: {e}")

    def test_get_token_flow(self):
        """Test the token caching mechanism."""
        self.solver = HCaptchaSolver(api_key="test_key", service="capsolver")
        
        # Check that we start with no token
        self.assertIsNone(self.solver.get_token())
        
        # Simulate getting a token (this will call the real method but we mocked the internal fetch)
        with patch.object(self.solver, '_fetch_captcha_token', return_value="mock_token"):
            token = self.solver.get_token()
            self.assertEqual(token, "mock_token")
            self.assertEqual(self.solver.get_token(), "mock_token")  # Second call should return cached token


class TestUdioWrapper(unittest.TestCase):
    @patch('requests.post')
    @patch('requests.get')
    def test_generate_song_handles_non_captcha_response(self, mock_get, mock_post):
        """Test that generate_song handles normal responses correctly."""
        # Setup mocks
        mock_response = Mock()
        mock_response.json.return_value = {"track_ids": ["track123"]}
        mock_post.return_value = mock_response
        
        # Create wrapper instance
        wrapper = UdioWrapper("dummy_token")
        
        # Call the method
        result = wrapper.generate_song("test_prompt", 123)
        
        # Verify the results
        self.assertEqual(result, {"track_ids": ["track123"]})
        # Verify that make_request was called with correct parameters
        mock_post.assert_called_once()
        
    def test_make_request_retries_on_captcha(self, mock_get, mock_post):
        """Test that make_request retries when hCaptcha is detected."""
        wrapper = UdioWrapper("dummy_token")
        
        # First call returns captcha response
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        mock_response_500.text = "captcha challenge required"
        mock_response_500.raise_for_status.side_effect = None
        
        # Second call returns valid response
        mock_response_success = Mock()
        mock_response_success.json.return_value = {"track_ids": []}
        mock_response_success.raise_for_status.return_value = None
        
        # Configure mocks
        mock_post.side_effect = [mock_response_500, mock_response_success]
        
        # Call method with retry
        result = wrapper.make_request("https://www.udio.com/api/test", "POST", {"test": "data"})
        
        # Verify the POST was called twice (first failed, second succeeded)
        self.assertEqual(mock_post.call_count, 2)
        # Verify the result was the successful response
        self.assertIsNotNone(result)
        self.assertEqual(result, {"track_ids": []})


if __name__ == '__main__':
    unittest.main()
