from fastapi import Depends, HTTPException, Response, Request
from fastapi.routing import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apps.dependencies import get_db, SessionLocal, hash_password, check_password, create_access_token, check_auth, get_current_user
from apps.schemas import UserCreate, PostCreate
from database.models import User, Post, Followers
from datetime import timedelta
import jwt
from config import settings
from apps import app
from sqlalchemy import func


non_auth_router = APIRouter()
auth_router = APIRouter(dependencies=[Depends(check_auth)])

async def verify_token(request: Request, call_next):
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            request.state.user = payload
        except jwt.DecodeError:
            request.state.user = None
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

@non_auth_router.get('/')
def home_get(request: Request,
             db: SessionLocal = Depends(get_db)):
    return JSONResponse(status_code=200, content={"message": "Hello world!",
                                                  "user": get_current_user(request, db).username})

@non_auth_router.post('/auth/register')
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


@non_auth_router.post('/auth/login')
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

@auth_router.get('/auth/logout')
def auth_logout_get(request: Request,
                    response: Response):
    request.state.user = None
    server_response = response
    server_response.set_cookie(key="access_token", value="", httponly=True, secure=True)
    return server_response

@non_auth_router.get('/users/{user_id:int}')
def user_get(user_id,
             request: Request,
             db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    user_info = {
        "username": user.username,
        "last_seen": user.last_seen,
        "followers": db.query(func.count(Followers.follower_id)).filter(Followers.followed_id == user.id).scalar(),
        "following": db.query(func.count(Followers.followed_id)).filter(Followers.follower_id == user.id).scalar(),
        "posts": db.query(func.count(Post.id)).filter(Post.user_id == user.id).scalar()
    }
    print(user.following)
    return JSONResponse(content={"data": user_info,
                                 "user": get_current_user(request, db).username})

@auth_router.post('/posts/create')
def messages_post(request: Request,
                  post: PostCreate,
                  db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    db_post = Post(
        title=post.title,
        content=post.content,
        user_id=user.id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return JSONResponse(status_code=200, content={"Post published"})

@non_auth_router.get('/posts/{post_id:int}')
def message_get(request: Request,
                post_id: int,
                db: SessionLocal = Depends(get_db)):
    raw_path = request.url.path
    print(raw_path)
    post = db.query(Post).filter(id == post_id).first()
    if not post:
        raise HTTPException(status_code=400, detail="This post does not exist")
    post_json = {
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'user': post.username.username,
        'date': str(post.created_at)}
    db.close()
    return JSONResponse(content=post_json)


@non_auth_router.get('/posts/all/{page:int}')
def messages_get(page: int,
                 request: Request,
                 db: SessionLocal = Depends(get_db)):
    posts = db.query(Post).offset((page - 1) * settings.POSTS_PER_PAGE).limit(settings.POSTS_PER_PAGE).all()
    posts_json = [{'id': post.id,
                   'title': post.title,
                   'content': post.content,
                   'user': post.username.username,
                   'date': str(post.created_at)}
                  for post in posts]
    db.close()
    return JSONResponse(content={"data": posts_json,
                                 "user": get_current_user(request, db)})

@auth_router.get('/users/{user_to_follow_id:int}/follow')
def follow_get(request: Request,
               user_to_follow_id: int,
               db: SessionLocal = Depends(get_db)
               ):

    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    user_to_follow = db.query(User).filter(User.id == user_to_follow_id).first()
    if user == user_to_follow:
        raise HTTPException(status_code=400, detail="You can't follow yourself")
    if user_to_follow in user.following:
        raise HTTPException(status_code=400, detail="Already followed")

    user.follow(user_to_follow)
    db.commit()
    return JSONResponse(status_code=200, content={"message": "Followed successfully"})

@auth_router.get('/users/{user_to_unfollow_id:int}/unfollow')
def unfollow_get(request: Request,
                 user_to_unfollow_id: int,
                 db: SessionLocal = Depends(get_db)):

    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    user_to_unfollow = db.query(User).filter(User.id == user_to_unfollow_id).first()
    if user == user_to_unfollow:
        raise HTTPException(status_code=400, detail="You can't unfollow yourself")
    if user_to_unfollow not in user.following:
        raise HTTPException(status_code=400, detail="You're not following this user")

    user.unfollow(user_to_unfollow)
    db.commit()
    return JSONResponse(status_code=200, content={"message": "Unfollowed successfully"})

@auth_router.get('/posts/followed/{page:int}')
def followed_posts_get(request: Request,
                       page: int,
                       db: SessionLocal = Depends(get_db)):

    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    posts = db.query(Post).filter(Post.user_id.in_(user.following)).offset((page - 1) * settings.POSTS_PER_PAGE).limit(settings.POSTS_PER_PAGE).all()
    posts_json = [{'id': post.id,
                   'title': post.title,
                   'content': post.content,
                   'user': post.username.username,
                   'date': str(post.created_at)}
                  for post in posts]
    return JSONResponse(content=posts_json)
