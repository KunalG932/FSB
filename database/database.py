import pymongo
from config import DB_URI, DB_NAME

dbclient = pymongo.MongoClient(DB_URI)
database = dbclient[DB_NAME]

user_data = database['users']
admins_collection = database['admins']
clicks = database['click']
channels = database['channel']

async def add_user(user_id: int):
    user_data.insert_one({'_id': user_id})
    return

async def remove_all():
    try:
        result = user_data.delete_many({})
        print(f"Deleted {result.deleted_count} documents from user_data collection.")
        return True
    except Exception as e:
        print(f"Failed to remove all users: {e}")
        return False
        

async def present_user(user_id: int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)

async def full_userbase():
    user_docs = user_data.find()
    user_ids = [doc['_id'] for doc in user_docs]
    return user_ids

async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return

async def add_admin(user_id: int):
    try:
        admins_collection.insert_one({'_id': user_id})
        return True
    except Exception as e:
        print(f"Failed to add admin: {e}")
        return False

async def remove_admin(user_id: int):
    try:
        admins_collection.delete_one({'_id': user_id})
        return True
    except Exception as e:
        print(f"Failed to remove admin: {e}")
        return False

async def is_admin(user_id: int):
    return bool(admins_collection.find_one({'_id': user_id}))

async def set_fsub(channel1: int, channel2: int):
    try:
        channels.update_one({}, {'$set': {'force_sub_channel_1': channel1, 'force_sub_channel_2': channel2}}, upsert=True)
    except Exception as e:
        print(f"Failed to set force subscribe channels: {e}")

async def get_fsub():
    try:
        config = channels.find_one({})
        return config.get('force_sub_channel_1', -1001774171058), config.get('force_sub_channel_2', -1001980866472)
    except Exception as e:
        print(f"Failed to get force subscribe channels: {e}")
        return -1001774171058, -1001980866472

async def get_admin_list():
    admin_docs = admins_collection.find()
    admin_ids = [doc['_id'] for doc in admin_docs]
    return admin_ids

async def add_click(user_id: int, base64_string: str):
    try:
        clicks.update_one(
            {'_id': user_id},
            {'$addToSet': {'base64_strings': base64_string}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Failed to store base64 string: {e}")
        return False

async def total_click(base64_string: str):
    try:
        count = clicks.count_documents({'base64_strings': base64_string})
        return count
    except Exception as e:
        print(f"Failed to get total users for base64 string: {e}")
        return 0

async def top_users():
    try:       
        pipeline = [
            {"$unwind": "$base64_strings"},
            {"$group": {"_id": "$_id", "total_clicks": {"$sum": 1}}},
            {"$sort": {"total_clicks": -1}},
            {"$limit": 10}
        ]
        top_users = clicks.aggregate(pipeline)
       
        top_users_list = [(user["_id"], user["total_clicks"]) for user in top_users]
        return top_users_list
    except Exception as e:
        print(f"Failed to get top users: {e}")
        return []
        
        
