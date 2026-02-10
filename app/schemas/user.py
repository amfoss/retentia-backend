from pydantic import BaseModel, EmailStr
from ..enums import Grade

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    username: str
    grade: Grade
    institute: str
    city: str
    marketing: str
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class GoogleAuthRequest(BaseModel):
    token: str
    
class GoogleVerifiedResponse(BaseModel):
    token: str
    email: str
    name: str

class GoogleCompleteProfile(BaseModel):
    token: str
    username: str
    password: str
    grade: Grade
    institute: str
    city: str
    marketing: str