import jwt
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from functools import wraps

SECRET_KEY = os.environ.get("SESSION_SECRET", "autosense-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

def generate_salt() -> str:
    return secrets.token_hex(16)

def hash_password(password: str, salt: str = None) -> str:
    if salt is None:
        salt = generate_salt()
    salted = salt + password
    hashed = hashlib.sha256(salted.encode()).hexdigest()
    return f"{salt}${hashed}"

def verify_password(password: str, stored_hash: str) -> bool:
    if '$' in stored_hash:
        salt, hashed = stored_hash.split('$', 1)
        return hash_password(password, salt) == stored_hash
    else:
        return hashlib.sha256(password.encode()).hexdigest() == stored_hash

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user_from_token(token: str):
    payload = decode_token(token)
    if payload is None:
        return None
    return payload
