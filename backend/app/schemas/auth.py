import schemas
from schemas.users import UsernameConstraints, PasswordConstraints
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class LoginRequestSchema(BaseModel):
    """The Login Request Schema use for user login."""
    username: UsernameConstraints = Field(title="Username")
    password: PasswordConstraints = Field(title="Password")
    
class RegisterRequestSchema(BaseModel):
    """The Register Request Schema use for user register."""
    username: UsernameConstraints = Field(title="Username")
    password: PasswordConstraints = Field(title="Password")
    email: Optional[EmailStr] = Field(None, title="Email")
    
class TokenResponseSchema(BaseModel):
    """The Token Response Schema use for token response."""
    access_token: str = Field(title="Access Token")
    token_type: str = Field("Bearer", title="The token type")