import datetime, enum
from database import Database
from sqlalchemy import String, ForeignKey, DateTime, Integer,\
    Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column

class TaskStatus(str, enum.Enum):
    """The Task Status enum to define the status of a Task."""
    NotStarted = "not_started",
    InProgress = "in_progress",
    Completed = "completed",
    Cancelled = "cancelled"

class TaskVisibility(str, enum.Enum):
    """The Task Visibility enum to define the visibility of a Task."""
    Public = "public",
    Private = "private"

class Task(Database.ORMBase):
    """The Task class, provide an ORM class for 'task' table in backend database."""
    __tablename__ = "task"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    creatorId: Mapped[str] = mapped_column(String(64),
                                           ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
                                           nullable=False, index=True)

    createdTime: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    updatedTime: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now())
    version: Mapped[int] = mapped_column(Integer, default=1)

    attributes: Mapped["TaskAttributes"] = relationship("TaskAttributes", back_populates='task', uselist=False, lazy='selectin')
    
class TaskAttributes(Database.ORMBase):
    """The Task Attributes class, provide an ORM class for 'task_attributes' table in backend database.
    It's contain the attributes, of a Task."""
    __tablename__ = "task_attributes"
    
    taskId: Mapped[str] = mapped_column(String(64), ForeignKey('task.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    
    name: Mapped[str] = mapped_column(String(256), nullable=True)
    visibility: Mapped[TaskVisibility] = mapped_column(SQLAlchemyEnum(TaskVisibility, native_enum=False), nullable=False, default=TaskVisibility.Private)
    status: Mapped[TaskStatus] = mapped_column(SQLAlchemyEnum(TaskStatus, native_enum=False), nullable=False, default=TaskStatus.NotStarted)
    
    task: Mapped[Task] = relationship("Task", back_populates='attributes', lazy='selectin')