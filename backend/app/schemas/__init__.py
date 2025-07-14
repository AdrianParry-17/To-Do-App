import enum
from pydantic import BaseModel
from typing import Generic, List, TypeVar

_T = TypeVar("_T")

class ResponseStatusType(enum.Enum):
    """The Response Status Type enum, use for defining the status of a response."""
    OK = "ok"
    Error = "error"
    
class ResponseResultType(enum.Enum):
    Object = "object"
    Collections = "collections"
    Error = "error"
    Message = "message"
    Unknown = "unknown"

class BaseResponseSchema(BaseModel):
    """The Base Response Schema, based class for all API response model."""
    status: ResponseStatusType
    result: ResponseResultType
    
class ObjectResponseSchema(BaseResponseSchema, Generic[_T]):
    """The Object Response Schema, use for API single object response."""
    
    status: ResponseStatusType = ResponseStatusType.OK 
    result: ResponseResultType = ResponseResultType.Object
    
    data: _T
    
class CollectionsResponseSchema(BaseResponseSchema, Generic[_T]):
    """The Collections Response Schema, use for API multiple objects response."""
    
    status: ResponseStatusType = ResponseStatusType.OK
    result: ResponseResultType = ResponseResultType.Collections
    
    data: List[_T]
    
class MessageResponseSchema(BaseResponseSchema, Generic[_T]):
    """The Message Response Schema, use for API messages response."""
    
    status: ResponseStatusType = ResponseStatusType.OK
    result: ResponseResultType = ResponseResultType.Message
    
    data: _T
    
class BaseErrorResponseSchema(BaseResponseSchema, Generic[_T]):
    """The Error Response Schema, use for API error response."""
    
    status: ResponseStatusType = ResponseStatusType.Error 
    result: ResponseResultType = ResponseResultType.Error
    
    data: _T