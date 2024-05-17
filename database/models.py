from sqlalchemy import String, Integer, ForeignKey, Column, DateTime, Boolean
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime


Base = declarative_base()

class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), index=True)

class PostType(Base):
    __tablename__ = 'ptypes'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), index=True)

class Followers(Base):
    __tablename__ = 'followers'

    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, ForeignKey('users.id'))
    followed_id = Column(Integer, ForeignKey('users.id'))

    def __init__(self, follower_id, followed_id):
        self.follower_id = follower_id
        self.followed_id = followed_id

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(20), index=True)
    email = Column(String(340), index=True)
    role_id = Column(Integer, ForeignKey('roles.id'), default=1)
    hashed_password = Column(String, index=True)
    created_at = Column(DateTime)
    last_seen = Column(DateTime, default=datetime.utcnow())

    posts = relationship("Post", back_populates="user")
    likes = relationship("Like", back_populates="user")

    followers = relationship(
        "Followers",
        backref="user",
        primaryjoin="(User.id == Followers.follower_id)",
        foreign_keys="[Followers.follower_id]"
    )

    following = relationship(
        "User",
        secondary="followers",
        primaryjoin="(User.id == Followers.followed_id)",
        backref="followers_of",
        overlaps="followers,user",
        foreign_keys="[Followers.followed_id]"
    )

    def __init__(self, username, email, hashed_password):
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.created_at = datetime.utcnow()

    def follow(self, user_to_follow, db):
        if not db.query(Followers). \
                filter(Followers.follower_id == self.id). \
                filter(Followers.followed_id == user_to_follow.id). \
                first():
            db.add(Followers(follower_id=self.id, followed_id=user_to_follow.id))
            return True
        return False

    def unfollow(self, user_to_unfollow, db):
        if follow_to_cancel := db.query(Followers). \
                filter(Followers.follower_id == self.id). \
                filter(Followers.followed_id == user_to_unfollow.id). \
                first():
            db.delete(follow_to_cancel)
            return True
        return False

    def like(self, post_to_like, db):
        if not db.query(Like). \
                filter(Like.user_id == self.id). \
                filter(Like.post_id == post_to_like.id). \
                first():
            db.add(Like(user=self, post=post_to_like))
            db.commit()
            return True
        return False

    def remove_like(self, post_to_remove_like, db):
        if like_to_remove := db.query(Like). \
                filter(Like.user_id == self.id). \
                filter(Like.post_id == post_to_remove_like.id). \
                first():
            db.delete(like_to_remove)
            return True
        return False

class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(100))
    content = Column(String(3000))
    created_at = Column(DateTime, default=datetime.utcnow)
    hidden = Column(Boolean, default=0)

    user_id = Column(ForeignKey('users.id'))
    user = relationship("User", back_populates="posts")
    likes = relationship("Like", back_populates="post")

    type = Column(Integer, ForeignKey('ptypes.id'), default=1)
    refer_to = Column(Integer, ForeignKey('posts.id'), default=None)

    children = relationship("Post",
                            foreign_keys=[refer_to],
                            backref="parent_post",
                            remote_side=[id])

    def hide(self):
        self.hidden = True

    def unhide(self):
        self.hidden = False

class Like(Base):
    __tablename__ = 'likes'

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    post = relationship("Post", back_populates="likes")
    user = relationship("User", back_populates="likes")

    def __init__(self, user, post):
        self.user = user
        self.post = post
