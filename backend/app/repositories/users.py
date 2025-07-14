import repositories
from typing import Iterable, List
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import User, UserAttributes, UserRole, UserPermission,\
    UserRoleRelationTable, RolePermissionRelationTable

class UserRepository(repositories.BaseRepository[User]):
    """The User Repository class, provides static methods for interacting directly with the User table in the database.
    Note that, exceptions are not handled!"""
    pass

class UserAttributesRepository(repositories.BaseRepository[UserAttributes]):
    """The User Attributes Repository class, provides static methods for interacting directly with the User Attributes table in the database.
    Note that, exceptions are not handled!"""
    pass

class UserRoleRepository(repositories.BaseRepository[UserRole]):
    """The User Role Repository class, provides static methods for interacting directly with the User Role table in the database.
    Note that, exceptions are not handled!"""
    
    @staticmethod
    async def GetRolesOfUser(session: AsyncSession, user_id: str) -> List[UserRole]:
        """Get all User Roles that a user with the given user id has.

        Args:
            session (AsyncSession): The database session to query.
            user_id (str): The user id to query.

        Returns:
            List[UserRole]: A list of all User Roles that the user has.
        """
        return await UserRoleRepository.QueryAll(session,
            select(UserRole)
            .join(UserRoleRelationTable, UserRole.name==UserRoleRelationTable.roleName)
            .where(UserRoleRelationTable.userId==user_id)
        )
    
    @staticmethod
    async def CheckRoleOfUser(session: AsyncSession, user_id: str, role_name: str) -> bool:
        """Check if a user with the given user id has a User Role with the given role name.

        Args:
            session (AsyncSession): The database session to query.
            user_id (str): The user id to query.
            role_name (str): The role name to check.

        Returns:
            bool: True if the user has the role, False otherwise (also if user does not exist).
        """
        return await UserRoleRepository.QueryFirst(session,
            select(UserRole)
            .join(UserRoleRelationTable, UserRoleRelationTable.roleName==UserRole.name)
            .where(UserRoleRelationTable.userId==user_id, UserRole.name==role_name)
        ) is not None

    @staticmethod
    async def DeleteRolesFromUser(session: AsyncSession, user_id: str, role_names: Iterable[str], commit: bool = True) -> None:
        """Delete roles of an user with the given user id and that in the given list of roles name to delete.

        Args:
            session (AsyncSession): The database session to delete.
            user_id (str): The user id to delete.
            role_names (Iterable[str]): The list of roles name to delete.
            commit (bool, optional): If True, will commit to the database. Defaults to True.
        """
        await session.execute(delete(UserRoleRelationTable)
                              .where(UserRoleRelationTable.userId==user_id,
                                     UserRoleRelationTable.roleName.in_(role_names)))
        if commit:
            await session.commit()
    
    @staticmethod
    async def DeleteAllRolesFromUser(session: AsyncSession, user_id: str, commit: bool = True) -> None:
        """Delete all roles of an user with the given user id.

        Args:
            session (AsyncSession): The database session to delete.
            user_id (str): The user id to delete.
            commit (bool, optional): If True, will commit to the database. Defaults to True.
        """
        await session.execute(delete(UserRoleRelationTable)
                              .where(UserRoleRelationTable.userId==user_id))
        if commit:
            await session.commit()

    @staticmethod
    async def AddRolesToUser(session: AsyncSession, user_id: str, role_names: Iterable[str], commit: bool = True) -> None:
        """Add roles to an user with the given user id and list of roles name to add.

        Args:
            session (AsyncSession): The database session to add.
            user_id (str): The user id to add.
            role_names (Iterable[str]): The list of roles name to add.
            commit (bool, optional): If True, will commit to the database. Defaults to True.
        """
        session.add_all((UserRoleRelationTable(userId=user_id, roleName=role) for role in role_names))
        if commit:
            await session.commit()

class UserPermissionRepository(repositories.BaseRepository[UserPermission]):
    """The User Permission Repository class, provides static methods for interacting directly with the User Permission table in the database.
    Note that, exceptions are not handled!"""

    @staticmethod
    async def GetPermissionsOfRole(session: AsyncSession, role_name: str) -> List[UserPermission]:
        """Get all User Permissions that a User Role with the given role name has.

        Args:
            session (AsyncSession): The database session to query.
            role_name (str): The role name to query.

        Returns:
            List[UserPermission]: A list of all User Permissions that the role has.
        """
        return await UserPermissionRepository.QueryAll(session,
            select(UserPermission)
            .join(RolePermissionRelationTable, RolePermissionRelationTable.permissionName==UserPermission.name)
            .where(RolePermissionRelationTable.roleName==role_name)
        )
    
    @staticmethod
    async def CheckPermissionOfRole(session: AsyncSession, role_name: str, permission_name: str) -> bool:
        """Check if a User Role with the given role name has a User Permission with the given permission name.

        Args:
            session (AsyncSession): The database session to query.
            role_name (str): The role name to query.
            permission_name (str): The permission name to check.

        Returns:
            bool: True if the role has the permission, False otherwise (also if role does not exist).
        """
        return await UserPermissionRepository.QueryFirst(session,
            select(UserPermission)
            .join(RolePermissionRelationTable, RolePermissionRelationTable.permissionName==UserPermission.name)
            .where(RolePermissionRelationTable.roleName==role_name, UserPermission.name==permission_name)
        ) is not None
    
    @staticmethod
    async def GetPermissionsOfUser(session: AsyncSession, user_id: str) -> List[UserPermission]:
        """Get all User Permissions that a user with the given user id has.

        Args:
            session (AsyncSession): The database session to query.
            user_id (str): The user id to query.

        Returns:
            List[UserPermission]: A list of all User Permissions that the user has.
        """
        return await UserPermissionRepository.QueryAll(session,
            select(UserPermission)
            .join(RolePermissionRelationTable, RolePermissionRelationTable.permissionName==UserPermission.name)
            .join(UserRoleRelationTable, RolePermissionRelationTable.roleName==UserRoleRelationTable.roleName)
            .where(UserRoleRelationTable.userId==user_id)
        )
    
    @staticmethod
    async def CheckPermissionOfUser(session: AsyncSession, user_id: str, permission_name: str) -> bool:
        """Check if a user with the given user id has a User Permission with the given permission name.

        Args:
            session (AsyncSession): The database session to query.
            user_id (str): The user id to query.
            permission_name (str): The permission name to check.

        Returns:
            bool: True if the user has the permission, False otherwise (also if user does not exist).
        """
        return await UserPermissionRepository.QueryFirst(session,
            select(UserPermission)
            .join(RolePermissionRelationTable, RolePermissionRelationTable.permissionName==UserPermission.name)
            .join(UserRoleRelationTable, RolePermissionRelationTable.roleName==UserRoleRelationTable.roleName)
            .where(UserRoleRelationTable.userId==user_id, UserPermission.name==permission_name)
        ) is not None
        
    @staticmethod
    async def DeletePermissionsOfRole(session: AsyncSession, role_name: str, permission_names: Iterable[str], commit: bool = True) -> None:
        """Delete permissions of a role with the given role name and list of permissions name to delete.

        Args:
            session (AsyncSession): The database session to delete.
            role_name (str): The role name to delete.
            permission_names (Iterable[str]): The list of permissions name to delete.
            commit (bool, optional): If True, will commit to the database. Defaults to True.
        """
        await session.execute(delete(RolePermissionRelationTable)
                              .where(RolePermissionRelationTable.roleName==role_name,
                                     RolePermissionRelationTable.permissionName.in_(permission_names)))
        if commit:
            await session.commit()

    @staticmethod
    async def AddPermissionsOfRole(session: AsyncSession, role_name: str, permission_names: Iterable[str], commit: bool = True) -> None:
        """Add permissions to a role with the given role name and list of permissions name to add.

        Args:
            session (AsyncSession): The database session to add.
            role_name (str): The role name to add.
            permission_names (Iterable[str]): The list of permissions name to add.
            commit (bool, optional): If True, will commit to the database. Defaults to True.
        """
        session.add_all((RolePermissionRelationTable(roleName=role_name, permissionName=perm) for perm in permission_names))
        if commit:
            await session.commit()