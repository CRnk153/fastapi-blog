import os

class settings:
    SECRET_KEY = str(os.getenv("SECRET_KEY"))
    POSTS_PER_PAGE = 15
    ALGORITHM = "HS256"
    EXPIRED_TIME = 15
    AUTH_REQUIRED_FUNCS = ["auth_logout_get",
                           "messages_post",
                           "follow_get",
                           "unfollow_get",
                           "followed_posts_get"]
