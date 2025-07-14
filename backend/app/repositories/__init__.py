from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, Select, Delete
from typing import TypeVar, Generic, Tuple, Optional, List, Iterable

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """The Base Repository class, provides static methods for interacting directly with database tables.
    Note that, exceptions are not handled!"""
    
    @staticmethod
    async def QueryFirst(session: AsyncSession, stmt: Select[Tuple[T]]) -> Optional[T]:
        """Perform a query using the given statement, then return the first result that matched the query.

        Args:
            session (AsyncSession): The database session to query.
            stmt (Select[Tuple[T]]): The query statement.

        Returns:
            Optional[T]: The first result that match the query, or None if there're none.
        """
        return (await session.execute(stmt)).scalar()
    
    @staticmethod
    async def QueryAll(session: AsyncSession, stmt: Select[Tuple[T]]) -> List[T]:
        """Perform a query using the given statement, then return all results that match the query.

        Args:
            session (AsyncSession): The database session to query.
            stmt (Select[Tuple[T]]): The query statement.

        Returns:
            List[T]: A list of all results that matched, or an empty list if there're none.
        """
        return list((await session.execute(stmt)).scalars().all())
    
    @staticmethod
    async def Delete(session: AsyncSession, stmt: Delete[Tuple[T]]) -> None:
        """Perform a delete operation using the given statement.

        Args:
            session (AsyncSession): The database session to delete from.
            stmt (Delete[Tuple[T]]): The delete statement.
        """
        await session.execute(stmt)
        
    @staticmethod
    async def Add(session: AsyncSession, item: T, commit: bool = True) -> T:
        """Add an item to the database.

        Args:
            session (AsyncSession): The database session to add.
            item (T): The item to add.
            commit (bool, optional): If True, will commit to the database and refresh the item. Defaults to True.

        Returns:
            T: The given item.
        """
        session.add(item)
        if commit:
            await session.commit()
            await session.refresh(item)
        
        return item
    
    @staticmethod
    async def AddMany(session: AsyncSession, items: Iterable[T], commit: bool = True) -> None:
        """Add multiple items to the database.

        Args:
            session (AsyncSession): The database session to add to.
            items (Iterable[T]): The list of items to add.
            commit (bool, optional): If True, will also commit to the database. Defaults to True.
        """
        session.add_all(items)
        if commit:
            await session.commit()
