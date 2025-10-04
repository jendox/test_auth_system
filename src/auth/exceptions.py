class AuthenticationError(Exception):
    """Exception raised when user authentication fails due to invalid credentials or inactive account."""


class InsufficientPermissions(Exception):
    """Exception raised when a user lacks required permissions to perform an action."""


class UserSessionNotFound(Exception):
    """Exception raised when a user session cannot be found or is invalid."""


class TokenNotFound(Exception):
    """Exception raised when a token cannot be found or is invalid."""


class PermissionNotFound(Exception):
    """Exception raised when a specified permission cannot be found in the system."""
