from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import bcrypt
import jwt
from config import settings
from typing import Optional
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, Depends
from database.models import User

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
        expire = datetime.utcnow() + timedelta(minutes=settings.EXPIRED_TIME)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def check_auth(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Sign in first", headers={"Location": "/"})

    return True

def get_current_user(request: Request,
                     db: SessionLocal = Depends(get_db)):
    if request.cookies.get("access_token"):
        current_user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
        return current_user.id
    else:
        return None
