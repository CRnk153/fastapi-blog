from fastapi import FastAPI
import logging
from logging.handlers import RotatingFileHandler
from fastapi import Request
from fastapi.responses import JSONResponse

app = FastAPI(
    debug=True
)

logging.basicConfig(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

global_logger = logging.getLogger(__name__)
global_file_handler = RotatingFileHandler('logs/critical.log', maxBytes=1024 * 1024, backupCount=5)
global_file_handler.setLevel(logging.ERROR)
global_file_handler.setFormatter(formatter)
global_logger.addHandler(global_file_handler)

auth_logger = logging.getLogger(__name__)
auth_file_handler = RotatingFileHandler('logs/authentication.log', maxBytes=1024 * 1024, backupCount=5)
auth_file_handler.setLevel(logging.INFO)
auth_file_handler.setFormatter(formatter)
auth_logger.addHandler(auth_file_handler)

posts_logger = logging.getLogger(__name__)
posts_file_handler = RotatingFileHandler('logs/post_interactions.log', maxBytes=1024 * 1024, backupCount=5)
posts_file_handler.setLevel(logging.INFO)
posts_file_handler.setFormatter(formatter)
posts_logger.addHandler(posts_file_handler)

@app.exception_handler(Exception)  # doesn't work right now
async def global_exception_handler(request: Request, exc: Exception):
    global_logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
