from passlib.context import CryptContext


class InvalidCredentials(Exception): ...


class PasswordHasher:
    def __init__(self, schemes: list[str]):
        self.context = CryptContext(schemes=schemes, deprecated="auto")

    def hash_password(self, plain_password: str) -> str:
        return self.context.hash(plain_password)

    def verify_password(self, plain_password: str, hashed_password: str):
        if not self.context.verify(plain_password, hashed_password):
            raise InvalidCredentials("Invalid password")


def get_password_hasher() -> PasswordHasher:
    return PasswordHasher(["argon2"])
