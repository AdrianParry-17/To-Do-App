import datetime
from schemas.tasks import TaskCreateSchema, TaskResponseSchema, TaskCollectionsResponseSchema,\
    TaskUpdateSchema, TaskObjectResponseSchema, TaskAttributesSchema
from models.tasks import Task, TaskAttributes, TaskVisibility
from repositories.tasks import TaskRepositories
from services.users import UserService
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from utils import Logger, GenerateUUID
from typing import List

class TaskServices:
    """The Task Services class, provide static method to working with Task in the database.
    Notice that, HTTP Exception can occurred."""
    
    @staticmethod
    async def GetTaskFromID(session: AsyncSession, task_id: str) -> Task:
        """Query a Task with the given id.

        Args:
            session (AsyncSession): The database session to query.
            task_id (str): The task id to query.

        HTTP Error:
            404 (Not Found): Task with the given id is not found.
            500 (Internal Server Error): An exception has occurred.

        Returns:
            Task: The result Task with the given id.
        """
        result = None
        try:
            result = await TaskRepositories.QueryFirst(session, select(Task).where(Task.id==task_id))
        except Exception as e:
            Logger.LogException(e, "TaskServices.GetTaskFromID - An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")
        
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Cannot find a task with id '{task_id}'")
            
        return result
    
    @staticmethod
    async def ListUserTasks(session: AsyncSession, user_id: str,
                            list_non_visibility: bool = False,
                            offset: int = 0, limit: int = 10) -> List[Task]:
        """
        Query a list of Tasks of a User with optional filtering, and supports pagination.

        Args:
            session (AsyncSession): The database session to query.
            user_id (str): The user id to query.
            list_non_visibility (bool, optional): If True, will list all tasks and not ignore non-visible one. Default to False.
            offset (int, optional): The number of records to skip for pagination. Defaults to 0.
            limit (int, optional): The maximum number of records to return. Defaults to 10.

        HTTP Error:
            500 (Internal Server Error): An exception has occurred during the query.

        Returns:
            List[Task]: A list of Task.
        """
        stmt = select(Task).join(TaskAttributes, Task.id==TaskAttributes.taskId)
        stmt = stmt.where(Task.creatorId==user_id)
        
        # Apply filter
        if not list_non_visibility:
            stmt = stmt.where(TaskAttributes.visibility==TaskVisibility.Public)
        
        # Apply offset and limit
        stmt = stmt.offset(max(offset, 0)).limit(max(1, limit))

        try:
            return await TaskRepositories.QueryAll(session, stmt)
        except Exception as e:
            Logger.LogException(e, "TaskServices.ListTasks - An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")
    
    @staticmethod
    async def CreateTask(session: AsyncSession, info: TaskCreateSchema) -> Task:
        """
        Create a new task in the database.

        Args:
            session (AsyncSession): The database session to use for the operation.
            info (TaskCreateSchema): The schema containing task creation information.

        HTTP Error:
            404 (Not Found): If an user with the given owner id is not found.
            409 (Conflict): If creating causing a database conflict.
            500 (Internal Server Error): If an exception occurs during the creation process.

        Returns:
            Task: The newly created Task object.
        """
        
        # Check if user with the id exist (auto throw exception 404 or 500).
        user = await UserService.FromID(session, info.creator_id)
        
        task_id = GenerateUUID()
        
        task = Task(id=task_id, creatorId=info.creator_id)
        task_attributes = TaskAttributes(name=info.name, status=info.status, visibility=info.visibility)
        task.attributes = task_attributes
        
        try:
            return await TaskRepositories.AddTask(session=session, task=task, commit=True)
        except IntegrityError as e:
            Logger.LogException(e, "TaskServices.CreateTask - An exception has occurred")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Create causing a database conflict to occurred!")
        except Exception as e:
            Logger.LogException(e, "TaskServices.CreateTask - An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")

    @staticmethod
    async def UpdateTask(session: AsyncSession, task: Task,
                         update_info: TaskUpdateSchema,
                         version_update: bool = True) -> Task:
        """
        Update an existing task in the database.

        Args:
            session (AsyncSession): The database session to use for the operation.
            task (Task): The Task object with updated information.
            version_update (bool, optional): If True, will also assign current time to 'updatedTime' and increase 'version' by 1. Default to True.

        HTTP Error:
            409 (Conflict): If there's an database conflict happened update.
            500 (Internal Server Error): If an exception occurs during the update process, or failed.

        Returns:
            Task: The updated Task object.
        """
        
        try:
            if update_info.name:
                task.name = update_info.name
            if update_info.status is not None:
                task.attributes.status = update_info.status
            if update_info.visibility is not None:
                task.attributes.visibility = update_info.visibility
                
            if version_update:
                task.updatedTime = datetime.datetime.now()
                task.version += 1
                
            return await TaskRepositories.UpdateTask(session, task)
        except IntegrityError as e:
            Logger.LogException(e, "TaskServices.UpdateTask - An exception has occurred")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Update causing a database conflict to occurred!")
        except Exception as e:
            Logger.LogException(e, "TaskServices.UpdateTask - An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")
            
    @staticmethod
    async def DeleteTaskWithID(session: AsyncSession, task_id: str) -> None:
        """
        Delete a task from the database by their task ID.

        Args:
            session (AsyncSession): The database session to use for the operation.
            task_id (str): The ID of the task to delete.

        HTTP Error:
            404 (Not Found): If a task with the given ID does not exist.
            500 (Internal Server Error): If an exception occurs during the deletion process.

        Returns:
            None
        """
        task = await TaskRepositories.QueryFirst(session, select(Task).where(Task.id==task_id))
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Cannot find a task with id '{task_id}'!")
        
        try:
            await TaskRepositories.DeleteTask(session, task, True)
        except Exception as e:
            Logger.LogException(e, "TaskServices.DeleteTaskWithID - An exception has occurred")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"{type(e).__name__}: {str(e)}")
