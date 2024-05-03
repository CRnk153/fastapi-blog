from starlette.middleware.cors import CORSMiddleware

from apps import app
from config import settings

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from apps.dependencies import check_auth, SessionLocal, get_db, get_current_user
import jwt

router_non_auth = APIRouter()
router_auth = APIRouter(dependencies=[Depends(check_auth)])

# I hate middleware

@router_non_auth.get('/')
def home_get(request: Request,
             db: SessionLocal = Depends(get_db)):
    return JSONResponse(status_code=200, content={"message": "Hello world!",
                                                  "user": get_current_user(request, db)})

async def verify_token(request: Request, call_next):
    token = request.cookies.get("access_token")
    if token != "":
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            request.state.user = payload
        except jwt.DecodeError:
            request.state.user = None
            raise HTTPException(status_code=401, detail="Invalid token")
        except jwt.ExpiredSignatureError:
            request.state.user = None
            response = JSONResponse(status_code=401, content="Sign in again")
            response.set_cookie(key="access_token", value="", httponly=True, secure=True)
            return response
    else:
        request.state.user = None
    response = await call_next(request)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(verify_token)
