import schemas
from fastapi import status
from pydantic import BaseModel, Field
from typing import List

class ErrorDetailSchema(BaseModel):
    """The Error Detail Schema for response with error detail."""
    code: int = Field(title="HTTP Error Code")
    detail: str = Field(title="Error details")

class ErrorResponseSchema(schemas.BaseErrorResponseSchema[List[ErrorDetailSchema]], BaseModel):
    """The Error Response Schema for responses with errors."""
    pass