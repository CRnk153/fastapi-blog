from apps import app
from uvicorn import run
from apps.routes import router
app.include_router(router)

if __name__ == '__main__':
    run(
        app
    )
