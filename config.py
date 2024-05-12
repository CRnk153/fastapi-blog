import os

class settings:
    def __init__(self):
        pass

    SECRET_KEY = str(os.getenv("SECRET_KEY"))
    POSTS_PER_PAGE = 15
    ALGORITHM = "HS256"
    EXPIRED_TIME = 15
