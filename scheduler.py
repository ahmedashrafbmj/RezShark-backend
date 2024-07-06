from apscheduler.schedulers.background import BlockingScheduler
from datetime import datetime, timedelta
from database import check_db_connection,queries_collection
from bson import ObjectId
from models import Status
import boto3
import json

# Initialize a session using Amazon Lambda
client = boto3.client('lambda')

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
    

def statusToggle(status: Status):
    item = queries_collection.find_one({"_id": ObjectId(status.queryId)})

    if not item:
        print("Item not found")
        return

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

        print("Status toggled successfully")
        return
    else:
        print("Failed to toggle status")
        return

def getSchedularData(time_str):
    try:
        reference_time = datetime.strptime(time_str, "%H:%M")
    
        # Calculate the time range
        start_time = reference_time - timedelta(minutes=5)
        end_time = reference_time + timedelta(minutes=5)

        current_date = datetime.now().date()
        formatted_date = current_date.strftime("%Y-%m-%d")

        print(formatted_date)
        
        # Query the collection
        query = {
            "earliestTime": {
                "$gte": start_time.strftime("%H:%M"),
                "$lte": end_time.strftime("%H:%M")
            },
            "requestType": "Time",
            "status": False,
            "isBooked": False,
            "gameDate": formatted_date,
        }
        
        item = queries_collection.find(query)

        for it in item:
            statusToggle(status=Status(queryId=str(it["_id"])))
            
    except Exception as e:
        print(e)
        pass

# Function to be scheduled
def scheduled_task():
    current_time = datetime.now().strftime("%H:%M")
    print(f"Scheduled task running at {current_time}")
    getSchedularData(current_time)


if __name__ == "__main__":

    if check_db_connection():
        print("Database connection successful")
    else:
        raise Exception("Database connection failed")

    # Scheduler setup
    scheduler = BlockingScheduler()

    # Schedule the task to run at the 0th second of every minute
    scheduler.add_job(scheduled_task, 'cron', second=0)

    # Start the scheduler
    try:
        print("Starting scheduler...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")