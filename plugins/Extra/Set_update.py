from pyrogram import Client, filters , enums
from info import ADMINS
import re
from database.users_chats_db import db

@Client.on_message(filters.command("set_muc") & filters.user(ADMINS))
async def set_muc_id(client, message):
    try:
        id = message.command[1]
        if id and str(id).startswith('-100') and len(str(id)) == 14:
            is_suc = await db.movies_update_channel_id(id)
            if is_suc:
                await message.reply("Successfully set movies update  channel id : " + id)
            else:
                await message.reply("Failed to set movies update channel id : " + id)
        else:
            await message.reply("Invalid channel id : " + id)
    except Exception as e:
        print('Err in set_muc_id', e)
        await message.reply("Failed to set movies channel id! Because : " + str(e))

@Client.on_message(filters.command("muc_switch") & filters.user(ADMINS))
async def toggle_movie_updates(client, message):
    try:
        # Status check karega
        current_status = await db.get_send_movie_update_status(client.me.id)
        
        # Status ko ulta kar dega (True hai toh False, False hai toh True)
        new_status = not current_status
        
        # FIX: yahan correct DB function name use kiya hai
        await db.update_send_movie_update_status(client.me.id, new_status)
        
        if new_status:
            await message.reply("✅ Auto Movie Update ab **ON** ho gaya hai. Database me file dalne par channel pe post aayegi.")
        else:
            await message.reply("❌ Auto Movie Update ab **OFF** ho gaya hai. Database me file dalne par update nahi jayega.")
            
    except Exception as e:
        print('Error in toggling movie update status:', e)
        await message.reply(f"Failed to toggle status! Error: {e}")
