from . import router_auth, router_non_auth
from apps.schemas import PostCreate
from apps.dependencies import SessionLocal, get_db, get_comments
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
    if post.type == 2:
        post_json['comment_for'] = post.refer_to
        post_json['answers'] = get_comments(post_id, db)
    elif post.type == 3:
        post_json['answer_for'] = post.refer_to
        post_json['answers'] = get_comments(post_id, db)
    else:
        post_json['comments'] = get_comments(post_id, db)
    db.close()
    return JSONResponse(content={"data": post_json})


@router_non_auth.get('/posts/all/{page:int}')
def messages_get(page: int,
                 db: SessionLocal = Depends(get_db)):
    posts = db.query(Post). \
        filter(Post.hidden == bool(0)). \
        filter(Post.type == 1). \
        offset((page - 1) * settings.POSTS_PER_PAGE). \
        limit(settings.POSTS_PER_PAGE).all()
    if not posts:
        raise HTTPException(status_code=400, detail="No such page")
    posts_json = [{'id': post.id,
                   'title': post.title,
                   'content': post.content,
                   'user': post.user.username,
                   'date': str(post.created_at),
                   'likes': db.query(func.count(Like.post_id)).filter(Like.post_id == post.id).scalar(),
                   'comments': get_comments(post.id, db)}
                  for post in posts]
    db.close()
    return JSONResponse(content={"data": posts_json})

@router_auth.get('/posts/followed/{page:int}')
def followed_posts_get(request: Request,
                       page: int,
                       db: SessionLocal = Depends(get_db)):

    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    followed_users = db.query(Followers).filter(Followers.follower_id == user.id).all()
    posts = db.query(Post). \
        filter(Post.user_id.in_([follow.followed_id for follow in followed_users])). \
        filter(Post.hidden == bool(0)). \
        filter(Post.type == 1). \
        offset((page - 1) * settings.POSTS_PER_PAGE). \
        limit(settings.POSTS_PER_PAGE).all()
    if not posts:
        raise HTTPException(status_code=400, detail="No such page")
    posts_json = [{'id': post.id,
                   'title': post.title,
                   'content': post.content,
                   'user': post.user.username,
                   'date': str(post.created_at),
                   'likes': db.query(func.count(Like.post_id)).filter(Like.post_id == post.id).scalar(),
                   'comments': get_comments(post.id, db)}
                   for post in posts]
    return JSONResponse(content={"data": posts_json})

@router_auth.get('/posts/{post_id:int}/like')
def post_like_get(request: Request,
                  post_id: int,
                  db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=400, detail="This post does not exist")
    if not user.like(post, db):
        raise HTTPException(status_code=400, detail="This post is already liked")
    if post.user_id == user.id:
        raise HTTPException(status_code=400, detail="You can't like yourself")
    db.commit()
    db.close()
    return JSONResponse(content={"message": "Successful"})

@router_auth.get('/posts/{post_id:int}/remove-like')
def post_remove_like_get(request: Request,
                         post_id: int,
                         db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=400, detail="This post does not exist")
    if not user.remove_like(post, db):
        raise HTTPException(status_code=400, detail="This post isn't liked")
    db.commit()
    db.close()
    return JSONResponse(content={"message": "Successful"})

@router_auth.post('/posts/{post_id}/comment')
def post_comment_post(request: Request,
                      comment: PostCreate,
                      post_id: int,
                      db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    post_to_comment = db.query(Post).filter(Post.id == post_id).first()
    if not post_to_comment:
        raise HTTPException(status_code=400, detail="No such post")
    if post_to_comment.type == 2 or post_to_comment.type == 3:
        raise HTTPException(status_code=400, detail="You can't comment comment or answer")
    db_post = Post(
        title=comment.title,
        content=comment.content,
        user_id=user.id,
        type=2,
        refer_to=post_id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return JSONResponse(status_code=200, content={"message": "Comment published"})

@router_auth.post('/posts/{post_id}/answer')
def post_answer_post(request: Request,
                     answer: PostCreate,
                     post_id: int,
                     db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    post_to_answer = db.query(Post).filter(Post.id == post_id).first()
    if not post_to_answer:
        raise HTTPException(status_code=400, detail="No such post")
    if post_to_answer.type == 1:
        raise HTTPException(status_code=400, detail="You can't answer to the post")
    db_post = Post(
        title=answer.title,
        content=answer.content,
        user_id=user.id,
        type=3,
        refer_to=post_id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return JSONResponse(status_code=200, content={"message": "Answer published"})
