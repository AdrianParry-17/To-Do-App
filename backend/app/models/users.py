import datetime, enum
from database import Database
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String,\
    Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column

class UserVisibility(str, enum.Enum):
    """The Task Visibility enum to define the visibility of a Task."""
    Private = "private"
    Public = "public"

class UserRole(Database.ORMBase):
    """The User Role class, provide an ORM class for 'user_role' table.\n
    It's contain the roles, for User."""
    __tablename__ = "user_role"
    
    name: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)

    createdTime: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    updatedTime: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    version: Mapped[int] = mapped_column(Integer, default=1)

class UserPermission(Database.ORMBase):
    """The User Permission class, provide an ORM class for 'user_permission' table.\n
    It's contain the permissions, for User."""
    __tablename__ = "user_permission"
    
    name: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)

    createdTime: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    updatedTime: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    version: Mapped[int] = mapped_column(Integer, default=1)

class RolePermissionRelationTable(Database.ORMBase):
    """The Role Permission Relation Table class, provide an ORM class for 'role_permission_relation_table' table.\n
    For provide a many-to-many relationship of 'user_role' and 'user_permission'."""
    __tablename__ = "role_permission_relation_table"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    roleName: Mapped[str] = mapped_column(String(64),
                                          ForeignKey('user_role.name', ondelete='CASCADE', onupdate='CASCADE'),
                                          nullable=False, unique=False, index=True)
    permissionName: Mapped[str] = mapped_column(String(64),
                                                ForeignKey('user_permission.name', ondelete='CASCADE', onupdate='CASCADE'),
                                                nullable=False, unique=False, index=True)

class User(Database.ORMBase):
    """The User class, provide an ORM class for 'user' table in the backend database."""
    __tablename__ = "user"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    username: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    passwordHash: Mapped[str] = mapped_column(String(128), nullable=False)
    
    createdTime: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    updatedTime: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    attributes: Mapped["UserAttributes"] = relationship("UserAttributes", back_populates="user", uselist=False, lazy='selectin')
    
class UserAttributes(Database.ORMBase):
    """The User Attributes class, provide an ORM class for 'user_attributes' table in the backend database.\n
    It's contain the attributes, of an User."""
    __tablename__ = "user_attributes"
    
    userId: Mapped[str] = mapped_column(String(64), ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)    
    
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=True)
    visibility: Mapped[UserVisibility] = mapped_column(SQLAlchemyEnum(UserVisibility, native_enum=False), nullable=False, default=UserVisibility.Private)
    
    user: Mapped["User"] = relationship("User", back_populates="attributes", lazy='selectin')

class UserRoleRelationTable(Database.ORMBase):
    """The User Role Relation Table class, provide an ORM class for 'user_role_relation_table' table.\n
    For provide a many-to-many relationship of 'user' and 'user_role'."""
    __tablename__ = "user_role_relation_table"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    userId: Mapped[str] = mapped_column(String(64),
                                        ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                                        nullable=False, unique=False, index=True)
    roleName: Mapped[str] = mapped_column(String(64),
                                          ForeignKey('user_role.name', ondelete='CASCADE', onupdate='CASCADE'),
                                          nullable=False, unique=False, index=True)