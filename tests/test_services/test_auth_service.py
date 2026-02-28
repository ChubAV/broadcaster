import pytest
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    create_verification_token,
    decode_verification_token,
)


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


def test_create_and_decode_verification_token():
    token = create_verification_token(
        email="user@test.com", secret_key="test-secret"
    )
    payload = decode_verification_token(token, secret_key="test-secret")
    assert payload is not None
    assert payload["email"] == "user@test.com"
    assert payload["verified"] is False


def test_create_and_decode_verified_token():
    token = create_verification_token(
        email="user@test.com", secret_key="test-secret", verified=True
    )
    payload = decode_verification_token(token, secret_key="test-secret")
    assert payload is not None
    assert payload["email"] == "user@test.com"
    assert payload["verified"] is True


def test_decode_verification_token_invalid():
    payload = decode_verification_token("bad-token", secret_key="test-secret")
    assert payload is None


def test_create_password_reset_token():
    token = create_verification_token("user@test.com", "secret", purpose="password_reset")
    payload = decode_verification_token(token, "secret")
    assert payload is not None
    assert payload["email"] == "user@test.com"
    assert payload["purpose"] == "password_reset"
    assert payload["verified"] is False


def test_decode_password_reset_token_verified():
    token = create_verification_token("user@test.com", "secret", purpose="password_reset", verified=True)
    payload = decode_verification_token(token, "secret")
    assert payload is not None
    assert payload["verified"] is True
    assert payload["purpose"] == "password_reset"


def test_registration_token_still_works():
    token = create_verification_token("user@test.com", "secret")
    payload = decode_verification_token(token, "secret")
    assert payload is not None
    assert payload["purpose"] == "email_verification"
