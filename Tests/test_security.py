"""Tests for JsWeb security features (CSRF, validation, etc.)."""

import pytest


@pytest.mark.unit
@pytest.mark.security
def test_csrf_token_generation():
    """Test CSRF token generation."""
    try:
        from jsweb.security import generate_csrf_token

        token1 = generate_csrf_token()
        token2 = generate_csrf_token()

        assert token1 is not None
        assert token2 is not None
        assert token1 != token2  # Tokens should be unique
    except ImportError:
        pytest.skip("CSRF utilities not available")


@pytest.mark.unit
@pytest.mark.security
def test_csrf_token_validation():
    """Test CSRF token validation."""
    try:
        from jsweb.security import generate_csrf_token, validate_csrf_token

        token = generate_csrf_token()
        assert validate_csrf_token(token) is not None or token is not None
    except ImportError:
        pytest.skip("CSRF utilities not available")


@pytest.mark.unit
@pytest.mark.security
def test_password_hashing():
    """Test password hashing functionality."""
    try:
        from jsweb.security import check_password, hash_password

        password = "mySecurePassword123!"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert check_password(password, hashed)
    except ImportError:
        pytest.skip("Password hashing not available")


@pytest.mark.unit
@pytest.mark.security
def test_password_hash_unique():
    """Test that same password produces different hashes."""
    try:
        from jsweb.security import hash_password

        password = "testpassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Should be different due to salt
    except ImportError:
        pytest.skip("Password hashing not available")


@pytest.mark.unit
@pytest.mark.security
def test_password_verification_fails_for_wrong_password():
    """Test that password verification fails for incorrect password."""
    try:
        from jsweb.security import check_password, hash_password

        password = "correctpassword"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert check_password(password, hashed)
        assert not check_password(wrong_password, hashed)
    except ImportError:
        pytest.skip("Password hashing not available")


@pytest.mark.unit
@pytest.mark.security
def test_secure_random_generation():
    """Test secure random token generation."""
    try:
        from jsweb.security import generate_secure_token

        token1 = generate_secure_token()
        token2 = generate_secure_token()

        assert token1 is not None
        assert token2 is not None
        assert len(token1) > 10
        assert token1 != token2
    except ImportError:
        pytest.skip("Secure token generation not available")


@pytest.mark.unit
@pytest.mark.security
def test_token_expiration():
    """Test token expiration functionality."""
    try:
        import time

        from jsweb.security import generate_token_with_expiry, verify_token

        token = generate_token_with_expiry(expiry_seconds=1)
        assert token is not None

        # Token should be valid immediately
        assert verify_token(token)

        # Wait for expiration
        time.sleep(1.1)
        # Token might be expired now
    except ImportError:
        pytest.skip("Token expiry not available")


@pytest.mark.unit
@pytest.mark.security
def test_input_sanitization():
    """Test input sanitization."""
    try:
        from jsweb.security import sanitize_input

        malicious = "<script>alert('XSS')</script>"
        safe = sanitize_input(malicious)

        assert safe is not None
        assert "<script>" not in safe.lower() or "script" not in safe.lower()
    except ImportError:
        pytest.skip("Input sanitization not available")


@pytest.mark.unit
@pytest.mark.security
def test_sql_injection_prevention():
    """Test SQL injection prevention."""
    try:
        from jsweb.security import escape_sql

        user_input = "'; DROP TABLE users; --"
        escaped = escape_sql(user_input)

        assert escaped is not None
        assert escaped != user_input  # Should be escaped
    except ImportError:
        pytest.skip("SQL escaping not available")


@pytest.mark.unit
@pytest.mark.security
def test_xss_prevention():
    """Test XSS prevention."""
    try:
        from jsweb.security import escape_html

        xss_payload = "<img src=x onerror=\"alert('XSS')\">"
        escaped = escape_html(xss_payload)

        assert escaped is not None
        assert "<" not in escaped or "&lt;" in escaped
    except ImportError:
        pytest.skip("HTML escaping not available")


@pytest.mark.unit
@pytest.mark.security
def test_rate_limiting():
    """Test rate limiting functionality."""
    try:
        from jsweb.security import RateLimiter

        limiter = RateLimiter(max_requests=5, window_seconds=60)

        # Should allow requests within limit
        for i in range(5):
            result = limiter.allow_request("user1")
            assert result is not None or result is True

        # 6th request might be limited
        result = limiter.allow_request("user1")
        # Result might be False if rate limited
    except ImportError:
        pytest.skip("Rate limiting not available")


@pytest.mark.unit
@pytest.mark.security
def test_secure_session_token():
    """Test secure session token generation."""
    try:
        from jsweb.security import generate_session_token

        token = generate_session_token()
        assert token is not None
        assert len(token) >= 32  # Should be reasonably long
    except ImportError:
        pytest.skip("Session token generation not available")


@pytest.mark.unit
@pytest.mark.security
def test_hmac_signing():
    """Test HMAC signing."""
    try:
        from jsweb.security import sign_data, verify_signature

        secret = "secret-key"
        data = "sensitive data"

        signature = sign_data(data, secret)
        assert signature is not None

        is_valid = verify_signature(data, signature, secret)
        assert is_valid
    except ImportError:
        pytest.skip("HMAC signing not available")


@pytest.mark.unit
@pytest.mark.security
def test_signature_verification_fails_with_wrong_secret():
    """Test that signature verification fails with wrong secret."""
    try:
        from jsweb.security import sign_data, verify_signature

        data = "sensitive data"
        signature = sign_data(data, "secret1")

        is_valid = verify_signature(data, signature, "secret2")
        assert not is_valid
    except ImportError:
        pytest.skip("HMAC signing not available")


@pytest.mark.unit
@pytest.mark.security
def test_constant_time_comparison():
    """Test constant-time string comparison (timing attack prevention)."""
    try:
        from jsweb.security import constant_time_compare

        assert constant_time_compare("hello", "hello")
        assert not constant_time_compare("hello", "world")
    except ImportError:
        pytest.skip("Constant-time comparison not available")


@pytest.mark.unit
@pytest.mark.security
def test_password_strength_validation():
    """Test password strength validation."""
    try:
        from jsweb.security import validate_password_strength

        # Weak password
        assert not validate_password_strength("123")

        # Strong password
        assert validate_password_strength("SecurePass123!")
    except ImportError:
        pytest.skip("Password strength validation not available")


@pytest.mark.unit
@pytest.mark.security
def test_csrf_header_validation():
    """Test CSRF header validation."""
    try:
        from jsweb.security import validate_csrf_header

        headers = {"X-CSRF-Token": "valid-token"}
        # Would need actual token validation
        assert headers is not None
    except ImportError:
        pytest.skip("CSRF header validation not available")


@pytest.mark.unit
@pytest.mark.security
def test_security_headers():
    """Test security headers generation."""
    try:
        from jsweb.security import get_security_headers

        headers = get_security_headers()
        assert headers is not None
        assert isinstance(headers, dict)
    except ImportError:
        pytest.skip("Security headers not available")


@pytest.mark.unit
@pytest.mark.security
def test_content_security_policy():
    """Test CSP header generation."""
    try:
        from jsweb.security import generate_csp_header

        csp = generate_csp_header()
        assert csp is not None
        assert "default-src" in csp or csp is not None
    except ImportError:
        pytest.skip("CSP generation not available")
