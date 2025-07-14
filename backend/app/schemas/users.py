import datetime, schemas

from click import Option
from models.users import UserVisibility
from typing import Annotated, Optional, List
from pydantic import BaseModel, EmailStr, Field, StringConstraints

UserIDConstraints = Annotated[str, StringConstraints(strip_whitespace=True, pattern="^[A-Za-z0-9-]*$", max_length=64)]
UsernameConstraints = Annotated[str, StringConstraints(strip_whitespace=True, pattern="^[A-Za-z0-9_]*$", min_length=8, max_length=32)]
PasswordConstraints = Annotated[str, StringConstraints(strip_whitespace=False, pattern=".*[A-Z].*[a-z].*[0-9].*", min_length=8)]

OptionalUsernameConstraints = Annotated[Optional[str], StringConstraints(strip_whitespace=True, pattern="^[A-Za-z0-9_]*$", min_length=8, max_length=32)]
OptionalPasswordConstraints = Annotated[Optional[str], StringConstraints(strip_whitespace=False, pattern=".*[A-Z].*[a-z].*[0-9].*", min_length=8)]

class UserAttributesSchema(BaseModel):
    """The schema use for UserAttributes"""
    email: Optional[EmailStr] = Field(None, title="User Email")
    visibility: UserVisibility = Field(title="Visibility")

class UserResponseSchema(BaseModel):
    """The schema use for response User."""
    id: UserIDConstraints = Field(title="User ID")
    username: UsernameConstraints = Field(title="Username")
    attributes: UserAttributesSchema = Field(title="User Attributes")
    
    createdTime: datetime.datetime = Field(title="Created Time", description="The time that the User was created.")
    updatedTime: datetime.datetime = Field(title="Updated Time", description="The latest time that the User was updated.")
    version: Annotated[int, Field(ge=0)] = Field(0, title="Version", description="The version of the User, starting from 1, equal to the Number Of Updated + 1")

class UserCreateSchema(BaseModel):
    """The schema use for request User creating."""
    username: UsernameConstraints = Field(title="Username")
    password: PasswordConstraints = Field(title="Password", description="Length must be >= 8, and contain at least an upper, lower and digit characters.")
    roles: List[str] = Field([], title="Roles")
    
    email: Optional[EmailStr] = Field(None, title="User Email")
    visibility: UserVisibility = Field(UserVisibility.Public, title="Visibility")

class UserUpdateSchema(BaseModel):
    """The schema use for request User updating."""
    username: OptionalUsernameConstraints = Field(None, title="Username")
    password: OptionalPasswordConstraints = Field(None, title="Password", description="Length must be >= 8, and contain at least an upper, lower and digit characters.")
    
    email: Optional[EmailStr] = Field(None, title="User Email")
    visibility: Optional[UserVisibility] = Field(None, title="Visibility")
    
class UserRoleResponseSchema(BaseModel):
    """The schema use for response User Role."""
    name: str = Field(title="Role Name")
    
    createdTime: datetime.datetime = Field(title="Created Time", description="The time that the User Role was created.")
    updatedTime: datetime.datetime = Field(title="Updated Time", description="The latest time that the User Role was updated.")
    version: Annotated[int, Field(ge=0)] = Field(0, title="Version", description="The version of the User Role, starting from 1, equal to the Number Of Updated + 1")

class UserPermissionResponseSchema(BaseModel):
    """The schema use for response User Permission."""
    name: str = Field(title="Permission Name")
    
    createdTime: datetime.datetime = Field(title="Created Time", description="The time that the User Permission was created.")
    updatedTime: datetime.datetime = Field(title="Updated Time", description="The latest time that the User Permission was updated.")
    version: Annotated[int, Field(ge=0)] = Field(0, title="Version", description="The version of the User Permission, starting from 1, equal to the Number Of Updated + 1")


class UserObjectResponseSchema(schemas.ObjectResponseSchema[UserResponseSchema]):
    """The schema for API response a single User object."""
    pass

class UserCollectionsResponseSchema(schemas.CollectionsResponseSchema[UserResponseSchema]):
    """The schema for API response multiple User object."""
    pass

class UserRoleObjectResponseSchema(schemas.ObjectResponseSchema[UserRoleResponseSchema]):
    """The schema for API response a single User Role object."""
    pass

class UserRoleCollectionsResponseSchema(schemas.CollectionsResponseSchema[UserRoleResponseSchema]):
    """The schema for API response multiple User Role object."""
    pass

class UserPermissionObjectResponseSchema(schemas.ObjectResponseSchema[UserPermissionResponseSchema]):
    """The schema for API response a single User Permission object."""
    pass

class UserPermissionCollectionsResponseSchema(schemas.CollectionsResponseSchema[UserPermissionResponseSchema]):
    """The schema for API response multiple User Permission object."""
    pass