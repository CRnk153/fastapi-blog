from uvicorn import run
# noinspection PyUnresolvedReferences
from apps.routes import auth, posts, users, admin,\
    secure_router, guest_router, admin_router
from apps import app

app.include_router(secure_router)
app.include_router(guest_router)
app.include_router(admin_router)

if __name__ == '__main__':
    run(
        app
    )
