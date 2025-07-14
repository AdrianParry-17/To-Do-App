import routers
from utils import Config
from models.users import User, UserRole, UserVisibility
from schemas import MessageResponseSchema
from schemas.users import UserAttributesSchema, UserCollectionsResponseSchema,\
    UserCreateSchema, UserIDConstraints, UserObjectResponseSchema, UserResponseSchema,\
    UserUpdateSchema, UserRoleCollectionsResponseSchema, UserRoleResponseSchema
from schemas.errors import ErrorResponseSchema
from services.users import UserPermissionService, UserService, UserRoleService
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query, status
from security import Permissions
from pydantic import Field
from typing import Annotated, List, Optional

QueryOffsetField = Annotated[int, Field(ge=0, allow_inf_nan=False)]
QueryLimitField = Annotated[int, Field(ge=1, allow_inf_nan=False)]

router = APIRouter(prefix='/user', tags=["User"])

def GetUserResponseSchema(user: User) -> UserResponseSchema:
    """Get the User Response Schema from the given User ORM object."""
    return UserResponseSchema(
        id=user.id,
        username=user.username,
        attributes=UserAttributesSchema(
            email=user.attributes.email,
            visibility=user.attributes.visibility
        ),
        createdTime=user.createdTime,
        updatedTime=user.updatedTime,
        version=user.version
    )

def GetUserRoleResponseSchema(user_role: UserRole) -> UserRoleResponseSchema:
    """Get the User Role Response Schema from the given User Role ORM object."""
    return UserRoleResponseSchema(
        name=user_role.name,
        
        createdTime=user_role.createdTime,
        updatedTime=user_role.updatedTime,
        version=user_role.version
    )

@router.get(
    '/', name="List Users", status_code=status.HTTP_200_OK,
    response_model=UserCollectionsResponseSchema,
    dependencies=[Depends(routers.GetCurrentUserID)],
    responses={
        status.HTTP_401_UNAUTHORIZED : { "model" : ErrorResponseSchema },
        status.HTTP_403_FORBIDDEN : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def ListUsers(username: Optional[str] = None,
                    user_ids: List[str] = Query([]),
                    visibility: List[UserVisibility] = Query([UserVisibility.Public]),
                    offset: QueryOffsetField = 0,
                    limit: QueryLimitField = 10,
                    session: AsyncSession = Depends(routers.GetDatabaseSession),
                    current_user_id: str = Depends(routers.GetCurrentUserID)):

    if not await UserPermissionService.CheckUserPermission(session, current_user_id, 'user.list', check_user_exists=False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Permission required!")
        
    if limit > Config.GetConfig("database.maxQueryLimit"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The 'limit' of query must be <= {Config.GetConfig("database.maxQueryLimit")}, not {limit}!")

    result = await UserService.ListUsers(session,
                                         username=username,
                                         user_ids=user_ids,
                                         visibility=visibility,
                                         offset=offset, limit=limit)
    
    return UserCollectionsResponseSchema(
        data=[GetUserResponseSchema(user) for user in result]
    )

@router.get(
    '/search', name="Search User", status_code=status.HTTP_200_OK,
    response_model=UserCollectionsResponseSchema,
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def SearchUsers(username: Optional[str] = None,
                      user_ids: List[str] = Query([]),
                      offset: QueryOffsetField = 0,
                      limit: QueryLimitField = 10,
                      session: AsyncSession = Depends(routers.GetDatabaseSession)):

    if limit > Config.GetConfig("database.maxQueryLimit"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The 'limit' of query must be <= {Config.GetConfig("database.maxQueryLimit")}, not {limit}!")

    result = await UserService.ListUsers(session,
                                         username=username,
                                         user_ids=user_ids,
                                         visibility=[UserVisibility.Public],
                                         offset=offset, limit=limit)
    
    return UserCollectionsResponseSchema(
        data=[GetUserResponseSchema(user) for user in result]
    )

@router.get(
    '/{user_id}', name="Get User", status_code=status.HTTP_200_OK,
    response_model=UserObjectResponseSchema,
    responses={
        status.HTTP_404_NOT_FOUND : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def GetUser(user_id: UserIDConstraints,
                  session: AsyncSession = Depends(routers.GetDatabaseSession)):
    
    result = await UserService.FromID(session, user_id)
    if result.attributes.visibility not in [UserVisibility.Public]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"User with id '{user_id}' are not publically visible!")
    
    return UserObjectResponseSchema(data=GetUserResponseSchema(result))

@router.post(
    "/", name="Create User", status_code=status.HTTP_201_CREATED,
    response_model=UserObjectResponseSchema,
    dependencies=[Depends(routers.GetCurrentUserID)],
    responses={
        status.HTTP_400_BAD_REQUEST : { "model" : ErrorResponseSchema },
        status.HTTP_401_UNAUTHORIZED : { "model" : ErrorResponseSchema },
        status.HTTP_403_FORBIDDEN : { "model" : ErrorResponseSchema },
        status.HTTP_409_CONFLICT : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def CreateUser(info: UserCreateSchema,
                     session: AsyncSession = Depends(routers.GetDatabaseSession),
                     current_user_id: str = Depends(routers.GetCurrentUserID)):
    if not await UserPermissionService.CheckUserPermission(session, current_user_id, 'user.create', check_user_exists=False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Permission required!")
    
    user = await UserService.Create(session,
                                    username=info.username,
                                    password=info.password,
                                    visibility=info.visibility,
                                    email=info.email,
                                    check_username_exist=True,
                                    check_email_exist=True)
    roles = info.roles
    if not roles:
        roles.append(Permissions.GetOptions('default_role', 'user'))
    
    await UserRoleService.SetUserRoles(session, user.id, roles,
                                       check_user_exists=False,
                                       check_valid_role_names=True)
    
    return user

@router.put(
    '/{user_id}', name="Update User", status_code=status.HTTP_200_OK,
    response_model=UserObjectResponseSchema,
    dependencies=[Depends(routers.GetCurrentUserID)],
    responses={
        status.HTTP_400_BAD_REQUEST : { "model" : ErrorResponseSchema },
        status.HTTP_401_UNAUTHORIZED : { "model" : ErrorResponseSchema },
        status.HTTP_403_FORBIDDEN : { "model" : ErrorResponseSchema },
        status.HTTP_404_NOT_FOUND : { "model" : ErrorResponseSchema },
        status.HTTP_409_CONFLICT : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }   
    }
)
async def UpdateUser(user_id: str, info: UserUpdateSchema,
                     session: AsyncSession = Depends(routers.GetDatabaseSession),
                     current_user_id: str = Depends(routers.GetCurrentUserID)):
    if current_user_id != user_id:
        if not await UserPermissionService.CheckUserPermission(session, current_user_id, 'user.update', check_user_exists=False):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Permission required!")
    
    user = await UserService.FromID(session, user_id)
    user = await UserService.Update(session, user,
                                    username=info.username,
                                    password=info.password,
                                    visibility=info.visibility,
                                    email=info.email,
                                    version_update=True,
                                    check_username_exist=True,
                                    check_email_exist=True)
    
    return UserObjectResponseSchema(data=GetUserResponseSchema(user))
    
@router.delete(
    "/{user_id}", name="Delete User", status_code=status.HTTP_200_OK,
    response_model=MessageResponseSchema[str],
    dependencies=[Depends(routers.GetCurrentUser)],
    responses={
        status.HTTP_400_BAD_REQUEST : { "model" : ErrorResponseSchema },
        status.HTTP_403_FORBIDDEN : { "model" : ErrorResponseSchema },
        status.HTTP_404_NOT_FOUND : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def DeleteUser(user_id: UserIDConstraints,
                     session: AsyncSession = Depends(routers.GetDatabaseSession),
                     current_user_id: User = Depends(routers.GetCurrentUserID)):
    
    if current_user_id != user_id:
        if not await UserPermissionService.CheckUserPermission(session, current_user_id, 'user.delete', check_user_exists=False):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Permission required!")
    
    user_roles = await UserRoleService.GetUserRoles(session, user_id, check_user_exists=False)
    not_deletable_roles = set(Permissions.GetOptions('not_deletable_role', ['moderator', 'admin']))
    
    if any((role.name in not_deletable_roles) for role in user_roles):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The user with id '{user_id}' have a role that made them not deletable!")

    await UserService.Delete(session, user_id)
    
    return MessageResponseSchema[str](
        data=f"Successfully deleted user with id '{user_id}'"
    )
    
@router.get(
    '/role/{user_id}', name="Get User Roles", status_code=status.HTTP_200_OK,
    response_model=UserRoleCollectionsResponseSchema,
    responses={
        status.HTTP_400_BAD_REQUEST : { "model" : ErrorResponseSchema },
        status.HTTP_404_NOT_FOUND : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def GetUserRoles(user_id: UserIDConstraints,
                       session: AsyncSession = Depends(routers.GetDatabaseSession)):
    
    user = await UserService.FromID(session, user_id)
    if user.attributes.visibility not in [UserVisibility.Public]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"User with id '{user_id}' are not publically visible!")

    result = await UserRoleService.GetUserRoles(session, user_id, check_user_exists=False)
    
    return UserRoleCollectionsResponseSchema(
        data=[GetUserRoleResponseSchema(role) for role in result]
    )

@router.post(
    '/role/{user_id}', name="Set User Roles", status_code=status.HTTP_200_OK,
    response_model=MessageResponseSchema[str],
    dependencies=[Depends(routers.GetCurrentUserID)],
    responses={
        status.HTTP_400_BAD_REQUEST : { "model" : ErrorResponseSchema },
        status.HTTP_403_FORBIDDEN : { "model" : ErrorResponseSchema },
        status.HTTP_404_NOT_FOUND : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def SetUserRoles(user_id: UserIDConstraints,
                       roles: List[str] = Query([]),
                       session: AsyncSession = Depends(routers.GetDatabaseSession),
                       current_user_id: str = Depends(routers.GetCurrentUserID)):
    if not await UserPermissionService.CheckUserPermission(session, current_user_id, 'user.set_permission', check_user_exists=False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Permission required!")
    
    await UserRoleService.SetUserRoles(session, user_id, roles)
    
    return MessageResponseSchema[str](
        data=f"Successfully set roles to user with id '{user_id}'"
    )

