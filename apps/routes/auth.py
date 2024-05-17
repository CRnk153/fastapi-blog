from starlette.responses import JSONResponse

from . import guest_router, secure_router
from apps.schemas import UserCreate
from apps.dependencies import SessionLocal, get_db, hash_password, create_access_token, check_password
from database.models import User

from fastapi import Depends, HTTPException, Request


@guest_router.post('/auth/register')
def auth_register_post(user: UserCreate,
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
        data={"sub": user.username}
    )

    server_response = JSONResponse(status_code=200, content={"message": "Successful"})
    server_response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True)

    return server_response


@guest_router.post('/auth/login')
def auth_login_post(user: UserCreate,
                    db: SessionLocal = Depends(get_db)):
    if not db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username does not exist")
    if not db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email does not exist")
    if not check_password(user.password, db.query(User).filter(User.username == user.username).first().hashed_password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    access_token = create_access_token(
        data={"sub": user.username}
    )

    server_response = JSONResponse(status_code=200, content={"message": "Successful"})
    server_response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True)

    return server_response

@secure_router.get('/auth/logout')
def auth_logout_get(request: Request):
    request.state.user = None
    server_response = JSONResponse(status_code=200, content={"message": "Successful"})
    server_response.set_cookie(key="access_token", value="", httponly=True, secure=True)
    return server_response
