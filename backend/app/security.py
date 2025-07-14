import jose.jwt, datetime, os
from sqlalchemy import select, delete
from database import Database
from models.users import RolePermissionRelationTable, UserPermission, UserRole
from repositories.users import UserRepository, UserAttributesRepository, UserPermissionRepository,\
    UserRoleRepository
from passlib.context import CryptContext
from utils import Logger, Config, SaferJsonObjectParse, GetQueryDictByPath
from typing import Any, Optional, Dict

class PasswordTools:
    """Provide static method for working with password hash and verifying."""
    __passwordContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    @staticmethod
    def HashPassword(plainPassword: str) -> Optional[str]:
        """Generate a hashed password from the given plain password.
        Will return None if the given plain password is evaluated to False, or exception occurred."""
        if not plainPassword:
            return None
        try:
            return PasswordTools.__passwordContext.hash(plainPassword)
        except Exception as e:
            Logger.LogException(e, "PasswordTools.HashPassword: An exception has occurred!")
            return None

    @staticmethod
    def VerifyPassword(checkPassword: str, passwordHash: str) -> bool:
        """Verify if the given plain password match the given password hash.
        Will also return False if exception occurred, or either given check password or password hash
        is evaluated to False."""
        if not checkPassword or not passwordHash:
            return False
        try:
            return PasswordTools.__passwordContext.verify(checkPassword, passwordHash)
        except Exception as e:
            Logger.LogException(e, "PasswordTools.VerifyPassword: An exception has occurred!")
            return False

class AuthTools:
    """Provide static method for authentication/authorization."""
    
    @staticmethod
    def GenerateJWT(data: Dict[str, Any]) -> Optional[str]:
        """Generate a JWT token from the given data.
        
        Args:
            data (Dict[str, Any]): The data to encode in the JWT token.
            
        Returns:
            Optional[str]: The generated JWT token, or None if an error occurred.
        """
        secret_key = os.getenv("JWT_SECRET_KEY")
        if not secret_key:
            Logger.LogError("AuthTools.GenerateJWT: No secret key provided in the environment variable!")
            return None
    
        algorithm = Config.GetConfig("security.jwtAlgorithm", "HS256")
        access_token_expire_time = max(Config.GetConfig("security.accessTokenExpireTime", 3600), 1)
        
        try:
            to_encode = data.copy()
            expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=access_token_expire_time)
            to_encode.update({"exp": expire})
            return jose.jwt.encode(to_encode, secret_key, algorithm=algorithm)
        except Exception as e:
            Logger.LogException(e, "AuthTools.GenerateJWT: An exception has occurred")
            return None

    @staticmethod
    def VerifyJWT(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token.
        
        Args:
            token (str): The JWT token to verify and decode.
            
        Returns:
            Optional[Dict[str, Any]]: The decoded token data if valid, None otherwise.
        """
        secret_key = os.getenv("JWT_SECRET_KEY")
        if not secret_key:
            Logger.LogError("AuthTools.GenerateJWT: No secret key provided in the environment variable!")
            return None
    
        algorithm = Config.GetConfig("security.jwtAlgorithm", "HS256")
        
        try:
            return jose.jwt.decode(token, secret_key, algorithms=[algorithm])
        except jose.JWTError as e:
            Logger.LogException(e, "AuthTools.VerifyJWT: Invalid token")
            return None
        except Exception as e:
            Logger.LogException(e, "AuthTools.VerifyJWT: An exception has occurred")
            return None
        
class Permissions:
    """Provide static method for permissions."""

    OPTIONS_NAME_SEPERATOR = '.'
    """The seperator between options and sub-options name (ex: logging.name -> The 'name' options of the 'logging' category)."""
    PERMISSION_FILE_PATH = os.path.join('data', 'configs', 'permissions.json')
    """The path of the global config file."""
    
    __options_data: Optional[Dict[str, Any]] = None
    
    @staticmethod
    async def Initialize() -> bool:
        """Initialize the Permission class and syncing the Permission/Roles database tables.

        Returns:
            bool: True on success, false on failure.
        """
        session = Database.GetSession()
        if not session:
            Logger.LogError("Permissions.Initialize: Database are not connected!")
            return False
        
        try:
            data: Dict[str, Any] = {}
            with open(Permissions.PERMISSION_FILE_PATH, 'r', encoding='utf-8') as f:
                data = SaferJsonObjectParse(f.read())
            
            permissions = data.get('permissions', [])
            roles = data.get('roles', {})
            options = data.get('options', {})
            
            if not isinstance(permissions, list) or not isinstance(roles, dict) or not isinstance(options, dict):
                Logger.LogError("Permissions.Initialize: Failed to read permission files (wrong format)!")
                return False
            
            if any(not isinstance(val, list) for val in roles.values()) or any(not isinstance(key, str) for key in roles.keys()):
                Logger.LogError("Permissions.Initialize: Failed to read permission files (wrong format)!")
                return False
            
            #* Options
            
            Permissions.__options_data = { str(k):v for k, v in options.items() }
                
            #* Permissions
            
            permissions = set(str(perm) for perm in permissions)
            curr_permissions = set(str(perm.name) for perm in (await UserPermissionRepository.QueryAll(session, select(UserPermission))))
            
            remove_perms = curr_permissions.difference(permissions)
            add_perms = permissions.difference(curr_permissions)
            
            if remove_perms:
                Logger.LogInfo(f"Permissions.Initialize: Removing {len(remove_perms)} permissions...")
                await UserPermissionRepository.Delete(session, delete(UserPermission).where(UserPermission.name.in_(remove_perms)))
                Logger.LogInfo(f"Permissions.Initialize: Removed {len(remove_perms)} permissions (" +
                               ", ".join(remove_perms) + ")")
            
            if add_perms:
                Logger.LogInfo(f"Permissions.Initialize: Adding {len(add_perms)} permissions...")
                await UserPermissionRepository.AddMany(session, (UserPermission(name=perms) for perms in add_perms), commit=False)
                Logger.LogInfo(f"Permissions.Initialize: Added {len(add_perms)} permissions (" +
                               ", ".join(add_perms) + ")")
            #* Roles
            
            roles_name = set(str(role) for role in roles.keys())
            curr_roles_name = set(str(role.name) for role in (await UserRoleRepository.QueryAll(session, select(UserRole))))
            
            remove_roles_name = curr_roles_name.difference(roles_name)
            add_roles_name = roles_name.difference(curr_roles_name)
            
            if remove_roles_name:
                Logger.LogInfo(f"Permissions.Initialize: Removing {len(remove_roles_name)} roles...")
                await UserRoleRepository.Delete(session, delete(UserRole).where(UserRole.name.in_(remove_roles_name)))
                Logger.LogInfo(f"Permissions.Initialize: Removed {len(remove_roles_name)} roles (" +
                               ", ".join(remove_roles_name) + ")")
            
            if add_roles_name:
                Logger.LogInfo(f"Permissions.Initialize: Adding {len(add_roles_name)} roles...")
                await UserRoleRepository.AddMany(session, (UserRole(name=role) for role in add_roles_name))
                Logger.LogInfo(f"Permissions.Initialize: Added {len(add_roles_name)} roles (" +
                               ", ".join(add_roles_name) + ")")
            
            for role in roles_name:
                role_perms = set(str(perm) for perm in roles[role] if perm in permissions)
                curr_role_perms = set(str(perm.name) for perm in (await UserPermissionRepository.GetPermissionsOfRole(session, role)))
                
                remove_role_perms = curr_role_perms.difference(role_perms)
                add_role_perms = role_perms.difference(curr_role_perms)
                
                if remove_role_perms:
                    Logger.LogInfo(f"Permissions.Initialize: Removing {len(remove_role_perms)} permissions for role '{role}'...")
                    await UserPermissionRepository.DeletePermissionsOfRole(session, role, remove_role_perms, commit=False)
                    Logger.LogInfo(f"Permissions.Initialize: Removed {len(remove_role_perms)} permissions for role '{role}' (" +
                               ", ".join(remove_role_perms) + ")")
                
                if add_role_perms:
                    Logger.LogInfo(f"Permissions.Initialize: Adding {len(add_role_perms)} permissions for role '{role}'...")
                    await UserPermissionRepository.AddPermissionsOfRole(session, role, add_role_perms, commit=False)
                    Logger.LogInfo(f"Permissions.Initialize: Added {len(add_role_perms)} permissions for role '{role}' (" +
                               ", ".join(add_role_perms) + ")")
            
            await session.commit()
            
            return True
        except Exception as e:
            Logger.LogException(e, "Permissions.Initialize: An exception has occurred")
            await session.rollback()
            return False
        
        finally:
            await session.close()
    
    @staticmethod
    def GetOptions(option_name: str, default=None) -> Any:
        """Get the options value from the given options name, or return a default value if not match.\n
        Seperate by '.' for suboptions (e.g. ex_options.ex_sub_options)"""
        if Permissions.__options_data is None:
            raise Exception("The Config didn't initialized!")
        return GetQueryDictByPath(Permissions.__options_data, option_name, Permissions.PERMISSION_FILE_PATH, default)