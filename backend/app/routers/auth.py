import routers
from models.users import User, UserVisibility
from routers.users import GetUserResponseSchema
from schemas.errors import ErrorResponseSchema
from services.users import UserRoleService, UserService
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.users import UserObjectResponseSchema, UserResponseSchema
from schemas.auth import LoginRequestSchema, RegisterRequestSchema, TokenResponseSchema
from security import PasswordTools, AuthTools, Permissions
from fastapi import Depends, HTTPException, status
from fastapi.routing import APIRouter

router = APIRouter(
    prefix="/auth", 
    tags=["Authentication"]
)

@router.post(
    "/login", name="Login", status_code=status.HTTP_200_OK,
    response_model=TokenResponseSchema,
    responses={
        status.HTTP_401_UNAUTHORIZED : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def Login(info: LoginRequestSchema, session: AsyncSession = Depends(routers.GetDatabaseSession)):
    user = await UserService.FromUsername(session, info.username)
    if not user or not PasswordTools.VerifyPassword(info.password, user.passwordHash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid username or password")
    
    token = AuthTools.GenerateJWT({"sub" : user.id})
    if not token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to generate access token")
    return TokenResponseSchema(access_token=token, token_type="Bearer")

@router.post(
    "/register", name="Register", status_code=status.HTTP_201_CREATED,
    response_model=TokenResponseSchema,
    responses={
        status.HTTP_400_BAD_REQUEST : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def Register(info: RegisterRequestSchema, session: AsyncSession = Depends(routers.GetDatabaseSession)):
    user = await UserService.Create(session,
                                    username=info.username,
                                    password=info.password,
                                    visibility=UserVisibility.Public,
                                    email=info.email,
                                    check_username_exist=True,
                                    check_email_exist=True)
    
    #NOTE: This one work fine and fast, unless 'default_role' is not a valid role (or not specified).
    await UserRoleService.SetUserRoles(session, user.id,
                                       [Permissions.GetOptions('default_role', 'user')],
                                       check_user_exists=False,
                                       check_valid_role_names=False)
    
    token = AuthTools.GenerateJWT({"sub" : user.id})
    if not token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to generate access token")
    return TokenResponseSchema(access_token=token, token_type="Bearer")

@router.get(
    "/current", name="Get Current User", status_code=status.HTTP_200_OK,
    response_model=UserObjectResponseSchema,
    dependencies=[Depends(routers.GetCurrentUser)],
    responses={
        status.HTTP_401_UNAUTHORIZED : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def GetCurrentUser(current_user: User = Depends(routers.GetCurrentUser)):
    return UserObjectResponseSchema(
        data=GetUserResponseSchema(current_user)
    )