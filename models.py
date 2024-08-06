from pydantic import BaseModel, Field, EmailStr, conint
from typing import Annotated, Optional

class User(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str
    last_name: str
    nickname: str
    birthday: Optional[str]
    city: Optional[str]
    state: Optional[str]
    isAdmin: bool

class UserInDB(User):
    hashed_password: str

class UserResponse(BaseModel):
    id: str
    nickname: str
    email: EmailStr
    isAdmin: bool

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    id: str
    nickname: str
    email: EmailStr
    isAdmin: bool
    first_name: str
    last_name: str
    nickname: str
    birthday: str
    city: str
    state: str

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
    booking_class: str
    earliestTime: str 
    latestTime: str 
    requestType: str
    playerCount: int
    scriptDate: str
    scriptTime: str

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
    booking_class: str
    status: bool
    userId: str
    earliestTime: str 
    latestTime: str 
    requestType: str
    playerCount: int
    scriptDate: str
    scriptTime: str

class Status(BaseModel):
    queryId: str


class ReservationReq(BaseModel):
    userId: str
    resName: str
    email: EmailStr
    password: str
    gameDate: str
    earliestTime: str
    booking_class: str
    latestTime: str 
    playerCount: Annotated[int,conint(gt=0)]
    name: str
    confirmationEmail: EmailStr
    ccEmails: list[str]
    hideInBackground: bool
    selectCourses: list[Annotated[int, conint(ge=0, le=1)]]
    selectCoursesNames: list[str]
    selectCoursesUrl: str
    dateOpened: str
    requestType: str
    status: bool = False
    scriptDate: str
    scriptTime: str

class Courses(BaseModel):
    course_id: int
    course_name: str

class CoursesResponse(BaseModel):
    website_path: str
    course_title: str
    location: str
    courses: list[Courses]
    holes: str