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
    resName: str
    dateOpened: str
    gameDate: str
    type: str
    status: bool
    userId: str
    earliestTime: str 
    latestTime: str 
    playerCount: int


class QuriesResponseWithInfo(BaseModel):
    id: str
    resName: str
    name: str
    email: str
    password: str
    dateOpened: str
    confirmationEmail: str
    ccEmails: list[str]
    selectCourses: list[int]
    gameDate: str
    type: str
    status: bool
    userId: str
    earliestTime: str 
    latestTime: str 
    playerCount: int


class Status(BaseModel):
    queryId: str


class ReservationReq(BaseModel):
    userId: str
    resName: str
    email: EmailStr
    password: str
    gameDate: str
    earliestTime: str 
    latestTime: str 
    playerCount: Annotated[int,conint(gt=0)]
    name: str
    confirmationEmail: EmailStr
    ccEmails: list[str]
    hideInBackground: bool
    selectCourses: list[Annotated[int, conint(ge=0, le=1)]]
    dateOpened: str
    status: bool = False
