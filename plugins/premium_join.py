from pyrogram import Client, filters
from pyrogram.types import ChatJoinRequest
from database.users_chats_db import db
from info import PRN_ID, VIP_GROUP_ID, NEW_PREMIUM_CHANNEL

# 🔥 FUTURE PROOFING: Yahan kitne bhi channels aage chalkar add kar sakte ho
PREMIUM_CHATS = [PRN_ID, VIP_GROUP_ID]
if NEW_PREMIUM_CHANNEL: # Corrected Python syntax
    PREMIUM_CHATS.append(NEW_PREMIUM_CHANNEL)
    
@Client.on_chat_join_request(filters.chat(PREMIUM_CHATS))
async def auto_approve_premium(client, message: ChatJoinRequest):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Database se direct check karo ki user premium hai ya nahi
    is_premium = await db.has_premium_access(user_id)
    
    if is_premium:
        # User premium hai -> Chup-chaap approve kar do
        try:
            await client.approve_chat_join_request(chat_id, user_id)
        except Exception as e:
            print(f"Approve Error: {e}")
    else:
        # User free hai -> Request decline karo aur warn karo
        try:
            await client.decline_chat_join_request(chat_id, user_id)
        except Exception: # HIDE_REQUESTER_MISSING bypass
            pass
            
        try:
            await client.send_message(
                user_id, 
                "❌ **Join Request Declined!**\n\nAapke paas active Premium Subscription nahi hai ya expire ho chuka hai. Premium activate karne ke liye /plan check karein."
            )
        except Exception:
            pass
