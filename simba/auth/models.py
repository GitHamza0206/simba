from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class UserResponse(BaseModel):
    id: str
    email: EmailStr
    access_token: Optional[str] = None
    email_confirmed: bool = False
    message: Optional[str] = None
    
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer" 