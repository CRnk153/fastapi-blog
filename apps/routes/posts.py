from . import router_auth, router_non_auth
from apps.schemas import PostCreate
from apps.dependencies import SessionLocal, get_db
from database.models import User, Post, Like, Followers
from config import settings

from fastapi import Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from sqlalchemy import func

@router_auth.post('/posts/create')
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
    return JSONResponse(status_code=200, content={"message": "Post published"})

@router_auth.get('/posts/remove/{post_id:int}')
def message_delete_get(request: Request,
                       post_id: int,
                       db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=400, detail="This post does not exist")
    if post.user_id != user.id:
        raise HTTPException(status_code=400, detail="You do not own this post")
    post.hide()
    db.commit()

@router_non_auth.get('/posts/{post_id:int}')
def message_get(post_id: int,
                db: SessionLocal = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).filter(Post.hidden == bool(0)).first()
    if not post:
        raise HTTPException(status_code=400, detail="This post does not exist")
    post_json = {
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'user': post.user.username,
        'date': str(post.created_at),
        'likes': db.query(func.count(Like.post_id)).filter(Like.post_id == post.id).scalar()}
    db.close()
    return JSONResponse(content=post_json)


@router_non_auth.get('/posts/all/{page:int}')
def messages_get(page: int,
                 db: SessionLocal = Depends(get_db)):
    posts = db.query(Post).filter(Post.hidden == bool(0)).offset((page - 1) * settings.POSTS_PER_PAGE).limit(settings.POSTS_PER_PAGE).all()
    posts_json = [{'id': post.id,
                   'title': post.title,
                   'content': post.content,
                   'user': post.user.username,
                   'date': str(post.created_at)}
                  for post in posts]
    db.close()
    return JSONResponse(content={"data": posts_json})

@router_auth.get('/posts/followed/{page:int}')
def followed_posts_get(request: Request,
                       page: int,
                       db: SessionLocal = Depends(get_db)):

    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    followed_users = db.query(Followers).filter(Followers.follower_id == user.id).all()
    posts = db.query(Post).filter(Post.user_id.in_([follow.followed_id for follow in followed_users])).filter(Post.hidden == bool(0)).offset((page - 1) * settings.POSTS_PER_PAGE).limit(settings.POSTS_PER_PAGE).all()
    posts_json = [{'id': post.id,
                   'title': post.title,
                   'content': post.content,
                   'user': post.user.username,
                   'date': str(post.created_at)}

                  for post in posts]
    return JSONResponse(content=posts_json)

@router_auth.get('/posts/{post_id:int}/like')
def post_like_get(request: Request,
                  post_id: int,
                  db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    post = db.query(Post).filter(Post.id == post_id).first()
    if not user.like(post, db):
        raise HTTPException(status_code=400, detail="This post is already liked")
    db.commit()
    db.close()
    return JSONResponse(content={"message": "Successful"})

@router_auth.get('/posts/{post_id:int}/remove-like')
def post_remove_like_get(request: Request,
                         post_id: int,
                         db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    post = db.query(Post).filter(Post.id == post_id).first()
    if not user.remove_like(post, db):
        raise HTTPException(status_code=400, detail="This post isn't liked")
    db.commit()
    db.close()
    return JSONResponse(content={"message": "Successful"})
