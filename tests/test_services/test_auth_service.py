import pytest
from app.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token


def test_hash_and_verify_password():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert verify_password("mypassword", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    token = create_access_token(user_id=42, secret_key="test-secret")
    payload = decode_access_token(token, secret_key="test-secret")
    assert payload["sub"] == 42


def test_decode_invalid_token():
    payload = decode_access_token("invalid-token", secret_key="test-secret")
    assert payload is None
