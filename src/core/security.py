from passlib.context import CryptContext

__all__ = (
    "PasswordHasher",
    "get_argon2_password_hasher",
    "InvalidCredentials",
)


class InvalidCredentials(Exception):
    """Exception raised when password verification fails."""


class PasswordHasher:
    """
    Password hashing and verification utility.

    Uses passlib with configurable hashing schemes for secure password management.
    """

    def __init__(self, schemes: list[str]):
        self.context = CryptContext(schemes=schemes, deprecated="auto")

    def hash_password(self, plain_password: str) -> str:
        """
        Hash a plain text password using configured algorithm.

        Args:
            plain_password: The password to hash

        Returns:
            Hashed password string
        """
        return self.context.hash(plain_password)

    def verify_password(self, plain_password: str, hashed_password: str):
        """
        Verify a plain password against its hashed version.

        Args:
            plain_password: Password to verify
            hashed_password: Stored hash to compare against

        Raises:
            InvalidCredentials: If password doesn't match the hash
        """
        if not self.context.verify(plain_password, hashed_password):
            raise InvalidCredentials("Invalid password")


def get_argon2_password_hasher() -> PasswordHasher:
    """
    Factory function to create PasswordHasher instance with Argon2.

    Returns:
        PasswordHasher configured with Argon2 algorithm
    """
    return PasswordHasher(["argon2"])
