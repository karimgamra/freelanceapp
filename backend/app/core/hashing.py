from passlib.context import CryptContext

my_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    return my_context.hash(password)


def verify_password(plain: str, hash: str) -> bool:
    return my_context.verify(plain, hash)
