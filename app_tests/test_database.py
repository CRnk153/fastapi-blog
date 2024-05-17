from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User, Followers, Post, Like
import pytest

engine = create_engine('sqlite:///test.db')
Session = sessionmaker(bind=engine)

@pytest.fixture(scope="function")
def test_session():
    session = Session()
    yield session
    session.rollback()

def test_user_get(test_session):
    user = User(username="test_user",
                email="test@example.org",
                hashed_password="test_password")
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    got_user = test_session.query(User).filter(User.username == "test_user").first()
    assert got_user.hashed_password == "test_password"

def test_user_follow(test_session):
    user = User(username="test_user",
                email="test@example.org",
                hashed_password="test_password")
    user2 = User(username="test_user2",
                 email="test2@example.org",
                 hashed_password="test_password2")
    test_session.add(user)
    test_session.add(user2)
    test_session.commit()
    test_session.refresh(user)
    test_session.refresh(user2)
    user.follow(user2, test_session)
    test_session.commit()
    test_session.refresh(user)
    test_session.refresh(user2)
    assert test_session.query(Followers). \
        filter(Followers.follower_id == user.id). \
        filter(Followers.followed_id == user2.id). \
        first()
    user.unfollow(user2, test_session)
    test_session.commit()
    test_session.refresh(user)
    test_session.refresh(user2)
    assert not test_session.query(Followers). \
        filter(Followers.follower_id == user.id). \
        filter(Followers.followed_id == user2.id). \
        first()

def test_post_get(test_session):
    user = User(username="test_user",
                email="test@example.org",
                hashed_password="test_password")
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    post = Post(title="test",
                content="test",
                user_id=user.id)
    test_session.add(post)
    test_session.commit()
    test_session.refresh(post)
    assert post.title == "test"
    post.hide()
    test_session.commit()
    assert post.hidden == bool(1)

def test_like_post(test_session):
    user = User(username="test_user",
                email="test@example.org",
                hashed_password="test_password")
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    post = Post(title="test",
                content="test",
                user_id=user.id)
    test_session.add(post)
    test_session.commit()
    test_session.refresh(post)
    user.like(post, test_session)
    test_session.commit()
    assert test_session.query(Like). \
        filter(Like.user_id == user.id). \
        filter(Like.post_id == post.id). \
        first()
    user.remove_like(post, test_session)
    test_session.commit()
    assert not test_session.query(Like). \
        filter(Like.user_id == user.id). \
        filter(Like.post_id == post.id). \
        first()

def test_post_comment_and_answer(test_session):
    user = User(username="test_user",
                email="test@example.org",
                hashed_password="test_password")
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    post = Post(title="test",
                content="test",
                user_id=user.id)
    test_session.add(post)
    test_session.commit()
    test_session.refresh(post)
    user2 = User(username="test_user2",
                 email="test2@example.org",
                 hashed_password="test_password2")
    test_session.add(user2)
    test_session.commit()
    test_session.refresh(user2)
    post2 = Post(title="test2",
                 content="test2",
                 user_id=user2.id,
                 type=2,
                 refer_to=post.id)
    test_session.add(post2)
    test_session.commit()
    test_session.refresh(post2)
    post3 = Post(title="test3",
                 content="test3",
                 user_id=user.id,
                 type=3,
                 refer_to=post2.id)
    test_session.add(post3)
    test_session.commit()
    test_session.refresh(post3)
    assert test_session.query(Post).filter(Post.refer_to == post.id). \
        filter(Post.type == 2). \
        filter(post.type == 1). \
        first()
    assert test_session.query(Post).filter(Post.refer_to == post2.id). \
        filter(Post.type == 3). \
        filter(post2.type == 2). \
        first()
