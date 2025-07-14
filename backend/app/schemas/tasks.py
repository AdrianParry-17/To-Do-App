import datetime, schemas
from models.tasks import TaskStatus, TaskVisibility
from typing import Annotated, Optional
from pydantic import BaseModel, Field, StringConstraints

IDConstraints = Annotated[str, StringConstraints(strip_whitespace=True, pattern="^[A-Za-z0-9-]*$", max_length=64)]

class TaskAttributesSchema(BaseModel):
    """The schema use for TaskAttributes"""
    name: Annotated[Optional[str], StringConstraints(strip_whitespace=True, max_length=256)] = Field(None, title="Task Name")
    status: TaskStatus = Field(TaskStatus.NotStarted, title="Task Status")
    visibility: TaskVisibility = Field(TaskVisibility.Private, title="Task Visibility")

class TaskResponseSchema(BaseModel):
    """The schema use for response Task."""
    id: IDConstraints = Field(title="Task ID")
    creator_id: IDConstraints = Field(title="Task Owner ID")
    attributes: TaskAttributesSchema = Field(title="Task Attributes")
    
    createdTime: datetime.datetime = Field(title="Created Time", description="The time that the Task was created.")
    updatedTime: datetime.datetime = Field(title="Updated Time", description="The latest time that the Task was updated.")
    version: Annotated[int, Field(ge=0)] = Field(0, title="Version", description="The version of the Task, starting from 1, equal to the Number Of Updated + 1")

class TaskCreateSchema(BaseModel):
    """The schema use for request Task creating."""
    creator_id: IDConstraints = Field(title="Task Owner ID")
    
    name: Annotated[Optional[str], StringConstraints(strip_whitespace=True, max_length=256)] = Field(None, title="Task Name")
    status: TaskStatus = Field(TaskStatus.NotStarted, title="Task Status")
    visibility: TaskVisibility = Field(TaskVisibility.Private, title="Task Visibility")
    
class TaskUpdateSchema(BaseModel):
    """The schema use for request Task updating."""
    name: Annotated[Optional[str], StringConstraints(strip_whitespace=True, max_length=256)] = Field(None, title="Task Name")
    status: Optional[TaskStatus] = Field(None, title="Task Status")
    visibility: Optional[TaskVisibility] = Field(None, title="Task Visibility")
    
    
class TaskObjectResponseSchema(schemas.ObjectResponseSchema[TaskResponseSchema]):
    """The schema for API response a single Task object."""
    pass

class TaskCollectionsResponseSchema(schemas.CollectionsResponseSchema[TaskResponseSchema]):
    """The schema for API response multiple Task object."""
    pass