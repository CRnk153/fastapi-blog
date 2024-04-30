from sqlalchemy import String, Integer, ForeignKey, Column, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), index=True)


class Followers(Base):
    __tablename__ = 'followers'

    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, ForeignKey('users.id'))
    followed_id = Column(Integer, ForeignKey('users.id'))

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(20), index=True)
    email = Column(String(340), index=True)
    role_id = Column(Integer, ForeignKey('roles.id'), default=1)
    hashed_password = Column(String, index=True)
    created_at = Column(DateTime)
    last_seen = Column(DateTime, default=datetime.utcnow())
    posts = relationship("Post", back_populates="username")
    followers = relationship(
        "Followers",
        backref="user",
        primaryjoin="(User.id == Followers.follower_id)"
    )
    following = relationship(
        "User",
        secondary="followers",
        primaryjoin="(User.id == Followers.followed_id)",
        backref="followers_of",
        overlaps="followers,user",
        foreign_keys="[Followers.followed_id]"
    )
    liked_posts = relationship("Post", secondary="likes", back_populates="liked_by")
    likes = relationship("Like", back_populates="user")

    def __init__(self, username, email, hashed_password):
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.created_at = datetime.utcnow()

    def follow(self, user_to_follow):
        if user_to_follow not in self.following:
            self.following.append(user_to_follow)
            return True
        return False

    def unfollow(self, user_to_unfollow):
        if user_to_unfollow in self.following:
            self.following.remove(user_to_unfollow)
            return True
        return False

    def like(self, post_to_like):
        if self not in post_to_like.liked_by:
            post_to_like.liked_by.append(self)
            return True
        return False

    def remove_like(self, post_to_remove_like):
        if self in post_to_remove_like.liked_by:
            post_to_remove_like.liked_by.remove(self)
            return True
        return False

class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    content = Column(String(3000))
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(ForeignKey('users.id'))

    username = relationship("User", back_populates="posts")
    likes = relationship("Like", back_populates="post")
    liked_by = relationship("User", secondary="likes", back_populates="liked_posts")

class Like(Base):
    __tablename__ = 'likes'

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    post = relationship("Post", back_populates="likes")
    user = relationship("User", back_populates="likes")
