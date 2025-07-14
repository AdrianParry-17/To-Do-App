from typing import AsyncGenerator
from utils import Logger
from services.users import UserService
from models.users import User
from security import AuthTools
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from database import Database

bearer_scheme = HTTPBearer()

async def GetDatabaseSession() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function for FastAPI endpoints to provide a valid AsyncSession.
    The session will be automatically closed after the endpoint finishes.
    
    Yields:
        AsyncSession: The valid database session to be used in the endpoint.

    Raises:
        HTTPException: If the database session cannot be created,
            raises a 503 Service Unavailable error.
    """
    if Database.SessionFactory is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The server database is currently not available!"
        )
    
    async with Database.SessionFactory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e

async def GetCurrentUser(session: AsyncSession = Depends(GetDatabaseSession),
                         credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> User:
    """Get the current user (use for protected route). HTTPException can occurred."""
    token = credentials.credentials
    payload = AuthTools.VerifyJWT(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Invalid access token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Invalid access token")
    
    try:
        return await UserService.FromID(session, user_id)
    except Exception as e:
        Logger.LogException(e, "GetCurrentUser: An exception has occurred")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Invalid access token")
        
async def GetCurrentUserID(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """Get the current user id (use for protected route). HTTPException can occurred.\n
    This will not perform a database query, so can be use for quick user id checking."""
    token = credentials.credentials
    payload = AuthTools.VerifyJWT(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Invalid access token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Invalid access token")
    return user_id
    