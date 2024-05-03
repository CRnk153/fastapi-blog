from apps.dependencies import get_db, SessionLocal

from database.models import User, Post, Followers
from . import router_auth, router_non_auth
from config import settings

from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from sqlalchemy import func

@router_non_auth.get('/users/{user_id:int}')
def user_get(user_id,
             db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    user_info = {
        "username": user.username,
        "last_seen": str(user.last_seen),
        "followers": db.query(func.count(Followers.follower_id)).filter(Followers.followed_id == user.id).scalar(),
        "following": db.query(func.count(Followers.followed_id)).filter(Followers.follower_id == user.id).scalar(),
        "posts": db.query(func.count(Post.id)).filter(Post.user_id == user.id).scalar()
    }
    print(user.following)
    return JSONResponse(content={"data": user_info})

@router_non_auth.get('/users/{user_id:int}/posts/{page:int}')
def user_posts_get(page: int,
                   user_id,
                   db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    posts = db.query(Post).filter(Post.user_id == user.id).offset((page - 1) * settings.POSTS_PER_PAGE).limit(settings.POSTS_PER_PAGE).all()
    if not posts:
        return HTTPException(status_code=400, detail="Missing information")
    posts_json = [{'id': post.id,
                   'title': post.title,
                   'content': post.content,
                   'user': post.user.username,
                   'date': str(post.created_at)}
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
    if user == user_to_unfollow:
        raise HTTPException(status_code=400, detail="You can't unfollow yourself")

    if not user.unfollow(user_to_unfollow, db):
        raise HTTPException(status_code=400, detail="You aren't following this user")
    db.commit()
    return JSONResponse(status_code=200, content={"message": "Unfollowed successfully"})
