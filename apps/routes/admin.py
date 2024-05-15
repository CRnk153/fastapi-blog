from . import protected_router
from apps.dependencies import SessionLocal, get_db
from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from database.models import Post

@protected_router.get('/admin/hide-post/{post_id}')
def hide_post_get(post_id: int,
                  db: SessionLocal = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="No such post")
    if post.user.role == 2:
        raise HTTPException(status_code=403, detail="Author is admin")
    post.hide()
    return JSONResponse(status_code=200, content={"message": "Successful"})
