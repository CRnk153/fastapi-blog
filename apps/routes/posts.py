from apps import posts_logger
from . import secure_router, guest_router
from apps.schemas import PostCreate
from apps.dependencies import SessionLocal, get_db, get_comments
from database.models import User, Post, Like, Followers
from config import settings

from fastapi import Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from sqlalchemy import func


@secure_router.post('/posts/create')
def messages_post(request: Request,
                  post: PostCreate,
                  db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    posts_logger.info(
        f"Post adding attempt by user: user={user.username}")
    db_post = Post(
        title=post.title,
        content=post.content,
        user_id=user.id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    posts_logger.info(
        f"Post added successfully by user: user={user.username}, post_id={db_post.id}")
    return JSONResponse(status_code=200, content={"message": "Post published"})


@secure_router.put('/posts/remove/{post_id:int}')
def message_delete_get(request: Request,
                       post_id: int,
                       db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    posts_logger.info(
        f"Post delete attempt by user: user={user.username}, post_id={post_id}")
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        posts_logger.warning(
            f"Post does not exist occurred: user={user.username}, endpoint=/posts/remove/{post_id}")
        raise HTTPException(status_code=404, detail="This post does not exist")
    if post.user_id != user.id:
        posts_logger.warning(
            f"Unowned post exc occurred: user={user.username}, endpoint=/posts/remove/{post_id}")
        raise HTTPException(status_code=403, detail="You do not own this post")
    post.hide()
    posts_logger.info(
        f"Post hidden successfully by user: user={user.username}, post_id={post_id}")
    db.commit()
    return JSONResponse(status_code=200, content={"message": "Post hidden"})

@guest_router.get('/posts/{post_id:int}')
def message_get(request: Request,
                post_id: int,
                db: SessionLocal = Depends(get_db)):
    posts_logger.info(
        f"Message read attempt: user={'guest' if not hasattr(request.state, 'user') else request.state.user.get('sub')}")
    post = db.query(Post).filter(Post.id == post_id).filter(Post.hidden == bool(0)).first()
    if not post:
        posts_logger.warning(
            f"Post does not exist occurred: user={'guest' if request.state.user is None else request.state.user.get('sub')}, endpoint=/posts/{post_id}")
        raise HTTPException(status_code=404, detail="This post does not exist")
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
    posts_logger.info(
        f"Post read successfully by user: {'guest' if request.state.user is None else request.state.user.get('sub')}, post={post_id}")
    return JSONResponse(content={"data": post_json})


@guest_router.get('/posts/all/{page:int}')
def messages_get(request: Request,
                 page: int,
                 db: SessionLocal = Depends(get_db)):
    posts_logger.info(
        f"Messages read attempt by user: user={'guest' if request.state.user is None else request.state.user.get('sub')}")
    posts = db.query(Post). \
        filter(Post.hidden == bool(0)). \
        filter(Post.type == 1). \
        offset((page - 1) * settings.POSTS_PER_PAGE). \
        limit(settings.POSTS_PER_PAGE).all()
    if not posts:
        posts_logger.warning(
            f"Page does not exist occurred: user={'guest' if request.state.user is None else request.state.user.get('sub')}, endpoint=/posts/all/{page}")
        raise HTTPException(status_code=404, detail="No such page")
    posts_json = [{'id': post.id,
                   'title': post.title,
                   'content': post.content,
                   'user': post.user.username,
                   'date': str(post.created_at),
                   'likes': db.query(func.count(Like.post_id)).filter(Like.post_id == post.id).scalar(),
                   'comments': get_comments(post.id, db)}
                  for post in posts]
    db.close()
    posts_logger.info(
        f"Messages read successfully by user: user={'guest' if request.state.user is None else request.state.user.get('sub')}, posts={[post.id for post in posts]}")
    return JSONResponse(content={"data": posts_json})


@secure_router.get('/posts/followed/{page:int}')
def followed_posts_get(request: Request,
                       page: int,
                       db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    posts_logger.info(
        f"Followed users' messages read attempt by user: user={user.username}")
    followed_users = db.query(Followers).filter(Followers.follower_id == user.id).all()
    posts = db.query(Post). \
        filter(Post.user_id.in_([follow.followed_id for follow in followed_users])). \
        filter(Post.hidden == bool(0)). \
        filter(Post.type == 1). \
        offset((page - 1) * settings.POSTS_PER_PAGE). \
        limit(settings.POSTS_PER_PAGE).all()
    if not posts:
        posts_logger.warning(
            f"Page does not exist occurred: user={user.username}, endpoint=/posts/followed/{page}")
        raise HTTPException(status_code=404, detail="No such page")
    posts_json = [{'id': post.id,
                   'title': post.title,
                   'content': post.content,
                   'user': post.user.username,
                   'date': str(post.created_at),
                   'likes': db.query(func.count(Like.post_id)).filter(Like.post_id == post.id).scalar(),
                   'comments': get_comments(post.id, db)}
                  for post in posts]
    posts_logger.info(
        f"Followed users' messages read successfully by user: user={user.username}, posts={[post.id for post in posts]}")
    return JSONResponse(content={"data": posts_json})


@secure_router.put('/posts/{post_id:int}/like')
def post_like_get(request: Request,
                  post_id: int,
                  db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    posts_logger.info(
        f"Post like attempt by user: {user.username}, post={post_id}")
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post or post.hidden == bool(1):
        posts_logger.warning(
            f"Post does not exist occurred: user={user.username}, endpoint=/posts/{post_id}/like")
        raise HTTPException(status_code=404, detail="This post does not exist")
    if not user.like(post, db):
        posts_logger.warning(
            f"Post already liked by user: user={user.username}")
        raise HTTPException(status_code=403, detail="This post is already liked")
    if post.user_id == user.id:
        posts_logger.warning(
                             f"Trying to like yourself by user: {user.username}, post={post_id}")
        raise HTTPException(status_code=403, detail="You can't like yourself")
    db.commit()
    posts_logger.info(
        f"Post like successfully by user: user={user.username}, post={post_id}")
    db.close()
    return JSONResponse(content={"message": "Successful"})


@secure_router.delete('/posts/{post_id:int}/remove-like')
def post_remove_like_get(request: Request,
                         post_id: int,
                         db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    posts_logger.info(
        f"Post like remove attempt by user: {user.username}, post={post_id}")
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post or post.hidden == bool(1):
        posts_logger.warning(
            f"Post does not exist occurred: user={user.username}, endpoint=/posts/{post_id}/remove-like")
        raise HTTPException(status_code=404, detail="This post does not exist")
    if not user.remove_like(post, db):
        posts_logger.warning(
            f"Post isn't liked by user: {user.username}, post={post_id}")
        raise HTTPException(status_code=403, detail="This post isn't liked")
    db.commit()
    posts_logger.info(
        f"Post like remove successfully by user: user={user.username}, post={post_id}")
    db.close()
    return JSONResponse(content={"message": "Successful"})


@secure_router.post('/posts/{post_id}/comment')
def post_comment_post(request: Request,
                      comment: PostCreate,
                      post_id: int,
                      db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    posts_logger.info(
        f"Post comment attempt by user: {user.username}, post={post_id}")
    post_to_comment = db.query(Post).filter(Post.id == post_id).first()
    if not post_to_comment:
        posts_logger.warning(
            f"Post does not exist occurred: user={user.username}, endpoint=/posts/{post_id}/comment")
        raise HTTPException(status_code=404, detail="No such post")
    if post_to_comment.type in (2, 3):
        posts_logger.warning(
            f"Post can't be commented due to it's type by user: {user.username}, post={post_id}")
        raise HTTPException(status_code=403, detail="You can't comment comment or answer")
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
    posts_logger.info(
        f"Post comment successfully by user: {user.username}, post={post_id}, comment={db_post.id}")
    return JSONResponse(status_code=200, content={"message": "Comment published"})


@secure_router.post('/posts/{post_id}/answer')
def post_answer_post(request: Request,
                     answer: PostCreate,
                     post_id: int,
                     db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == request.state.user.get("sub")).first()
    posts_logger.info(
        f"Comment answer attempt by user: {user.username}, post={post_id}")
    post_to_answer = db.query(Post).filter(Post.id == post_id).first()
    if not post_to_answer:
        posts_logger.warning(
            f"Post does not exist occurred: user={user.username}, endpoint=/posts/{post_id}/answer")
        raise HTTPException(status_code=404, detail="No such post")
    if post_to_answer.type == 1:
        posts_logger.warning(
            f"Post can't be answered due to it's type by user: {user.username}, post={post_id}")
        raise HTTPException(status_code=403, detail="You can't answer to the post")
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
    posts_logger.info(
        f"Post answer successfully by user: {user.username}, post={post_id}, answer={db_post.id}")
    return JSONResponse(status_code=200, content={"message": "Answer published"})
