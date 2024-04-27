from apps import app
from uvicorn import run
from apps.routes import non_auth_router, auth_router
app.include_router(non_auth_router)
app.include_router(auth_router)

if __name__ == '__main__':
    run(
        app
    )
