import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from typing import Optional
from utils import Logger, Config

class Database:
    """The Database class, provide static method to managing the backend database."""
    
    SessionFactory: Optional[async_sessionmaker[AsyncSession]] = None
    """Use to creating database session."""
    ORMBase: DeclarativeMeta = declarative_base()
    """Base class for all database ORM."""
    
    __engine: Optional[AsyncEngine] = None
    
    @staticmethod
    async def Connect() -> bool:
        """Connect to the database.

        Returns:
            bool: True on success, False on failure.
        """
        #* Check if already connected
        if Database.__engine is not None:
            Logger.LogWarning("Database.Connect: Database is already connected! Will do nothing.")
            return True
        
        database_url = os.getenv("DATABASE_URL", None)
        if not database_url:
            Logger.LogError("Database.Connect: No database path specified in the environment variable!")
            return False
        
        try:
            Database.__engine = create_async_engine(
                url=database_url,
                connect_args=Config.GetConfig("database.connectArgs", {}),
                pool_size=int(Config.GetConfig("database.poolSize", 32)),
                max_overflow=int(Config.GetConfig("database.maxOverflow", 32))
            )
            Database.SessionFactory = async_sessionmaker(bind=Database.__engine,
                                                         expire_on_commit=Config.GetConfig("database.session.expireOnCommit", False),
                                                         class_=AsyncSession)

            #! Remove on change database from SQLite
            @event.listens_for(Database.__engine.sync_engine, "connect")
            def _enable_foreign_keys(dbapi_connection, connection_record):
                dbapi_connection.execute("PRAGMA foreign_keys=ON;")
            
            
            return True
        except Exception as e:
            if Database.__engine:
                await Database.__engine.dispose()
            
            Database.__engine = None
            Database.SessionFactory = None
            
            Logger.LogException(e, "Database: Failed to connect to the database")
            return False
    
    @staticmethod
    async def Disconnect() -> bool:
        """Disconnect from the database.

        Returns:
            bool: True on success, False on failure.
        """
        #* Check if not connected
        if Database.__engine is None:
            Logger.LogWarning("Database.Disconnect: Database is not connected! Will do nothing.")
            return True
        
        try:
            await Database.__engine.dispose()
            
            Database.__engine = None
            Database.SessionFactory = None
            
            return True
        except Exception as e:
            Database.__engine = None
            Database.SessionFactory = None
            
            Logger.LogException(e, "Database: Failed to disconnect from the database")
            
            return False
        
    @staticmethod
    def IsConnected() -> bool:
        """Check if the database is connected.

        Returns:
            bool: True if connected, False if not.
        """
        return Database.__engine is not None
    
    @staticmethod
    def GetSession() -> Optional[AsyncSession]:
        """Get a database async database session, make sure to close after used.

        Returns:
            AsyncSession | None: The database session to use, or None if not connected.

        Raises:
            Exception: If the database is not connected.
        """
        if Database.SessionFactory is None:
            Logger.LogWarning("Database.GetSession: Database is not connected!")
            return None
        
        return Database.SessionFactory()
        
    @staticmethod
    async def CreateTables() -> bool:
        if Database.__engine is None:
            Logger.LogError("Database.CreateTables: Database is not connected!")
            return False
        try:
            async with Database.__engine.begin() as conn:
                await conn.run_sync(Database.ORMBase.metadata.create_all)
            return True
        except Exception as e:
            Logger.LogException(e, "Database: Failed to create tables")
            return False