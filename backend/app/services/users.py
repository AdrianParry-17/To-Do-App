import datetime
from fastapi import status, HTTPException
from security import PasswordTools, Permissions
from repositories.users import UserRepository, UserAttributesRepository,\
    UserPermissionRepository, UserRoleRepository
from schemas.users import UserCreateSchema, UserUpdateSchema
from models.users import User, UserAttributes, UserPermission, UserRole, UserVisibility
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, select, delete, update
from utils import Logger, GenerateUUID
from typing import Iterable, List, Optional

class UserService:
    """The User Service class, provide static method to working with User.
    Notice that, Exception can occurred, but converted to HTTP Exception."""

    @staticmethod
    async def FromID(session: AsyncSession, user_id: str) -> User:
        """Query an User with the given id.

        Args:
            session (AsyncSession): The database session to query.
            user_id (str): The user id to query.

        HTTP Error:
            404 (Not Found): User with the given id is not found.
            500 (Internal Server Error): An exception has occurred.

        Returns:
            User: The result User with the given id.
        """
        result: Optional[User] = None
        try:
            result = await UserRepository.QueryFirst(session, select(User).where(User.id==user_id))
        except Exception as e:
            Logger.LogException(e, "UserService.FromID: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")
        
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Cannot find an user with id '{user_id}'")
            
        return result

    @staticmethod
    async def FromUsername(session: AsyncSession, username: str) -> User:
        """Query an User with the given username.

        Args:
            session (AsyncSession): The database session to query.
            username (str): The username to query.

        HTTP Error:
            404 (Not Found): User with the given username is not found.
            500 (Internal Server Error): An exception has occurred.

        Returns:
            User: The result User with the given username.
        """
        result: Optional[User] = None
        try:
            result = await UserRepository.QueryFirst(session, select(User).where(User.username==username))
        except Exception as e:
            Logger.LogException(e, "UserService.FromUsername: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")
        
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Cannot find an user with username '{username}'")
            
        return result

    @staticmethod
    async def ListUsers(session: AsyncSession,
                        username: Optional[str] = None,
                        user_ids: List[str] = [],
                        visibility: List[UserVisibility] = [UserVisibility.Public],
                        offset: int = 0, limit: int = 10) -> List[User]:
        """Query a list of Users with optional filtering, and supports pagination.

        Args:
            session (AsyncSession): The database session to query.
            username (Optional[str], optional): The username to search, default to None mean will not enable.
            user_ids (List[str], optional): A list of ids to search through, will only limited the search through these ids only.\
                Default to [] mean search all (a.k.a not applied).
            visibility (List[UserVisibility], optional): A list of user visibility to filter. Default to [UserVisibility.Public].
            offset (int, optional): The number of records to skip for pagination. Defaults to 0.
            limit (int, optional): The maximum number of records to return. Defaults to 10.

        HTTP Error:
            500 (Internal Server Error): An exception has occurred during the query.

        Returns:
            List[User]: A list of User.
        """
        stmt = select(User).join(UserAttributes, UserAttributes.userId==User.id)
        
        # Apply filter
        stmt = stmt.where(UserAttributes.visibility.in_(visibility))
        if username:
            stmt = stmt.where(func.lower(User.username).like(f"%{username.lower()}%"))
        if user_ids:
            stmt = stmt.where(User.id.in_(user_ids))
        
        # Apply offset and limit
        stmt = stmt.offset(max(offset, 0)).limit(max(1, limit))

        try:
            return await UserRepository.QueryAll(session, stmt)
        except Exception as e:
            Logger.LogException(e, "UserService.ListUsers: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")

    @staticmethod
    async def Create(session: AsyncSession,
                     username: str, password: str,
                     visibility: UserVisibility = UserVisibility.Public,
                     email: Optional[str] = None,
                     check_username_exist: bool = True,
                     check_email_exist: bool = True) -> User:
        """Create a new user with the specified attributes.

        Args:
            session (AsyncSession): The database session to use.
            username (str): The username for the new user.
            password (str): The password for the new user.
            visibility (UserVisibility, optional): The visibility setting for the user. Defaults to UserVisibility.Public.
            email (Optional[str], optional): The email address for the user. Defaults to None.
            check_username_exist (bool, optional): Whether to check if username already exists. Defaults to True.
            check_email_exist (bool, optional): Whether to check if email already exists. Defaults to True.

        HTTP Error:
            400 (Bad Request): Username or email already exists.
            409 (Conflict): Database conflict occurred during creation.
            500 (Internal Server Error): An exception has occurred or password hashing failed.

        Returns:
            User: The newly created user.
        """
        if check_username_exist and await UserRepository.QueryFirst(session, select(User).where(User.username==username)) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"An user with username '{username}' are already exist!")
        if check_email_exist and email and await UserAttributesRepository.QueryFirst(session, select(UserAttributes).where(UserAttributes.email==email)) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"An user with email '{email}' are already exist!")

        user_id = GenerateUUID()
        password_hash = PasswordTools.HashPassword(password)
        if not password_hash:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to hash password!")
        
        user = User(id=user_id, username=username, passwordHash=password_hash)
        user_attributes = UserAttributes(email=email, visibility=visibility)
        user.attributes=user_attributes
        
        try:
            return await UserRepository.Add(session, user)
        
        except IntegrityError as e:
            Logger.LogException(e, "UserService.Create: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Create causing a database conflict to occurred!")
        except Exception as e:
            Logger.LogException(e, "UserService.Create: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")

    @staticmethod
    async def Update(session: AsyncSession, user: User,
                     username: Optional[str] = None,
                     password: Optional[str] = None,
                     visibility: Optional[UserVisibility] = None,
                     email: Optional[str] = None,
                     version_update: bool = True,
                     check_username_exist: bool = True,
                     check_email_exist: bool = True) -> User:
        """Update an existing user's attributes.

        Args:
            session (AsyncSession): The database session to use.
            user (User): The user object to update.
            username (Optional[str], optional): New username. Defaults to None.
            password (Optional[str], optional): New password. Defaults to None.
            visibility (Optional[UserVisibility], optional): New visibility setting. Defaults to None.
            email (Optional[str], optional): New email address. Defaults to None.
            version_update (bool, optional): Whether to increment version and update timestamp. Defaults to True.
            check_username_exist (bool, optional): Whether to check if new username exists. Defaults to True.
            check_email_exist (bool, optional): Whether to check if new email exists. Defaults to True.

        HTTP Error:
            400 (Bad Request): New username or email already exists.
            409 (Conflict): Database conflict occurred during update.
            500 (Internal Server Error): An exception has occurred or password hashing failed.

        Returns:
            User: The updated user object.
        """
        
        if check_username_exist and username and await UserRepository.QueryFirst(session, select(User).where(User.username==username)) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Cannot change username to '{username}' because there's already existed an user with that username!")
        if check_email_exist and email and await UserAttributesRepository.QueryFirst(session, select(UserAttributes).where(UserAttributes.email==email)) is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Cannot change email to '{email}' because there's already existed an user with that email!")
    
        password_hash = PasswordTools.HashPassword(password) if password else None
        if password and not password_hash:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to hash the password!")

        try:
            if username:
                user.username = username
            if password_hash:
                user.passwordHash = password_hash
            if email:
                user.attributes.email = email
            if visibility:
                user.attributes.visibility = visibility
            
            if version_update:
                user.updatedTime = datetime.datetime.now()
                user.version += 1
            
            await session.commit()
            await session.refresh(user)
            
            return user
        
        except IntegrityError as e:
            Logger.LogException(e, "UserService.Update: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Update causing a database conflict to occurred!")
        except Exception as e:
            Logger.LogException(e, "UserService.Update: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")

    @staticmethod
    async def Delete(session: AsyncSession, user_id: str,
                     check_user_exist: bool = True) -> None:
        """Delete a user from the system.

        Args:
            session (AsyncSession): The database session to use.
            user_id (str): The ID of the user to delete.
            check_user_exist (bool, optional): Whether to verify user exists before deletion. Defaults to True.

        HTTP Error:
            404 (Not Found): User with the given id is not found.
            409 (Conflict): Database conflict occurred during deletion.
            500 (Internal Server Error): An exception has occurred.
        """
        if check_user_exist and await UserRepository.QueryFirst(session, select(User).where(User.id==user_id)) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Cannot find an user with id '{user_id}'")
        
        try:
            await UserRepository.Delete(session, delete(User).where(User.id==user_id))
        
        except IntegrityError as e:
            Logger.LogException(e, "UserService.Delete: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Delete causing a database conflict to occurred!")
        except Exception as e:
            Logger.LogException(e, "UserService.Delete: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")

class UserRoleService:
    """The User Role Service class, provides static methods for managing user roles.
    Notice that, Exception can occurred, but converted to HTTP Exception."""
    
    @staticmethod
    async def GetUserRoles(session: AsyncSession, user_id: str,
                           check_user_exists: bool = True) -> List[UserRole]:
        """Query all roles associated with a specific user.

        Args:
            session (AsyncSession): The database session to query.
            user_id (str): The user id to query roles for.
            check_user_exists (bool, optional): Whether to verify user exists before querying roles. Defaults to True.

        HTTP Error:
            404 (Not Found): User with the given id is not found.
            500 (Internal Server Error): An exception has occurred.

        Returns:
            List[UserRole]: A list of roles associated with the user.
        """
        if check_user_exists and await UserRepository.QueryFirst(session, select(User).where(User.id==user_id)) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Cannot find an user with id '{user_id}'")
        
        try:
            return await UserRoleRepository.GetRolesOfUser(session, user_id)
        except Exception as e:
            Logger.LogException(e, "UserRoleService.GetUserRoles: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")

    @staticmethod
    async def SetUserRoles(session: AsyncSession, user_id: str, role_names: Iterable[str],
                           check_user_exists: bool = True,
                           check_valid_role_names: bool = True) -> None:
        """Set the roles for a specific user, replacing any existing roles.

        Args:
            session (AsyncSession): The database session to use.
            user_id (str): The user id to set roles for.
            role_names (Iterable[str]): The names of roles to assign to the user.
            check_user_exists (bool, optional): Whether to verify user exists before setting roles. Defaults to True.
            check_valid_role_names (bool, optional): Whether to validate role names exist. Defaults to True.

        HTTP Error:
            404 (Not Found): User with the given id is not found.
            400 (Bad Request): One or more role names are invalid.
            409 (Conflict): Database conflict occurred during role assignment.
            500 (Internal Server Error): An exception has occurred.
        """
        if check_user_exists and await UserRepository.QueryFirst(session, select(User).where(User.id==user_id)) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Cannot find an user with id '{user_id}'")
        role_names_set = set(role_names)
        
        if check_valid_role_names:
            invalid_role_names = await UserRoleRepository.QueryAll(session, select(UserRole))
            invalid_role_names = role_names_set.difference(role.name for role in invalid_role_names)

            if invalid_role_names:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"{', '.join(f'{name}' for name in invalid_role_names)} are not valid role names!")
        
        try:
            await UserRoleRepository.DeleteAllRolesFromUser(session, user_id, commit=False)
            await UserRoleRepository.AddRolesToUser(session, user_id, role_names_set, commit=True)
        except IntegrityError as e:
            Logger.LogException(e, "UserRoleService.SetUserRoles: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Set roles causing a database conflict to occurred!")
        except Exception as e:
            Logger.LogException(e, "UserRoleService.SetUserRoles: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")


class UserPermissionService:
    """The User Permission Service class, provides static methods for managing user permissions.
    Notice that, Exception can occurred, but converted to HTTP Exception."""
    
    @staticmethod
    async def GetUserPermissions(session: AsyncSession, user_id: str,
                                 check_user_exists: bool = True) -> List[UserPermission]:
        """Query all permissions associated with a specific user.

        Args:
            session (AsyncSession): The database session to query.
            user_id (str): The user id to query permissions for.
            check_user_exists (bool, optional): Whether to verify user exists before querying permissions. Defaults to True.

        HTTP Error:
            404 (Not Found): User with the given id is not found.
            500 (Internal Server Error): An exception has occurred.

        Returns:
            List[UserPermission]: A list of permissions associated with the user.
        """
        if check_user_exists and await UserRepository.QueryFirst(session, select(User).where(User.id==user_id)) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Cannot find an user with id '{user_id}'")

        try:
            return await UserPermissionRepository.GetPermissionsOfUser(session, user_id)
        except Exception as e:
            Logger.LogException(e, "UserPermissionService.GetUserPermissions: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")

    @staticmethod
    async def CheckUserPermission(session: AsyncSession, user_id: str, permission_name: str,
                                  check_user_exists: bool = True) -> bool:
        """Check if a specific user has a particular permission.

        Args:
            session (AsyncSession): The database session to query.
            user_id (str): The user id to check permission for.
            permission_name (str): The name of the permission to check.
            check_user_exists (bool, optional): Whether to verify user exists before checking permission. Defaults to True.

        HTTP Error:
            404 (Not Found): User with the given id is not found.
            500 (Internal Server Error): An exception has occurred.

        Returns:
            bool: True if the user has the specified permission, False otherwise.
        """
        if check_user_exists and await UserRepository.QueryFirst(session, select(User).where(User.id==user_id)) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Cannot find an user with id '{user_id}'")

        try:
            return await UserPermissionRepository.CheckPermissionOfUser(session, user_id, permission_name)
        except Exception as e:
            Logger.LogException(e, "UserPermissionService.CheckUserPermission: An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")