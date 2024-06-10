from fastapi import FastAPI, HTTPException, Query
from passlib.context import CryptContext
from models import User, UserResponse, UserLogin, LoginResponse,QuriesReq,QuriesResponse,Status
from database import users_collection, check_db_connection,queries_collection
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.get("/users", response_model=List[UserResponse])
async def allUsers():
    db_data = users_collection.find({ "isAdmin": False})
    result = []

    for data in db_data:
        data["id"] = str(data["_id"])
        result.append(UserResponse(**data))
    return result

@app.delete("/users")
async def delUser(userId: str = Query(False)):
    db_user = users_collection.delete_one({"_id": ObjectId(userId)})
    if db_user.deleted_count == 1:
        return { "message": "success"}
    raise HTTPException(status_code=400, detail="Error deleting user")

@app.post("/signup", response_model=UserResponse)
async def signup(user: User):
    hashed_password = pwd_context.hash(user.password)
    user_dict = user.dict()
    user_dict["email"] = user_dict["email"].lower()
    user_dict["hashed_password"] = hashed_password
    user_dict.pop("password")
    exist_user = users_collection.find_one({"email": user_dict["email"]})

    if exist_user is None:
        result = users_collection.insert_one(user_dict)
        new_user = users_collection.find_one({"_id": result.inserted_id})
        new_user["id"] = str(new_user["_id"])
        new_user.pop("_id")
        return UserResponse(**new_user)
    else:
        raise HTTPException(status_code=400, detail="Username or email already exists")

@app.post("/login", response_model=LoginResponse)
async def login(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email.lower()})
    if db_user and pwd_context.verify(user.password, db_user["hashed_password"]):
        return {"id": str(db_user["_id"]),
                "username": str(db_user["username"]),
                "isAdmin": str(db_user["isAdmin"]),
                }
    raise HTTPException(status_code=400, detail="Invalid username or password")

@app.get("/queries", response_model=List[QuriesResponse])
async def queries(
        isAdmin: Optional[bool] = Query(False),
        userId: Optional[str] = Query(None),
    ):
    if isAdmin == True:
        db_data = queries_collection.find()
    else:
        db_data = queries_collection.find({"userId": ObjectId(userId)})

    result = []

    for data in db_data:
        data["id"] = str(data["_id"])
        data["userId"] = str(data["userId"])

        result.append(QuriesResponse(**data))
    return result

@app.post("/addQuery", response_model=QuriesResponse)
async def queries(qury: QuriesReq):
    try:

        qury.userId = ObjectId(qury.userId)
        query_dict = qury.dict()
        result = queries_collection.insert_one(query_dict)
        queryRes = queries_collection.find_one({"_id": result.inserted_id})
        queryRes["id"] = str(queryRes["_id"])
        queryRes["userId"] = str(queryRes["userId"])
        queryRes.pop("_id")
        return QuriesResponse(**queryRes)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Error Add Query")

@app.put("/toggleStatus")
async def statusToggle(status: Status):
    item = queries_collection.find_one({"_id": ObjectId(status.queryId)})

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    new_status = not item["status"]

    result = queries_collection.update_one(
        {"_id": ObjectId(status.queryId)},
        {"$set": {"status": new_status}}
    )

    if result.modified_count:
        return {"message": "Status toggled successfully", "new_status": new_status}
    else:
        raise HTTPException(status_code=400, detail="Failed to toggle status")


if check_db_connection():
    print("Database connection successful")
else:
    raise HTTPException(status_code=500, detail="Database connection failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
