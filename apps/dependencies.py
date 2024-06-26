from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy import create_engine, func
import bcrypt
import jwt
from config import settings
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, Depends
from database.models import User, Post, Like

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

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.EXPIRED_TIME)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def check_auth(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Sign in first", headers={"Location": "/"})

    return True

def check_admin(request: Request,
                db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    if user.role_id != 2:
        raise HTTPException(status_code=401, detail="This is protected route", headers={"Location": "/"})

def get_current_user(request: Request):
    if request.cookies.get("access_token"):
        return request.state.user.get("sub")
    else:
        return None

def get_comments(post_id, db):
    parent_comment = aliased(Post)
    child_comment = aliased(Post)

    comments = db.query(child_comment). \
        join(parent_comment, parent_comment.id == child_comment.refer_to). \
        filter(parent_comment.id == post_id). \
        filter(child_comment.hidden == bool(0)). \
        with_entities(child_comment)

    comment_list = []
    for comment in comments:
        comment_data = {
            'id': comment.id,
            'title': comment.title,
            'content': comment.content,
            'user': comment.user.username,
            'date': str(comment.created_at),
            'likes': db.query(func.count(Like.post_id)).filter(Like.post_id == comment.id).scalar(),
            'answers': get_comments(comment.id, db)
        }
        comment_list.append(comment_data)

    return comment_list
