from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User
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
