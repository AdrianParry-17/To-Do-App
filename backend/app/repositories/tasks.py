from typing import List, Optional, Tuple
from models.tasks import Task, TaskAttributes
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from utils import Logger

class TaskRepositories:
    """The Task Repositories class, provide static method to interacting directly with the Task related table in the database.
    Note that, exception are not handled!"""
    
    @staticmethod
    async def QueryFirst(session: AsyncSession,
                         stmt: Select[Tuple[Task]]) -> Optional[Task]:
        """Perform a query for Task using the given statement, then return the first Task column that matched the query.

        Args:
            session (AsyncSession): The database session to query.
            stmt (Select[Tuple[Task]]): The query statement.

        Returns:
            Optional[Task]: The first Task that match the query, of None if there're none.
        """
        return (await session.execute(stmt)).scalar()

    @staticmethod
    async def QueryAll(session: AsyncSession,
                       stmt: Select[Tuple[Task]]) -> List[Task]:
        """Perform a query for Task using the given statement, then return all that match the query.

        Args:
            session (AsyncSession): The database session to query.
            stmt (Select[Tuple[Task]]): The query statement.

        Returns:
            List[Task]: A list of all Tasks that matched, or an empty list if there're none.
        """
        return list((await session.execute(stmt)).scalars().all())
    @staticmethod
    async def QueryAttributesFirst(session: AsyncSession,
                                   stmt: Select[Tuple[TaskAttributes]]) -> Optional[TaskAttributes]:
        """Perform a query for TaskAttributes using the given statement, then return the first TaskAttributes column that matched the query.

        Args:
            session (AsyncSession): The database session to query.
            stmt (Select[Tuple[TaskAttributes]]): The query statement.

        Returns:
            Optional[TaskAttributes]: The first TaskAttributes that match the query, of None if there're none.
        """
        return (await session.execute(stmt)).scalar()

    @staticmethod
    async def QueryAttributesAll(session: AsyncSession,
                                 stmt: Select[Tuple[TaskAttributes]]) -> List[TaskAttributes]:
        """Perform a query for TaskAttributes using the given statement, then return all that match the query.

        Args:
            session (AsyncSession): The database session to query.
            stmt (Select[Tuple[TaskAttributes]]): The query statement.

        Returns:
            List[TaskAttributes]: A list of all TaskAttributessthat matched, or an empty list if there're none.
        """
        return list((await session.execute(stmt)).scalars().all())
    
    @staticmethod
    async def AddTask(session: AsyncSession, task: Task, commit: bool = True) -> Task:
        """Add a Task to the database.

        Args:
            session (AsyncSession): The database session to add.
            task (Task): The Task instance to add.
            commit (bool, optional): If True, will commit to the database and refresh the given Task instance. Default to True.

        Returns:
            Task: The given Task.
        """
        session.add(task)
        if commit:
            return await TaskRepositories.UpdateTask(session, task)
        
        return task
    
    @staticmethod
    async def UpdateTask(session: AsyncSession, task: Task) -> Task:
        """Commit the database and refresh the given Task instance.

        Args:
            session (AsyncSession): The database session to update.
            task (Task): The task instance to refresh.

        Returns:
            Task: The given Task instance.
        """
        await session.commit()
        await session.refresh(task)
        
        return task
    
    @staticmethod
    async def DeleteTask(session: AsyncSession, task: Task, commit: bool = True) -> None:
        """Delete the given Task from the database.

        Args:
            session (AsyncSession): The database session to delete.
            task (Task): The task instance to delete.
            commit (bool, optional): If True, will commit to the database. Defaults to True.
        """
        await session.delete(task.attributes)
        await session.delete(task)
        if commit:
            await session.commit()        