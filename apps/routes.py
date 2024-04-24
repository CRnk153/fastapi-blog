from fastapi import Depends, HTTPException, Response, Request
from fastapi.routing import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from apps.dependencies import get_db, SessionLocal, hash_password, check_password, create_access_token
from apps.schemas import UserCreate, PostCreate
from database.models import User, Post
from datetime import timedelta
import jwt
from config import SECRET_KEY, EXPIRED_TIME, POSTS_PER_PAGE, ALGORITHM
from apps import app

router = APIRouter()


async def verify_token(request: Request, call_next):
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            request.state.user = payload
        except jwt.DecodeError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    response = await call_next(request)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(verify_token)


@router.get('/')
def home_get(request: Request):
    if hasattr(request.state, "user"):
        return JSONResponse(content=f'Hello, {request.state.user.get("sub")}!')
    return "Hello world"


@router.post('/auth/register')
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
        data={"sub": user.username}, expires_delta=timedelta(EXPIRED_TIME)
    )

    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True)

    return "Signed up and logged in successfully"


@router.post('/auth/login')
def auth_login_post(user: UserCreate,
                    db: SessionLocal = Depends(get_db)
                    ):
    if not db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username does not exist")
    if not db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email does not exist")
    if not check_password(user.password, db.query(User).filter(User.username == user.username).first().hashed_password):
        raise HTTPException(status_code=400, detail="Password is incorrect")
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(EXPIRED_TIME)
    )

    response = RedirectResponse('/')
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True)

    return "Logged in successfully"


@router.get('/auth/logout')
def auth_logout_get(request: Request):
    request.state.user = None
    response = RedirectResponse('/')
    response.set_cookie(key="access_token", value="", httponly=True, secure=True)
    return "Logged out successfully"


@router.post('/posts/create')
def messages_post(request: Request,
                  post: PostCreate,
                  db: SessionLocal = Depends(get_db)):
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=401, detail="Sign in first")
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    db_post = Post(
        title=post.title,
        content=post.content,
        user_id=user.id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)


@router.get('/posts/{post_id:int}')
def message_get(post_id: int,
                db: SessionLocal = Depends(get_db)):
    post = db.query(Post).filter(id == post_id).first()
    if not post:
        raise HTTPException(status_code=400, detail="This post does not exist")
    post_json = {
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'user': post.username,
        'date': str(post.created_at)}
    db.close()
    return post_json


@router.get('/posts/all/{page:int}')
def messages_get(page: int,
                 db: SessionLocal = Depends(get_db)):
    posts = db.query(Post).offset((page - 1) * POSTS_PER_PAGE).limit(POSTS_PER_PAGE).all()
    posts_json = [{'id': post.id,
                   'title': post.title,
                   'content': post.content,
                   'user': post.username,
                   'date': str(post.created_at)}
                  for post in posts]
    db.close()
    return JSONResponse(content=posts_json)


@router.get('/users/{user_to_follow_id:int}/follow')
def follow_get(request: Request,
               user_to_follow_id: int,
               db: SessionLocal = Depends(get_db)
               ):
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=401, detail="Sign in first")
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    user_to_follow = db.query(User).filter(User.id == user_to_follow_id).first()

    user.follow(user_to_follow)
    db.commit()
