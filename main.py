from uvicorn import run
from apps.routes import auth, posts, users, admin,\
    router_auth, router_non_auth, protected_router
from apps import app

app.include_router(router_auth)
app.include_router(router_non_auth)
app.include_router(protected_router)

if __name__ == '__main__':
    run(
        app
    )
