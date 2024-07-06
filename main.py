from fastapi import FastAPI, HTTPException, Query
from passlib.context import CryptContext
from models import User, UserResponse, UserLogin, LoginResponse,QuriesReq,QuriesResponse,Status,ReservationReq, QuriesResponseWithInfo,CoursesResponse,Courses
from database import users_collection, check_db_connection,queries_collection
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from typing import List, Optional, Union
from fastapi.middleware.cors import CORSMiddleware
import json
import boto3
from datetime import datetime, timedelta
import socketio
import pandas as pd
import ast
import pytz

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

sio = socketio.AsyncServer(async_mode="asgi",cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio, app)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def process_csv():
    new_df = pd.DataFrame()
    df = pd.read_csv("output.csv")
    
    for index, row in df.iterrows():
        obj = {}
        obj["website_path"] = row["Website Path"]
        obj["course_title"] = row["Course Title"]
        obj["location"] = row["Location"]
        obj["holes"] = row["Holes"]

        courses = row["Courses"].split(",")
        courses_vals = row["Courses Values"].split(",")
        courses_data = []

        print(courses)
        print(courses_vals)
        for i in range(len(courses)):
            try:
                courses_obj = {}
                courses_obj["course_id"] = courses_vals[i]
                courses_obj["course_name"] = courses[i]

                courses_data.append(courses_obj)
            except:
                pass

        obj["courses"] = courses_data

        new_df = pd.concat([new_df, pd.DataFrame([obj])], ignore_index=True)

    new_df.to_csv("new_output.csv")
    return new_df

@app.get("/getCourses", response_model=List[CoursesResponse])
async def allUsers():
    try:
        df = pd.read_csv("new_output.csv")
        result = []

        df['courses'] = df['courses'].apply(ast.literal_eval)

        for index, row in df.iterrows():
            all_crs = []

            courses = row['courses']
            for i in range(len(courses)):
                crs = Courses(
                    course_id=courses[i]["course_id"],
                    course_name=courses[i]["course_name"],
                )

                all_crs.append(crs)

            course = CoursesResponse(
                course_title=row["course_title"],
                holes=row["course_title"],
                location=row["location"],
                website_path=row["website_path"],
                courses=all_crs
            )

            result.append(course)
        return result
    except:
        raise HTTPException(status_code=400, detail="Error getting courses")

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
                "username": str(db_user["nickname"]),
                "isAdmin": str(db_user["isAdmin"]),
                **db_user
                }
    raise HTTPException(status_code=400, detail="Invalid username or password")

   
def describe_log_streams():
    client = boto3.client('logs')
    log_group_name = f'/aws/lambda/script-HelloWorldFunction-TsWKn8pKaVKK'
    
    try:
        # Describe log streams
        response = client.describe_log_streams(
            logGroupName=log_group_name,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )

        log_stream = response.get('logStreams', [])
        if len(log_stream) > 0:
            log_stream = log_stream[0]
            return log_stream['logStreamName']

        return None

    except client.exceptions.ResourceNotFoundException as e:
        print(f"Log group '{log_group_name}' not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_start_end_time(date_str):
    start_datetime = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
    end_datetime = start_datetime + timedelta(minutes=30)

    start_time_ms = int(start_datetime.timestamp() * 1000)
    end_time_ms = int(end_datetime.timestamp() * 1000)

    return start_time_ms, end_time_ms


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

    if response['ResponseMetadata']['RequestId'] and response['ResponseMetadata']['HTTPHeaders']['date']:
        return (response['ResponseMetadata']['RequestId'], response['ResponseMetadata']['HTTPHeaders']['date'])
    else:
        return (None, None)
    

def is_within_24_hours(date_str):
    # Parse the input date string to a datetime object
    date = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
    
    # Convert the datetime object to UTC
    date = date.replace(tzinfo=pytz.UTC)
    
    # Get the current time in UTC
    now = datetime.now(pytz.UTC)
    
    # Calculate the difference
    difference = now - date
    
    # Check if the difference is within 24 hours
    return abs(difference) <= timedelta(hours=24)



def is_within_20_minutes(date_str):
    # Parse the input date string to a datetime object
    date = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
    
    # Convert the datetime object to UTC
    date = date.replace(tzinfo=pytz.UTC)
    
    # Get the current time in UTC
    now = datetime.now(pytz.UTC)
    
    # Calculate the difference
    difference = now - date
    
    # Check if the difference is within 20 minutes
    return abs(difference) <= timedelta(minutes=20)


def startNewLambda(queryId):
    try:
        item = queries_collection.find_one({"_id": ObjectId(queryId)})

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        if(item['requestType'] == 'Time'):
            res = is_within_20_minutes(item["firstReqTime"])
            if res == False:
                return False

        res = is_within_24_hours(item["firstReqTime"])
        if res == False:
            return False
        
        new_item = {
            "booking_email": item['email'],
            "booking_password": item['password'],
            "user_date_str": datetime.strptime(item['gameDate'], '%Y-%m-%d').strftime('%m-%d-%Y') ,
            "user_start_time_str": item['earliestTime'],
            "user_end_time_str": item['latestTime'],
            "players_input": item['playerCount'],
            "receiver_email": item['confirmationEmail'],
            "name": item['name'],
            "email_cc_text": item['ccEmails'],
            "courses_selected": item['selectCourses'],
            'course_names': item['selectCoursesNames'],
            'website_link': item['selectCoursesUrl'],
            'course_values': item['selectCourses'],
        }

        request_id, date = start_lambda_function(new_item)

        if request_id != None:
            queries_collection.update_one(
                {"_id": ObjectId(queryId)},
                {"$set": {"requestId": request_id, "requestTime": date}}
            )

        return True
    except Exception as e:
        print(e)
        pass

def updateBookedStatus(queryId):
    try:
        item = queries_collection.find_one({"_id": ObjectId(queryId)})

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        queries_collection.update_one(
                {"_id": ObjectId(queryId)},
                {"$set": {"isBooked": True}}
            )
    except Exception as e:
        print(e)
        pass

# Function 'HelloWorldFunction' timed out after 600 seconds
def check_lambda_execution_status(request_id, requestTime, queryId, status):
    client = boto3.client('logs')
    log_group_name = f'/aws/lambda/script-HelloWorldFunction-TsWKn8pKaVKK'
    
    # main_group = describe_log_streams()
    # if main_group != None:
        # print(main_group)
    try:
        start_time, end_time = get_start_end_time(requestTime)

        response = client.filter_log_events(
            logGroupName=log_group_name,
            # logStreamNames=[main_group],
            filterPattern=f'"{request_id}"',
            interleaved=True,
            startTime=start_time,
            limit=50
            # endTime=end_time
        )
        global find_it
        find_it = "Active"

        while 'nextToken' in response:
           
            for event in response['events']:
                message = event['message']
                if 'Booking completed' in message:
                    find_it = "Booking Complete"
                    updateBookedStatus(queryId)
                    return "Booking Complete"
                
                if "Error" in message:
                    find_it = "Error"
                
                if "Login Error" in message:
                    find_it = "Login Error"
                    return "Login Error"

                if "Task timed out" in message:
                    res = startNewLambda(queryId)
                    if res:
                        find_it = "Active"
                    else:
                        find_it = "Expired"
                    return find_it

            response = client.filter_log_events(
                logGroupName=log_group_name,
                # logStreamNames=[main_group],
                filterPattern=f'"{request_id}"',
                interleaved=True,
                startTime=start_time,
                limit=50,
                nextToken=response['nextToken']
            )

            

        # Poll CloudWatch Logs for recent log events
        # response = client.filter_log_events(
        #     logGroupName=log_group_name,
        #     # logStreamNames=[main_group],
        #     filterPattern=f'"{request_id}"',
        #     interleaved=True,
        #     startTime=start_time,
        #     # endTime=end_time
        # )
        
        return find_it
        
    except client.exceptions.ResourceNotFoundException as e:
        print(f"Lambda function script-HelloWorldFunction-TsWKn8pKaVKK not found.")
        return "Error"
    except Exception as e:
        print(f"Error: {e}")
        return "Error"


def getReservationHandler(isAdmin, userId):
    if isAdmin == True:
        db_data = queries_collection.find()
    else:
        db_data = queries_collection.find({"userId": ObjectId(userId)})

    result = []

    for data in db_data:
        data["id"] = str(data["_id"])
        data["userId"] = str(data["userId"])

        if data["requestId"] != None and data["status"] and data["isBooked"] == False:
            new_type = check_lambda_execution_status(data["requestId"], data["requestTime"], data["id"],
                                                     data["status"])
        else:
            new_type = "Booking Complete" if(data["isBooked"]) else "Inactive"

        data["type"] = new_type

        qData = QuriesResponse(**data)
        result.append(qData.dict())
    return result

@app.get("/reservations")
async def queries(
        isAdmin: Optional[bool] = Query(False),
        userId: Optional[str] = Query(None),
        showType: Optional[bool] = Query(True),
    ):
    if isAdmin == True:
        db_data = queries_collection.find()
    else:
        db_data = queries_collection.find({"userId": ObjectId(userId)})

    result = []

    for data in db_data:
        data["id"] = str(data["_id"])
        data["userId"] = str(data["userId"])

        # if data["requestId"] != None and showType and data["status"] and data["isBooked"] == False:
        #     new_type = check_lambda_execution_status(data["requestId"], data["requestTime"], data["id"],
        #                                              data["status"])
        # else:

        if(data["isBooked"]):
            new_type = "Booking Complete"
        elif(data["status"] == False):
            new_type = "Inactive"
        else:
            new_type = "Loading Status ..."

        data["type"] = new_type
        if showType == False:
            result.append(QuriesResponseWithInfo(**data))
        else:
            result.append(QuriesResponse(**data))

    return result

@app.post("/addReservation")
async def addReservation(qury: ReservationReq):
    try:
        qury.userId = ObjectId(qury.userId)
        query_dict = qury.dict()
        query_dict["requestId"] = None
        query_dict["requestTime"] = None
        query_dict["isBooked"] = False
        query_dict["firstReqTime"] = None
        result = queries_collection.insert_one(query_dict)

        if qury.requestType == "Standard":
            await statusToggle(status=Status(queryId=str(result.inserted_id)))

        return True
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Error Add Reservation")


@app.delete("/reservation")
async def addReservation(queryId: str):
    try:
        result = queries_collection.delete_one({"_id": ObjectId(queryId)})
        if result.deleted_count == 1:
            return True
        
        return False
    except:
        raise HTTPException(status_code=400, detail="Error Deleting Reservation")

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
                "user_date_str": datetime.strptime(item['gameDate'], '%Y-%m-%d').strftime('%m-%d-%Y') ,
                "user_start_time_str": item['earliestTime'],
                "user_end_time_str": item['latestTime'],
                "players_input": item['playerCount'],
                "receiver_email": item['confirmationEmail'],
                "name": item['name'],
                "email_cc_text": item['ccEmails'],
                "courses_selected": item['selectCourses'],
                'course_names': item['selectCoursesNames'],
                'website_link': item['selectCoursesUrl'],
                'course_values': item['selectCourses'],
            }

            request_id, date = start_lambda_function(new_item)

            if request_id != None:
                queries_collection.update_one(
                    {"_id": ObjectId(status.queryId)},
                    {"$set": {"requestId": request_id, "requestTime": date, "firstReqTime": date}}
                )
        else:
            queries_collection.update_one(
                    {"_id": ObjectId(status.queryId)},
                    {"$set": {"requestId": None, "requestTime": None}}
                )

        return {"message": "Status toggled successfully", "new_status": new_status}
    else:
        raise HTTPException(status_code=400, detail="Failed to toggle status")


# Define Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print("Client connected:", sid)

@sio.event
async def disconnect(sid):
    print("Client disconnected:", sid)

@sio.event
async def message(sid, data):
    if not data:
        return
    
    result = getReservationHandler(data["isAdmin"], data["id"])

    if(len(result) > 0):
        await sio.emit("message", result, to=sid)

if check_db_connection():
    print("Database connection successful")
else:
    raise HTTPException(status_code=500, detail="Database connection failed")

if __name__ == "__main__":
    # process_csv()
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
