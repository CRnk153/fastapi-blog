from typing import Optional
from pydantic import BaseModel, EmailStr

# Nearly useless

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    role: int

    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str
    role: int

class UserDB(User):
    hashed_password: str
    role: int

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    username: Optional[str] = None
    role: Optional[int]

class PostBase(BaseModel):
    title: str
    content: str

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class PostInDB(Post):
    user_id: int

class PostDB(Post):
    user_id: int
