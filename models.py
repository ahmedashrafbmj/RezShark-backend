from pydantic import BaseModel, Field, EmailStr, conint
from typing import Annotated

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
    dateOpened: str
    status: bool
    userId: str

class Status(BaseModel):
    queryId: str


class ReservationReq(BaseModel):
    userId: str
    email: EmailStr
    password: str
    gameDate: str
    earliestTime: str 
    latestTime: str 
    playerCount: Annotated[int,conint(gt=0)]
    name: str
    confirmationEmail: EmailStr
    ccEmails: str
    hideInBackground: bool
    selectCourses: list[Annotated[int, conint(ge=0, le=1)]]
    dateOpened: str
    status: bool = False
