from pymongo import MongoClient

client = MongoClient("mongodb+srv://khanali:Admin12345@cluster0.kqw5aw6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["rezshark"]
users_collection = db["user"]
queries_collection = db["queries"]

def check_db_connection():
    try:
        # This will attempt to list the database names and raise an exception if it fails
        client.admin.command('ping')
        return True
    except ConnectionError:
        return False