import os
from passlib.context import CryptContext
import time
import jwt
from cryptography.fernet import Fernet

SECRET_KEY = os.getenv("SECRET_KEY", "dev_insecure_change_me")
ALGORITHM = os.getenv("JWT_ALGO", "HS256")
ACCESS_TOKEN_EXP = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 86400))


ENCRYPTION_KEY = os.getenv("FERNET_KEY", Fernet.generate_key().decode())
cipher_suite = Fernet(ENCRYPTION_KEY)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(passwd: str, pwd_hash: str) -> bool:
    return pwd_context.verify(passwd, pwd_hash)

def enc_netapp_password(password: str) -> str:
    if not password:
        return ""
    encryoted_bytes = cipher_suite.encrypt(password.encode("utf-8"))
    return encryoted_bytes.decode("utf-8")

def decrypt_netapp_password(enc_pass: str) -> str:
    if not enc_pass:
        return ""
    
    try:
        decrypt_pass = cipher_suite.decrypt(enc_pass.encode("utf-8"))
        return decrypt_pass.decode("utf-8")
    except Exception:
        raise ValueError("Could not decrypt password. Invalid Key?")

def create_token(data: dict):
    to_encode = data.copy()
    expire = int(time.time()) + ACCESS_TOKEN_EXP
    to_encode.update({"exp":expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
