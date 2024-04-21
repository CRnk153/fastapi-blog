from sqlalchemy import String, Integer, ForeignKey, Column, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), index=True)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(20), index=True)
    email = Column(String(340), index=True)
    role_id = Column(Integer, ForeignKey('roles.id'), default=1)
    hashed_password = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    posts = relationship("Post", back_populates="username")

class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    content = Column(String(3000))
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(ForeignKey('users.id'))
    username = relationship("User", back_populates="posts")
