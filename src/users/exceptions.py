class UserAlreadyExists(Exception):
    """Exception raised when attempting to create a user with an existing email."""


class UserNotFound(Exception):
    """Exception raised when a user cannot be found."""


class UserAlreadyActivated(Exception):
    """Exception raised when attempting to activate an already active user."""


class AdminDeletion(Exception):
    """Exception raised when attempting to deactivate an admin user."""


class UserRoleNotFound(Exception):
    """Exception raised when a user role cannot be found."""
