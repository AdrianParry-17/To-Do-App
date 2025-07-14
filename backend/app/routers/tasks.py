import routers
from utils import Config, Logger
from models.users import User
from models.tasks import Task, TaskVisibility
from schemas import MessageResponseSchema
from schemas.tasks import TaskAttributesSchema, TaskCollectionsResponseSchema,\
    TaskCreateSchema, IDConstraints, TaskObjectResponseSchema, TaskResponseSchema, TaskUpdateSchema
from schemas.errors import ErrorResponseSchema
from services.tasks import TaskServices
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from pydantic import Field

router = APIRouter(prefix="/task", tags=["Task"])

def GetTaskResponseSchema(task: Task) -> TaskResponseSchema:
    """Get the Task Response Schema from the given Task ORM object."""
    return TaskResponseSchema(
        id=task.id,
        creator_id=task.creatorId,
        attributes=TaskAttributesSchema(
            name=task.attributes.name,
            status=task.attributes.status,
            visibility=task.attributes.visibility
        ),
        createdTime=task.createdTime,
        updatedTime=task.updatedTime,
        version=task.version
    )

@router.get(
    "/", name="List User Tasks", status_code=status.HTTP_200_OK,
    response_model=TaskCollectionsResponseSchema,
    dependencies=[Depends(routers.GetCurrentUserID)],
    responses={
        status.HTTP_401_UNAUTHORIZED : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def ListUserTasks(user_id: IDConstraints, list_non_visibility: bool = False,
                        offset: Annotated[int, Field(ge=0, allow_inf_nan=False)] = 0,
                        limit: Annotated[int, Field(ge=1, allow_inf_nan=False)] = 10,
                        session: AsyncSession = Depends(routers.GetDatabaseSession),
                        current_user_id: User = Depends(routers.GetCurrentUserID)):
    
    if list_non_visibility and current_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Only a user can view their own non-visible tasks!")
        
    if limit > Config.GetConfig("database.maxQueryLimit"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The 'limit' of query must be <= {Config.GetConfig("database.maxQueryLimit")}, not {limit}!")

    result = await TaskServices.ListUserTasks(session, user_id,
                                              list_non_visibility=list_non_visibility,
                                              offset=offset, limit=limit)
    return TaskCollectionsResponseSchema(
        data=[GetTaskResponseSchema(task) for task in result]
    )

@router.get(
    "/{task_id}", name="Get Task", status_code=status.HTTP_200_OK,
    response_model=TaskObjectResponseSchema,
    dependencies=[Depends(routers.GetCurrentUserID)],
    responses={
        status.HTTP_401_UNAUTHORIZED : { "model" : ErrorResponseSchema },
        status.HTTP_404_NOT_FOUND : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def GetTask(task_id: IDConstraints,
                  session: AsyncSession = Depends(routers.GetDatabaseSession),
                  user_id: str = Depends(routers.GetCurrentUserID)):
    
    result = await TaskServices.GetTaskFromID(session, task_id)
    if result.creator_id != user_id and result.attributes.visibility not in [TaskVisibility.Public]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="A user can only view their own non-visible tasks!")
    
    return TaskObjectResponseSchema(data=GetTaskResponseSchema(result))

@router.post(
    "/", name="Create Task", status_code=status.HTTP_201_CREATED,
    response_model=TaskObjectResponseSchema,
    dependencies=[Depends(routers.GetCurrentUserID)],
    responses={
        status.HTTP_401_UNAUTHORIZED : { "model" : ErrorResponseSchema },
        status.HTTP_409_CONFLICT : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def CreateTask(info: TaskCreateSchema, session: AsyncSession = Depends(routers.GetDatabaseSession),
                     user_id: str = Depends(routers.GetCurrentUserID)):
    if info.creator_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="A user can only create their own tasks!")
    result = await TaskServices.CreateTask(session, info)
    
    return TaskObjectResponseSchema(data=GetTaskResponseSchema(result))
    
@router.put(
    "/{task_id}", name="Update Task", status_code=status.HTTP_200_OK,
    response_model=TaskObjectResponseSchema,
    dependencies=[Depends(routers.GetCurrentUserID)],
    responses={
        status.HTTP_401_UNAUTHORIZED : { "model" : ErrorResponseSchema },
        status.HTTP_404_NOT_FOUND : { "model" : ErrorResponseSchema },
        status.HTTP_409_CONFLICT : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }   
    }
)
async def UpdateTask(task_id: IDConstraints, info: TaskUpdateSchema, session: AsyncSession = Depends(routers.GetDatabaseSession),
                     user_id: str = Depends(routers.GetCurrentUserID)):
    
    result = await TaskServices.GetTaskFromID(session, task_id)
    if result.creator_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="A user can only update their own tasks!")        

    result = await TaskServices.UpdateTask(session, result, info)
    
    return TaskObjectResponseSchema(data=GetTaskResponseSchema(result))

@router.delete(
    "/{task_id}", name="Delete Task", status_code=status.HTTP_200_OK,
    response_model=MessageResponseSchema[str],
    dependencies=[Depends(routers.GetCurrentUserID)],
    responses={
        status.HTTP_404_NOT_FOUND : { "model" : ErrorResponseSchema },
        status.HTTP_422_UNPROCESSABLE_ENTITY : { "model" : ErrorResponseSchema },
        status.HTTP_500_INTERNAL_SERVER_ERROR : { "model" : ErrorResponseSchema },
        status.HTTP_503_SERVICE_UNAVAILABLE : { "model" : ErrorResponseSchema }
    }
)
async def DeleteTask(task_id: IDConstraints, session: AsyncSession = Depends(routers.GetDatabaseSession),
                     user_id: str = Depends(routers.GetCurrentUserID)):
    task = await TaskServices.GetTaskFromID(session, task_id)
    if task.creator_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="A user can only delete their own tasks!")
    
    await TaskServices.DeleteTaskWithID(session, task_id)
    
    return MessageResponseSchema[str](
        data=f"Successfully deleted task with id '{task_id}'"
    )