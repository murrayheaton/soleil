"""
Authentication module exceptions.

Custom exceptions for authentication, authorization, and token errors.
"""


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class AuthorizationError(Exception):
    """Custom exception for authorization errors."""
    pass


class TokenError(Exception):
    """Custom exception for token-related errors."""
    pass