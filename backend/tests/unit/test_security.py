"""Unit tests for security utilities (password hashing, JWT tokens)."""
import pytest
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_and_verify_valid_password(self):
        """Test: hashed password can be verified with correct plaintext."""
        pwd = "MySecureP@ss123"
        hashed = hash_password(pwd)
        assert hashed is not None
        assert hashed != pwd  # hash should not equal plaintext
        assert verify_password(pwd, hashed) is True

    def test_verify_wrong_password(self):
        """Test: wrong password fails verification."""
        pwd = "MySecureP@ss123"
        hashed = hash_password(pwd)
        assert verify_password("WrongPassword", hashed) is False

    def test_hash_is_deterministic(self):
        """Test: hashing same password twice produces different hashes (salt)."""
        pwd = "SameP@ss123"
        h1 = hash_password(pwd)
        h2 = hash_password(pwd)
        assert h1 != h2  # Different due to salt
        assert verify_password(pwd, h1) is True
        assert verify_password(pwd, h2) is True

    def test_empty_password_hash(self):
        """Test: empty password can be hashed."""
        hashed = hash_password("")
        assert hashed is not None

    def test_long_password(self):
        """Test: very long password can be hashed."""
        long_pwd = "A" * 100
        hashed = hash_password(long_pwd)
        assert hashed is not None
        assert verify_password(long_pwd, hashed) is True


class TestJWTToken:
    """Test JWT token creation and decoding."""

    def test_create_and_decode_access_token(self):
        """Test: create and decode a valid access token."""
        token = create_access_token(
            subject="user-123",
            email="user@example.com",
            role="ADMIN",
        )
        assert token is not None
        assert isinstance(token, str)

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["email"] == "user@example.com"
        assert payload["role"] == "ADMIN"

    def test_create_and_decode_refresh_token(self):
        """Test: create and decode a valid refresh token."""
        token = create_refresh_token(subject="user-123")
        assert token is not None
        assert isinstance(token, str)

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_access_token_has_no_type(self):
        """Test: access token does not have a 'type' claim (or defaults differently)."""
        token = create_access_token(
            subject="user-123",
            email="user@example.com",
            role="ADMIN",
        )
        payload = decode_token(token)
        # Access tokens should not have type=refresh
        assert payload.get("type") != "refresh"

    def test_decode_invalid_token(self):
        """Test: decoding a malformed token returns None."""
        payload = decode_token("invalid-token-string")
        assert payload is None

    def test_decode_empty_token(self):
        """Test: decoding an empty string returns None."""
        payload = decode_token("")
        assert payload is None

    def test_access_token_with_custom_expiry(self):
        """Test: access token with custom expiry delta (via settings)."""
        token = create_access_token(
            subject="user-123",
            email="user@example.com",
            role="ADMIN",
        )
        assert token is not None
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["email"] == "user@example.com"
        # exp should be in the payload
        assert "exp" in payload

    def test_access_token_with_token_type(self):
        """Test: access token with custom token_type (e.g. password_reset)."""
        token = create_access_token(
            subject="user-123",
            email="user@example.com",
            role="ADMIN_RESET",
            token_type="password_reset",
        )
        assert token is not None
        payload = decode_token(token)
        assert payload["type"] == "password_reset"
        assert payload["role"] == "ADMIN_RESET"

    def test_refresh_token_decodes_correctly(self):
        """Test: decode_token correctly parses refresh token contents."""
        token = create_refresh_token(subject="candidate-456")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "candidate-456"
        assert payload["type"] == "refresh"
        # Should have an expiry
        assert "exp" in payload
