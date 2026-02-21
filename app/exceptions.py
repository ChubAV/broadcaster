class AppError(Exception):
    """Base application error."""


class NotFoundError(AppError):
    """Resource not found or not accessible."""

    def __init__(self, resource: str, resource_id: int | None = None):
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} not found")


class ForbiddenError(AppError):
    """Action not permitted."""


class BillingLimitError(AppError):
    """Plan limit exceeded."""


class MessengerConnectionError(AppError):
    """Messenger connection failed."""
