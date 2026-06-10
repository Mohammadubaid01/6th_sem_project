from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["ai_tutor"]

attempts_collection = db["attempts"] 

test_results_collection = db["test_results"]