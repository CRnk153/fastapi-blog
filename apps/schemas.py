from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    username: str = Field(min_length=5, max_length=20)
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: int = Field(lt=4, gt=0)

class UserProfileEdit(BaseModel):
    username: str = Field(min_length=5, max_length=20)
    email: EmailStr

class UserPasswordChange(BaseModel):
    password: str = Field(min_length=8)

class PostBase(BaseModel):
    title: str
    content: str

class PostCreate(PostBase):
    pass

class Post(PostBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
