from config import settings
from . import router_non_auth, router_auth
from apps.schemas import UserCreate
from apps.dependencies import SessionLocal, get_db, hash_password, create_access_token, check_password
from database.models import User

from fastapi import Response, Depends, HTTPException, Request

from datetime import timedelta

@router_non_auth.post('/auth/register')
def auth_register_post(response: Response,
                       user: UserCreate,
                       db: SessionLocal = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(settings.EXPIRED_TIME)
    )

    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True)

    return "Signed up and logged in successfully"


@router_non_auth.post('/auth/login')
def auth_login_post(response: Response,
                    user: UserCreate,
                    db: SessionLocal = Depends(get_db)):
    if not db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username does not exist")
    if not db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email does not exist")
    if not check_password(user.password, db.query(User).filter(User.username == user.username).first().hashed_password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(settings.EXPIRED_TIME)
    )

    server_response = response
    server_response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True)

    return server_response

@router_auth.get('/auth/logout')
def auth_logout_get(request: Request,
                    response: Response):
    request.state.user = None
    server_response = response
    server_response.set_cookie(key="access_token", value="", httponly=True, secure=True)
    return server_response
