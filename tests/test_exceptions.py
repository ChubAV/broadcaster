import pytest
from app.exceptions import NotFoundError, ForbiddenError, BillingLimitError


def test_not_found_error_message():
    err = NotFoundError("Ad", 42)
    assert str(err) == "Ad not found"
    assert err.resource == "Ad"
    assert err.resource_id == 42


def test_forbidden_error_message():
    err = ForbiddenError("Not allowed")
    assert str(err) == "Not allowed"


def test_billing_limit_error_message():
    err = BillingLimitError("Ad limit reached (3 on free plan)")
    assert str(err) == "Ad limit reached (3 on free plan)"
