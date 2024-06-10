from pydantic import BaseModel, Field, EmailStr

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    isAdmin: bool

class UserInDB(User):
    hashed_password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    isAdmin: bool

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    id: str
    username: str
    isAdmin: bool

class QuriesReq(BaseModel):
    type: str
    dateOpened: str
    status: bool
    userId: str

class QuriesResponse(BaseModel):
    id: str
    type: str
    dateOpened: str
    status: bool
    userId: str

class Status(BaseModel):
    queryId: str
