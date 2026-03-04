class SessionExpiredException(Exception):
    """Raised when the refresh token has expired."""

    pass


class AccessForbiddenException(Exception):
    """Raised when the user does not have chatbot access."""

    pass
