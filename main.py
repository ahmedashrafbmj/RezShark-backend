from fastapi import FastAPI, HTTPException, Query
from passlib.context import CryptContext
from models import User, UserResponse, UserLogin, LoginResponse,QuriesReq,QuriesResponse,Status,ReservationReq
from database import users_collection, check_db_connection,queries_collection
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import json
import boto3
import datetime

# Initialize a session using Amazon Lambda
client = boto3.client('lambda')

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

@app.get("/reservations", response_model=List[QuriesResponse])
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

@app.post("/addReservation")
async def addReservation(qury: ReservationReq):
    try:
        qury.userId = ObjectId(qury.userId)
        query_dict = qury.dict()
        queries_collection.insert_one(query_dict)
        return True
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Error Add Reservation")
    
# check_lambda_execution_status("3f8e774f-7659-479e-9cb5-39e2cfdb8e5b")

def start_lambda_function(data):
    # payloadStr = json.dumps({
    #         "booking_email": "01il84@mepost.pw",
    #         "booking_password": "1234567",
    #         "user_date_str": "06-15-2024",
    #         "user_start_time_str": "06:00",
    #         "user_end_time_str": "23:00",
    #         "players_input": 1,
    #         "receiver_email": "01il84@mepost.pw",
    #         "name": "khan",
    #         "email_cc_text": [""],
    #         "courses_selected": [0, 1, 1, 1, 0]
    #     })


    payloadStr = json.dumps(data)
    payloadBytesArr = bytes(payloadStr, encoding='utf8')
    response = client.invoke(
        FunctionName='script-HelloWorldFunction-TsWKn8pKaVKK',
        InvocationType='Event',  # Or 'RequestResponse' for async invocation
        Payload=payloadBytesArr
    )

    print(response)


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

        if new_status:
            new_item = {
                "booking_email": item['email'],
                "booking_password": item['password'],
                "user_date_str": datetime.datetime.strptime(item['gameDate'], '%Y-%m-%d').strftime('%m-%d-%Y') ,
                "user_start_time_str": item['earliestTime'],
                "user_end_time_str": item['latestTime'],
                "players_input": item['playerCount'],
                "receiver_email": item['confirmationEmail'],
                "name": item['name'],
                "email_cc_text": [''],
                "courses_selected": item['selectCourses']
            }
            print(new_item)
            start_lambda_function(new_item)
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
