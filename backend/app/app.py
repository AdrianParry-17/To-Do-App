import routers.tasks
import dotenv, schemas, schemas.errors, routers.users, routers.auth
# import routers.tasks, routers.auth
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi import FastAPI, Request, status
from database import Database
from security import Permissions
from utils import Config, Logger
from contextlib import asynccontextmanager
from starlette.exceptions import HTTPException as StarletteHTTPException

#TODO: Here's a todo list
#!  - Bug (Need to fix):
#       + Input Sanitization (Zero-Width Characters, Control Characters, Special/Decoration Character).
#       + Input Validation (Emoji,...)
#*  - Task (Need to do):
#       + Making Schema, and error response.
#       + Add Authorization and Authentication.
#       + Adding User Search route, and Register route.
#?  - Implement Note (Non-Urgent):
#       + Use Alembic (when database start being used)
#       + Check Database.Connect, need to remove some temporary code for enable SQLite foreign key when switching database (to PostgreSQL)

#* Call when initialize the backend
async def onInitialize() -> bool:
    #* Pre-initialization
    dotenv.load_dotenv()
    
    if not Config.Initialize():
        return False
    Logger.Initialize()
    
    #* Database Initialize
    if not await Database.Connect():
        Logger.LogError("Failed to connect to the database!")
        return False
    if not await Database.CreateTables():
        Logger.LogError("Failed to create ORM tables!")
        return False
    
    #* Security Initialize
    Logger.LogInfo("Syncing database permissions...")
    if not await Permissions.Initialize():
        Logger.LogError("Failed to syncing permissions!")
        return False
    
    return True

#* Call when deinitialize the backend
async def onDeinitialize():
    #* Database Deinitialize
    if not await Database.Disconnect():
        Logger.LogError("Failed to disconnected from the database!")
        return

#* The lifespan of the FastAPI app.
@asynccontextmanager
async def appLifespan(app: FastAPI):
    # Initialize
    if not await onInitialize():
        Logger.LogError("Failed to initialize! Exiting...")
        return

    yield
    
    # Deinitialize
    await onDeinitialize()

app = FastAPI(lifespan=appLifespan)
app.include_router(routers.users.router)
app.include_router(routers.tasks.router)
app.include_router(routers.auth.router)

#* Error handler

@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content= schemas.errors.ErrorResponseSchema(
            data=[
                schemas.errors.ErrorDetailSchema(
                    code=exc.status_code,
                    detail=str(exc.detail)
                )
            ]
        ).model_dump(mode='json')
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=schemas.errors.ErrorResponseSchema(
            data=[
                schemas.errors.ErrorDetailSchema(
                    code=exc.status_code,
                    detail=str(exc.detail)
                )
            ]
        ).model_dump(mode='json')
    )
    
@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    def format_message(e) -> schemas.errors.ErrorDetailSchema:
        # e is a dict with keys: 'loc', 'msg', 'type', etc.
        loc = ".".join(str(x) for x in e.get("loc", []))
        msg = e.get("msg", "Invalid input.")
        err_type = e.get("type", "unknown_error")
        if loc:
            detail = f"{loc} ({err_type}): {msg}"
        else:
            detail = f"({err_type}): {msg}"
            
        return schemas.errors.ErrorDetailSchema(
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=schemas.errors.ErrorResponseSchema(
            data=[format_message(e) for e in exc.errors()]
        ).model_dump(mode='json')
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=schemas.errors.ErrorResponseSchema(
            data=[
                schemas.errors.ErrorDetailSchema(code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                                 detail=f"{type(exc).__name__}: {str(exc)}")
            ]
        ).model_dump(mode='json')
    )
