import pymongo
from info import DATABASE_URI, DATABASE_NAME
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

myclient = pymongo.MongoClient(DATABASE_URI)
mydb = myclient[DATABASE_NAME]

class UserTracker:
    def __init__(self):
        self.refer_collection = mydb["refers"]
        self.refer_logs = mydb["referral_analytics"] # Naya collection analytics ke liye

    def get_refer_data(self, user_id: int):
        user = self.refer_collection.find_one({'user_id': user_id})
        if not user:
            default_data = {
                'user_id': user_id,
                'total_invites': 0,
                'claimed_milestones': [],
                'infinite_claims': 0
            }
            self.refer_collection.insert_one(default_data)
            return default_data
            
        # 💥 THE CRASH FIX: Purane users ke purane points ko naye invites me convert karna
        if 'total_invites' not in user:
            user['total_invites'] = user.get('points', 0) // 10
            user['claimed_milestones'] = []
            user['infinite_claims'] = 0
            self.refer_collection.update_one({'user_id': user_id}, {'$set': user})
            
        return user

    def add_invite(self, inviter_id: int, new_user_id: int):
        # Inviter ka count badhao
        self.refer_collection.update_one(
            {'user_id': inviter_id},
            {'$inc': {'total_invites': 1}},
            upsert=True
        )
        # Analytics ke liye log save karo (Timestamp ke sath)
        self.refer_logs.insert_one({
            'inviter_id': inviter_id,
            'new_user_id': new_user_id,
            'timestamp': datetime.now()
        })

    def log_claimed_milestone(self, user_id: int, milestone: str):
        self.refer_collection.update_one(
            {'user_id': user_id},
            {'$push': {'claimed_milestones': milestone}}
        )

    def log_infinite_claim(self, user_id: int):
        self.refer_collection.update_one(
            {'user_id': user_id},
            {'$inc': {'infinite_claims': 1}}
        )

    # 📊 ADMIN ANALYTICS FUNCTION
    def get_analytics(self):
        now = datetime.now()
        today = now - timedelta(days=1)
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)

        daily = self.refer_logs.count_documents({'timestamp': {'$gte': today}})
        weekly = self.refer_logs.count_documents({'timestamp': {'$gte': last_7_days}})
        monthly = self.refer_logs.count_documents({'timestamp': {'$gte': last_30_days}})
        total = self.refer_logs.count_documents({})

        return daily, weekly, monthly, total

    # 🏆 TOP 10 REFERRERS LOGIC (MONTHLY & ALL-TIME)
    def get_top_referrers(self, period="monthly"):
        if period == "alltime":
            # Purana logic: Sabse zyada invites wala
            return list(self.refer_collection.find({"total_invites": {"$gt": 0}}).sort("total_invites", pymongo.DESCENDING).limit(10))
        else:
            # Naya logic: Sirf is mahine ke invites count karega
            start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            pipeline = [
                {"$match": {"timestamp": {"$gte": start_of_month}}},
                {"$group": {"_id": "$inviter_id", "total_invites": {"$sum": 1}}},
                {"$sort": {"total_invites": -1}},
                {"$limit": 10},
                {"$project": {"user_id": "$_id", "total_invites": 1, "_id": 0}}
            ]
            return list(self.refer_logs.aggregate(pipeline))

    # 🔥 GET USER'S MONTHLY INVITE COUNT
    def get_user_monthly_invites(self, user_id: int):
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.refer_logs.count_documents({"inviter_id": user_id, "timestamp": {"$gte": start_of_month}})

    # 📈 DYNAMIC RANK CALCULATOR (TIME AWARE)
    def get_user_rank(self, invites: int, period="monthly"):
        if invites <= 0:
            return None
            
        if period == "alltime":
            higher_scores_count = self.refer_collection.count_documents({"total_invites": {"$gt": invites}})
            return higher_scores_count + 1
        else:
            start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            pipeline = [
                {"$match": {"timestamp": {"$gte": start_of_month}}},
                {"$group": {"_id": "$inviter_id", "total": {"$sum": 1}}},
                {"$match": {"total": {"$gt": invites}}},
                {"$count": "higher_rankers"}
            ]
            result = list(self.refer_logs.aggregate(pipeline))
            if result:
                return result[0]["higher_rankers"] + 1
            return 1

# Initialize Database
referdb = UserTracker()
