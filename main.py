from uvicorn import run
from apps.routes import auth, posts, users, router_auth, router_non_auth
from apps import app

app.include_router(router_auth)
app.include_router(router_non_auth)

if __name__ == '__main__':
    run(
        app
    )
