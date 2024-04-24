from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import bcrypt
import jwt
from config import SECRET_KEY, ALGORITHM, EXPIRED_TIME
from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends

engine = create_engine("postgresql://postgres:@localhost/fastapi")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def check_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = None
                        ):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(EXPIRED_TIME)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
