import os
from datetime import datetime, UTC
import logging

try:
	from pymongo import MongoClient
	from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError # Import specific exceptions
except ImportError:
	MongoClient = None
except Exception as e: # Catch any other unexpected import errors
    print(f"ERROR: Failed to import pymongo: {e}")
    MongoClient = None

MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB", "unclut")
COLLECTION = os.getenv("MONGODB_COLLECTION", "users")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _get_collection():
	if not (MONGO_URI and MongoClient):
		return None
	try:
		client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
		client.admin.command('ismaster')
		db = client[DB_NAME]
		logging.info(f"Successfully connected to MongoDB database: {DB_NAME}")
		return db[COLLECTION]
	except (ConnectionFailure, ServerSelectionTimeoutError) as e:
		logging.error(f"MongoDB connection failed: {e}. Please check your MONGODB_URI and Network Access in Atlas.")
		return None
	except Exception as e:
		logging.error(f"An unexpected error occurred during MongoDB connection setup: {e}")
		return None

def record_activity(user_email: str, unsub_delta: int = 0, deleted_delta: int = 0) -> None:
	if not user_email or (unsub_delta == 0 and deleted_delta == 0):
		return
	coll = _get_collection()
	now = datetime.now(UTC)
	update = {
		"$setOnInsert": {
			"email": user_email,
			"createdAt": now,
		},
		"$inc": {
			"unsubs_count": max(0, int(unsub_delta)),
			"deleted_count": max(0, int(deleted_delta))
		},
		"$set": {"updatedAt": now}
	}
	try:
		result = coll.update_one({"_id": user_email}, update, upsert=True)
		if result.upserted_id:
			logging.info(f"New user {user_email} added to database.")
		elif result.modified_count:
			logging.info(f"Updated activity for {user_email}. Unsub: {unsub_delta}, Deleted: {deleted_delta}.")
		else:
			logging.info(f"Activity record operation for {user_email} completed with no changes (dry run or no new activity).")
	except Exception as e:
		logging.error(f"Failed to record activity for {user_email} in MongoDB: {e}")
