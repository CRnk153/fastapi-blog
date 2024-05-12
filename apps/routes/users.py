from apps.dependencies import get_db, SessionLocal, get_comments, hash_password
from apps.schemas import UserProfileEdit, UserPasswordChange

from database.models import User, Post, Followers, Like
from . import router_auth, router_non_auth
from config import settings

from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from sqlalchemy import func

@router_non_auth.get('/users/{user_id:int}')
def user_get(user_id,
             db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="No such user")
    user_info = {
        "username": user.username,
        "last_seen": str(user.last_seen),
        "followers": db.query(func.count(Followers.follower_id)).filter(Followers.followed_id == user.id).scalar(),
        "following": db.query(func.count(Followers.followed_id)).filter(Followers.follower_id == user.id).scalar(),
        "posts": db.query(func.count(Post.id)).filter(Post.user_id == user.id).filter(Post.type == 1).scalar()
    }
    return JSONResponse(content=user_info)

@router_non_auth.get('/users/{user_id:int}/posts/{page:int}')
def user_posts_get(page: int,
                   user_id,
                   db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return HTTPException(status_code=400, detail="No such user")
    posts = db.query(Post). \
        filter(Post.user_id == user.id). \
        filter(Post.hidden == bool(0)). \
        filter(Post.type == 1). \
        offset((page - 1) * settings.POSTS_PER_PAGE). \
        limit(settings.POSTS_PER_PAGE).all()
    if not posts:
        return HTTPException(status_code=400, detail="No such page")
    posts_json = [{'id': post.id,
                   'title': post.title,
                   'content': post.content,
                   'user': post.user.username,
                   'date': str(post.created_at),
                   'likes': db.query(func.count(Like.post_id)).filter(Like.post_id == post.id).scalar(),
                   'comments': get_comments(post.id, db)}
                  for post in posts]
    db.close()
    return JSONResponse(content=posts_json)

@router_auth.get('/users/{user_to_follow_id:int}/follow')
def follow_get(request: Request,
               user_to_follow_id: int,
               db: SessionLocal = Depends(get_db)
               ):

    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    user_to_follow = db.query(User).filter(User.id == user_to_follow_id).first()
    if not user_to_follow:
        raise HTTPException(status_code=400, detail="No such user")
    if user == user_to_follow:
        raise HTTPException(status_code=400, detail="You can't follow yourself")
    if not user.follow(user_to_follow, db):
        raise HTTPException(status_code=400, detail="You already following this user")
    db.commit()
    return JSONResponse(status_code=200, content={"message": "Followed successfully"})

@router_auth.get('/users/{user_to_unfollow_id:int}/unfollow')
def unfollow_get(request: Request,
                 user_to_unfollow_id: int,
                 db: SessionLocal = Depends(get_db)):

    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    user_to_unfollow = db.query(User).filter(User.id == user_to_unfollow_id).first()
    if not user_to_unfollow:
        raise HTTPException(status_code=400, detail="No such user")
    if user == user_to_unfollow:
        raise HTTPException(status_code=400, detail="You can't unfollow yourself")
    if not user.unfollow(user_to_unfollow, db):
        raise HTTPException(status_code=400, detail="You aren't following this user")
    db.commit()
    return JSONResponse(status_code=200, content={"message": "Unfollowed successfully"})

@router_auth.post('/users/edit-profile')
def edit_profile_post(request: Request,
                      user_body: UserProfileEdit,
                      db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    if db.query(User).filter(User.username == user_body.username).first():
        raise HTTPException(status_code=400, detail="Username is already used")
    if db.query(User).filter(User.email == user_body.email).first():
        raise HTTPException(status_code=400, detail="Email is already used")
    user.username = user_body.username
    user.email = user_body.email
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=settings.EXPIRED_TIME)
    )

    server_response = JSONResponse(status_code=200, content={"message": "Successful"})
    server_response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True)

    return server_response

@router_auth.post('/users/change-password')
def change_password_post(request: Request,
                         user_body: UserPasswordChange,
                         db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    user.hashed_password = hash_password(user_body.password)
    db.commit()
    db.refresh(user)

    return JSONResponse(status_code=200, content={"message": "Successful"})
