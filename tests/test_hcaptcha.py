from unittest.mock import Mock, patch
from udio_wrapper import UdioWrapper
from udio_wrapper.hcaptcha_solver import HCaptchaSolver

def test_hcaptcha_solver_import():
    """Test that HCaptchaSolver can be imported."""
    try:
        solver = HCaptchaSolver()
        assert solver is not None
    except ImportError:
        raise ImportError("HCaptchaSolver not found in udio_wrapper.hcaptcha_solver")
        
def test_is_hcaptcha_blocked_detection():
    """Test that is_hcaptcha_blocked correctly identifies captcha responses."""
    from udio_wrapper.hcaptcha_solver import is_hcaptcha_blocked
    
    # Mock a 500 response with hCaptcha indicators
    fake_response_500 = Mock()
    fake_response_500.status_code = 500
    fake_response_500.text = "hcaptcha challenge failed"  # Simulate hCaptcha response
    
    # Mock a normal 500 response without hCaptcha indicators
    normal_500 = Mock()
    normal_500.status_code = 500
    normal_500.text = "Internal Server Error"
    
    # Normal response
    success_response = Mock()
    success_response.status_code = 200
    
    # Test that our fake 500 response is considered captcha-blocked
    result = is_hcaptcha_blocked(fake_response_500)
    assert result is True, "hCaptcha 500 response should be considered as captcha-blocked"
    
    # Test normal 500 response - should not be considered as captcha blocked
    result = is_hcaptcha_blocked(normal_500)
    assert result is False, "Normal 500 response should not be considered as captcha-blocked"
    
    # Test successful response - should not be captcha blocked
    success_response = Mock()
    success_response.status_code = 200
    result = is_hcaptcha_blocked(success_response)
    assert result is False, "Successful response should not be considered as captcha-blocked"

def test_solver_initialization():
    """Test that HCaptchaSolver can be initialized."""
    # Test with 2captcha service
    solver_2captcha = HCaptchaSolver(service="2captcha")
    assert solver_2captcha is not None
    
    # Test with capsolver service
    solver_capsolver = HCaptchaSolver(service="capsolver")
    assert solver_capsolver is not None
    
    # Test with no service (should work too)
    solver_none = HCaptchaSolver()
    assert solver_none is not None

def test_get_token_flow():
    """Test the token caching mechanism."""
    solver = HCaptchaSolver(api_key="test_key", service="capsolver")
    
    # Initially no token
    assert solver.get_token() is None
    
    # Mock the token fetch to return a test token
    with patch.object(solver, '_fetch_captcha_token', return_value="mock_token") as mock_fetch:
        token = solver.get_token()
        assert token == "mock_token"
        # Should have fetched the token once
        mock_fetch.assert_called_once()
        # Second call should return cached token
        token2 = solver.get_token()
        assert token2 == "mock_token"
        mock_fetch.assert_not_called()  # No additional fetch should occur
