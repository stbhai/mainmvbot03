from datetime import timedelta
import pytz
import datetime, time
from Script import script 
from info import ADMINS, LOG_CHANNEL
from utils import get_seconds
from database.users_chats_db import db, mydb 
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ==========================================
# 🖼️ YAHAN APNI ALAG-ALAG IMAGES KE LINKS DAALO
# ==========================================

# 1. Standard '/plan' command wali image
PLAN_CMD_IMG = "https://i.ibb.co/GfC0C3CR/x.jpg"

# 2. Start menu ke 'Premium' button (seeplans callback) click par aane wali image
PREMIUM_BTN_IMG = "https://i.ibb.co/GfC0C3CR/x.jpg"

# 3. Welcome message ke 'My Premium Plan' button (check_myplan callback) click par aane wali image
MY_PLAN_IMG = "https://i.ibb.co/RTYS1yKH/x.jpg"

# 4. '💳 Check Plans & Pricing 💰' button click par aane wali image
ALL_PLANS_PRICE_IMG = "https://i.ibb.co/CpZdBkX3/x.jpg"

# 5. Welcome message ke 'My Premium Plan' button (check_myplan callback) click par aane wali image
NO_PLAN_IMG = "https://i.ibb.co/LDnqh0kK/x.jpg"

PREMIUM_DELIVERY_CHANNEL = -1004290988287

@Client.on_message(filters.command("add_premium"))
async def give_premium_cmd_handler(client, message):
    if message.from_user.id not in ADMINS:
        await message.reply("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ.")
        return
    if len(message.command) == 3:
        user_id = int(message.command[1])
        try:
            user = await client.get_users(user_id)
        except:
            return await message.reply("❌ User not found!")
            
        time_str = message.command[2]        
        seconds = await get_seconds(time_str)
        if seconds > 0:
            current_time = datetime.datetime.now()
            
            if await db.has_premium_access(user_id):
                remaining_time = await db.check_remaining_uasge(user_id)
                expiry_time = current_time + remaining_time + datetime.timedelta(seconds=seconds)
            else:
                expiry_time = current_time + datetime.timedelta(seconds=seconds)

            # 🔥 THE CRM UPGRADE: Setting "paid" tag and resetting reminders
            user_data = {
                "id": user_id, 
                "expiry_time": expiry_time,
                "premium_type": "paid",
                "notified_3d": False,
                "notified_2d": False,
                "notified_1d": False
            } 
            await db.update_user(user_data)
            
            await message.reply_text(f"✅ ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ: {user.mention}\n⚡ ɪᴅ : {user.id}\n⏰ ᴀᴄᴄᴇꜱꜱ : {time_str}")
            
           # --- 5-MESSAGE SYSTEM (AUTO-APPROVE & NEW CHANNEL) ---
            try:
                from info import PRN_ID, VIP_GROUP_ID, NEW_PREMIUM_CHANNEL
                import asyncio
                
                # 🔥 LINK FIX: member_limit=2 hata kar creates_join_request=True laga diya
                vip_invite = await client.create_chat_invite_link(chat_id=VIP_GROUP_ID, creates_join_request=True)
                prn_invite = await client.create_chat_invite_link(chat_id=PRN_ID, creates_join_request=True)
                
                # Naye Channel Ka Link (Updates Channel)
                new_ch_invite = None
                try:
                    new_ch_invite = await client.create_chat_invite_link(chat_id=NEW_PREMIUM_CHANNEL, creates_join_request=True)
                except Exception as e:
                    print(f"Naye Channel ka link banne mein error (Check karo kya bot channel me admin hai?): {e}")

                expiry_str = expiry_time.strftime("%d %B %Y")
                
                msg1 = (
                    f"🌟 <b><u>ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴍʙᴇʀsʜɪᴘ ᴀᴄᴛɪᴠᴀᴛᴇᴅ</u></b>\n\n"
                    f"Congratulations {user.mention}! 🎉\n"
                    f"Aapka account successfully <b>Premium</b> par Upgrade ho gaya hai."
                )

                msg2 = (
                    f"<b>❏ [1] PREMIUM REQUEST GROUP ™ ✅</b>\n"
                    f"<b>Request To Join 👇👇</b>\n"                    
                    f"{vip_invite.invite_link}\n\n"
                    f"<blockquote>⚡ <b>What You Can Do Here?</b>\n"
                    f"• Request Any Movie / Web Series\n"
                    f"• Get Fast Download Links\n"
                    f"• Request 4K / 1080p Quality\n"
                    f"• Request Unavailable Movies</blockquote>\n\n"
                    f"📢<b>Important:\n"
                    f"Link par click karke 'Request' bhejein, system aapko instantly auto-approve kar dega! 💬</b>"
                )

                msg3 = (
                    f"🚨 𝙏𝙝𝙞𝙨 𝙞𝙨 𝙊𝙥𝙩𝙞𝙤𝙣𝙖𝙡 𝘾𝙝𝙖𝙣𝙣𝙚𝙡 🚨\n\n"
                    f"<b>❏ [2] Premium Masti Channel 🔞: </b>\n"
                    f"<b>Request To Join 👇👇</b>\n"
                    f"{prn_invite.invite_link}\n\n"
                    f"<blockquote>[ Agar aap 18+ content dekhna pasand karte hain toh join kar sakte hain. Otherwise aap channel leave bhi kar sakte hain. 🫥]</blockquote>"
                )

                # 🔥 NAYA MSG4: Updates Channel Ke Liye
                if new_ch_invite:
                    msg4 = (
                        f"<b>❏ [3] New Premium Movies & Series: </b>\n\n"
                        f"<b>Request To Join 👇👇</b>\n"
                        f"{new_ch_invite.invite_link}\n\n"
                        f"<blockquote>🎬 Yahan aapko sabhi <b>New Movies & Web Series</b> ki latest files milti rahengi.\n"
                        f"• Channel join karke rakhein taaki koi bhi new release miss na ho!</blockquote>"
                    )
                else:
                    msg4 = None

                # Purana msg4 ab msg5 ban gaya hai
                msg5 = (
                    f"<b>⌛ Premium Expires On: {expiry_str} ✅</b>\n\n"
                    f"Apne plan ki validity check karne ke liye bot mein <b>/myplan</b> 👈 command ka use karein.\n\n"
                    f"🚀 <b>Ab seedha apni favourite movies & series search karo aur enjoy karo!</b>"
                )

                # --- SEND TO USER ---
                try:
                    await client.send_message(chat_id=user_id, text=msg1)
                    await asyncio.sleep(1.5)
                    await client.send_message(chat_id=user_id, text=msg2, disable_web_page_preview=True)
                    await asyncio.sleep(1.5)
                    await client.send_photo(chat_id=user_id, photo="https://i.ibb.co/YTLdpVyZ/x.jpg", caption=msg3, has_spoiler=True)
                    await asyncio.sleep(1.5)
                    
                    if msg4: # Sirf tabhi bhejega jab info.py me channel ID set hogi aur link ban gaya hoga
                        await client.send_message(chat_id=user_id, text=msg4, disable_web_page_preview=True)
                        await asyncio.sleep(1.5)
                        
                    await client.send_message(chat_id=user_id, text=msg5, disable_web_page_preview=True)
                    print(f"✅ Premium DM successfully sent to user: {user_id}")
                except Exception as user_dm_error:
                    print(f"⚠️ User DM delivery failed: {user_dm_error}")

                # --- SEND TO DELIVERY CHANNEL ---
                try:
                    if PREMIUM_DELIVERY_CHANNEL and PREMIUM_DELIVERY_CHANNEL != 0:
                        await client.send_message(
                            chat_id=PREMIUM_DELIVERY_CHANNEL, 
                            text=f"📦 **PREMIUM DELIVERY COPY**\n👤 **User:** {user.mention}\n⚡ **User ID:** `{user.id}`\n\n👇 **Neeche diye gaye messages same link copy hain, aap personally forward kar sakte hain:**"
                        )
                        await asyncio.sleep(1.5)
                        await client.send_message(chat_id=PREMIUM_DELIVERY_CHANNEL, text=msg1)
                        await asyncio.sleep(1.5)
                        await client.send_message(chat_id=PREMIUM_DELIVERY_CHANNEL, text=msg2, disable_web_page_preview=True)
                        await asyncio.sleep(1.5)
                        await client.send_photo(chat_id=PREMIUM_DELIVERY_CHANNEL, photo="https://i.ibb.co/YTLdpVyZ/x.jpg", caption=msg3, has_spoiler=True)
                        await asyncio.sleep(1.5)
                        
                        if msg4:
                            await client.send_message(chat_id=PREMIUM_DELIVERY_CHANNEL, text=msg4, disable_web_page_preview=True)
                            await asyncio.sleep(1.5)
                            
                        await client.send_message(chat_id=PREMIUM_DELIVERY_CHANNEL, text=msg5, disable_web_page_preview=True)
                        print(f"✅ Premium log copy successfully stored in backup channel.")
                except Exception as chan_error:
                    print(f"❌ Backup Channel logging failed: {chan_error}")

            except Exception as e:
                print(f"Message Engine Failure: {e}")

            try:
                time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
                current_time_str = time_zone.strftime("%d-%m-%Y  ⏱️ %I:%M:%S %p")            
                expiry_str_in_ist = expiry_time.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y  ⏱️ %I:%M:%S %p")  

                log_msg = (
                    f"#PREMIUM_ADDED\n\n"
                    f"👤 <b>Admin:</b> {message.from_user.mention}\n"
                    f"🎯 <b>User:</b> {user.mention}\n"
                    f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
                    f"⏰ <b>Duration:</b> {time_str}\n\n"
                    f"⏳ <b>Joining Date:</b> {current_time_str}\n"
                    f"⌛️ <b>Expiry Date:</b> {expiry_str_in_ist}"
                )
                await client.send_message(chat_id=LOG_CHANNEL, text=log_msg)
            except Exception as e:
                print(f"Log Error: {e}")
            
        else: await message.reply_text("Invalid time format.")
    else: await message.reply_text("Usage: /add_premium user_id time")

@Client.on_message(filters.command("premium_users"))
async def premium_users_info(client, message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return await message.reply("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ.")
        
    msg = await message.reply("📊 <b>Generating Premium Pipeline Report...</b>\n<i>Fetching details, please wait.</i>", parse_mode=enums.ParseMode.HTML)
    
    paid_users, ref_users, trial_users = [], [], []
    now_ist = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    
    users = await db.get_all_users()
    
    async for user in users:
        data = await db.get_user(user['id'])
        if data and data.get("expiry_time"):
            expiry = data.get("expiry_time")
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
            
            if now_ist > expiry_ist:
                await db.remove_premium_access(user['id'])
                continue
                
            p_type = data.get("premium_type", "paid") # Legacy fallback
            u_id = data.get("id")
            
            try:
                u = await client.get_users(u_id)
                name = u.first_name if u.first_name else "Unknown"
            except Exception:
                name = "Unknown User"
                
            expiry_str = expiry_ist.strftime("%d-%m-%Y %I:%M:%S %p")
            time_left = expiry_ist - now_ist
            days, remainder = time_left.days, time_left.seconds
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            entry = f"User: {name}\nID: {u_id}\nExpires: {expiry_str}\nRemaining: {days}D, {hours}H, {minutes}M\n{'-'*30}\n"
            
            if p_type == 'paid': paid_users.append(entry)
            elif p_type == 'referral': ref_users.append(entry)
            else: trial_users.append(entry)

    total_active = len(paid_users) + len(ref_users) + len(trial_users)
    
    # 1. SUMMARY FOR TELEGRAM MESSAGE
    summary = (
        f"🏆 <b>PREMIUM CRM DASHBOARD</b> 🏆\n\n"
        f"🟢 <b>Total Active Subscriptions:</b> {total_active}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>PAID VIPS (The Money Makers):</b> {len(paid_users)}\n"
        f"👥 <b>REFERRAL EARNERS:</b> {len(ref_users)}\n"
        f"⏱️ <b>ACTIVE TRIALS (Hot Leads):</b> {len(trial_users)}\n\n"
        f"<i>Full detailed list is generated in the text file below.</i>"
    )
    
    # 2. DETAILED LIST FOR TEXT FILE
    full_report = "==============================\n"
    full_report += "   PREMIUM USERS DATABASE\n"
    full_report += "==============================\n\n"
    
    full_report += f"=== 💰 PAID VIPS ({len(paid_users)}) ===\n"
    full_report += "".join(paid_users) if paid_users else "No paid users.\n"
    
    full_report += f"\n=== 👥 REFERRAL EARNERS ({len(ref_users)}) ===\n"
    full_report += "".join(ref_users) if ref_users else "No referral users.\n"
    
    full_report += f"\n=== ⏱️ ACTIVE TRIALS ({len(trial_users)}) ===\n"
    full_report += "".join(trial_users) if trial_users else "No active trials.\n"

    with open('premium_users_info.txt', 'w', encoding='utf-8') as outfile:
        outfile.write(full_report)
        
    await msg.delete()
    await message.reply_document('premium_users_info.txt', caption=summary, parse_mode=enums.ParseMode.HTML)
    os.remove('premium_users_info.txt')

@Client.on_message(filters.command("myplan"))
async def check_plans_cmd(client, message):
    user = message.from_user.mention
    user_id  = message.from_user.id
    
    if await db.has_premium_access(user_id):         
        remaining_time = await db.check_remaining_uasge(user_id)            
        days = remaining_time.days
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_remaining_time = f"{days}D, {hours}H, {minutes}M"
        
        expiry_time = remaining_time + datetime.datetime.now()
        expiry_date = expiry_time.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d %b %Y")
        
        # === PREMIUM USER DASHBOARD ===
        caption = f"""<b>👑 ᴘʀᴇᴍɪᴜᴍ ᴅᴀsʜʙᴏᴀʀᴅ</b>\n\nHello {user},\nAapka Premium account <b>Aᴄᴛɪᴠᴇ</b> hai.\n<blockquote><b>🟢 Sᴜʙsᴄʀɪᴘᴛɪᴏɴ Dᴇᴛᴀɪʟs</b>\n• <b>Sᴛᴀᴛᴜs:</b> 👑 Pʀᴇᴍɪᴜᴍ Mᴇᴍʙᴇʀ\n• <b>ID:</b> <code>{user_id}</code>\n• <b>Eхᴘɪʀʏ:</b> <code>{expiry_date}</code>\n• <b>Tɪᴍᴇ Lᴇғᴛ:</b> <code>{formatted_remaining_time}</code></blockquote>\n\n✨ <i>Tʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴄʜᴏᴏsɪɴɢ ᴘʀᴇᴍɪᴜᴍ!</i>"""
        
        btn = [[InlineKeyboardButton("❌ ᴄʟᴏꜱᴇ ❌", callback_data="close_data")]]
        
        await message.reply_photo(
            photo=MY_PLAN_IMG,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )
    else:
        # === FREE USER DASHBOARD ===
        caption = f"""<b>👤 Yᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ᴅᴀsʜʙᴏᴀʀᴅ</b>\n\nHello {user},\nAap abhi hamare <b>Bᴀsɪᴄ Pʟᴀɴ</b> par hain.\n\n<blockquote><b>🔴 Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs</b>\n• <b>Sᴛᴀᴛᴜs:</b> Fʀᴇᴇ Mᴇᴍʙᴇʀ\n• <b>ID:</b> <code>{user_id}</code>\n• <b>Aᴄᴄᴇss:</b> Sᴛᴀɴᴅᴀʀᴅ (Lɪᴍɪᴛᴇᴅ)</blockquote>\n\n⚡ <b>Wʜʏ Sᴇᴛᴛʟᴇ Fᴏʀ Bᴀsɪᴄ?</b>\nSmart users wait nahi karte! Premium me upgrade karein aur <b>ᴘʀᴇᴍɪᴜᴍ ғᴇᴀᴛᴜʀᴇs & ʙᴇɴᴇғɪᴛs turant unlock karein</b>\n\n👇 <i>Abhi Free Trial try karein ya Premium plans dekhein!</i>"""
        
        btn = [ 
            [InlineKeyboardButton("🎁 Cʟᴀɪᴍ Fʀᴇᴇ Tʀɪᴀʟ 🎁", callback_data="give_trial")],
            [InlineKeyboardButton("💎 Bᴜʏ Pʀᴇᴍɪᴜᴍ 💎", callback_data="seeplans")],
            [InlineKeyboardButton("❌ ᴄʟᴏꜱᴇ ❌", callback_data="close_data")]
        ]
        
        await message.reply_photo(
            photo=NO_PLAN_IMG,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )
		
@Client.on_message(filters.command("remove_premium"))
async def remove_premium(client, message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.reply_text("⚠️ <b>Access Denied:</b> You don't have permission to use this command.")
        return
        
    if len(message.command) == 2:
        try:
            target_user_id = int(message.command[1])
        except ValueError:
            await message.reply_text("❌ <b>Error:</b> Please provide a valid numeric User ID.")
            return
            
        try:
            user = await client.get_users(target_user_id)
        except Exception:
            await message.reply_text("❌ <b>Error:</b> User not found in database or Telegram history.")
            return

        if await db.remove_premium_access(target_user_id):
            await message.reply_text(f"✅ <b>Success:</b> Premium access removed for {user.mention}!")
            
            expiry_msg = (
                f"👋 <b>Hello, Premium User!</b>\n\n"
                f"🚨 <b>ALERT: Aapka Premium Plan Expire Ho Chuka Hai!</b> ⚠️\n\n"
                f"⚡ <b>Renew Your Plan</b> 👉 /myplan"
            )
            
            try:
                await client.send_message(chat_id=target_user_id, text=expiry_msg, parse_mode=enums.ParseMode.HTML)
            except Exception: pass
        else:
            await message.reply_text("❌ <b>Unable to remove user!</b>")
    else:
        await message.reply_text("ℹ️ <b>Usage:</b> <code>/remove_premium user_id</code>")

		
@Client.on_message(filters.command("refresh"))
async def reset_trial(client, message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.reply("ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ.")
        return
    try:
        if len(message.command) > 1:
            target_user_id = int(message.command[1])
            updated_count = await db.reset_free_trial(target_user_id)
            message_text = f"ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʀᴇꜱᴇᴛ ꜰʀᴇᴇ ᴛʀᴀɪʟ." if updated_count else f"ᴜꜱᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ."
        else:
            updated_count = await db.reset_free_trial()
            message_text = f"ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʀᴇꜱᴇᴛ ꜰʀᴇᴇ ᴛʀᴀɪʟ ꜰᴏʀ {updated_count} ᴜꜱᴇʀꜱ."
        await message.reply_text(message_text, parse_mode=enums.ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@Client.on_message(filters.command("plan"))
async def plan(client, message):
    btn = [[InlineKeyboardButton("💳 Check Plans & Pricing 💰", callback_data='free')], [InlineKeyboardButton("❌ ᴄʟᴏꜱᴇ ❌", callback_data="close_data")]]
    await message.reply_photo(photo=PLAN_CMD_IMG, caption=script.PREPLANS_TXT.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)

@Client.on_callback_query(filters.regex("^seeplans$"))
async def seeplans_button_callback(client, query):
    await query.answer() 
    
    # Back button ka callback 'start' hi rahega kyunki ye main menu se aaya hai
    btn = [[
        InlineKeyboardButton("💳 Check Plans & Pricing 💰", callback_data='free')
    ],[
        InlineKeyboardButton("🔙 Back", callback_data='start'), 
        InlineKeyboardButton("Close ❌", callback_data="close_data") 
    ]]
    
    try:
        # Purane Pricing page ko wapas Plans page mein Edit karega
        from pyrogram.types import InputMediaPhoto
        await query.message.edit_media(
            media=InputMediaPhoto(media=PREMIUM_BTN_IMG, caption=script.PREPLANS_TXT.format(query.from_user.mention), parse_mode=enums.ParseMode.HTML),
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except Exception:
        # Agar edit fail ho jaye (jaise pehli baar main menu se aate waqt), toh naya photo bhejega
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo=PREMIUM_BTN_IMG, 
            caption=script.PREPLANS_TXT.format(query.from_user.mention), 
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )
		
@Client.on_callback_query(filters.regex("^free$"))
async def free_plan_callback(client, query):
    await query.answer()
    try:
        # Yahan callback_data='seeplans' kar diya hai taaki ye Plans page par wapas jaye
        buttons = [[
            InlineKeyboardButton('👉 📸 Send Payment Screenshot', url='https://t.me/stbhai_admin')
        ],[
            InlineKeyboardButton('💎 𝗖ᴜꜱᴛᴏᴍ 𝗣ʟᴀɴ 💎', callback_data='other')
        ],[
            InlineKeyboardButton('• 𝗕𝗮𝗰𝗸 •', callback_data='seeplans'), 
            InlineKeyboardButton('Close ❌', callback_data="close_data") 
        ]]
        
        from pyrogram.types import InputMediaPhoto
        await query.message.edit_media(
            media=InputMediaPhoto(media=ALL_PLANS_PRICE_IMG, caption=script.FREE_TXT.format(query.from_user.mention), parse_mode=enums.ParseMode.HTML), 
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        print(f"Error in free_plan: {e}")
# ==========================================
# 🔥 FIXED ADD PREM TITLE (Sirf ye Naya part hai)
# ==========================================

@Client.on_message(filters.command("wipe_premium_db"))
async def wipe_premium_db(client, message):
    if message.from_user.id not in ADMINS: return
    await mydb.premium_titles.delete_many({})
    await message.reply_text("✅ <b>Database Wiped!</b>")

@Client.on_message(filters.command("add_prem_title"))
async def add_prem_title(client, message):
    if message.from_user.id not in ADMINS: return
    try:
        if message.reply_to_message and message.reply_to_message.photo:
            image_id = message.reply_to_message.photo.file_id
            cmd_text = message.text.split(" ", 1)[1] if "|" in message.text else ""
        elif message.photo:
            image_id = message.photo.file_id
            cmd_text = message.caption.split(" ", 1)[1] if "|" in message.caption else ""
        else:
            return await message.reply_text("❌ Photo reply karo ya photo ke caption mein command likho!")

        if not cmd_text:
            return await message.reply_text("❌ Format: /add_prem_title Movie | Caption")

        title, custom_text = cmd_text.split("|", 1)
        await db.add_premium_title(title.strip(), image_id, custom_text.strip())
        preview = custom_text.replace('\\n', '\n')
        await message.reply_photo(photo=image_id, caption=f"✅ <b>SAVED SUCCESSFULLY</b>\n\n{preview}")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.command("del_prem_title"))
async def del_prem_title(client, message):
    if message.from_user.id not in ADMINS: return
    title = message.text.split(" ", 1)[1]
    await db.remove_premium_title(title)
    await message.reply_text(f"🗑 {title} Removed!")

@Client.on_message(filters.command("prem_titles"))
async def list_prem_titles(client, message):
    if message.from_user.id not in ADMINS: return
    titles = await db.get_premium_titles()
    text = "💎 <b>Premium Titles:</b>\n\n" + "\n".join([f"- `{t['title']}`" for t in titles])
    await message.reply_text(text)

@Client.on_callback_query(filters.regex("^check_myplan$"))
async def check_myplan_callback(client, query):
    await query.answer()
    user = query.from_user.mention
    user_id = query.from_user.id
    
    if await db.has_premium_access(user_id):         
        remaining_time = await db.check_remaining_uasge(user_id)            
        days = remaining_time.days
        hours, remainder = divmod(remaining_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_remaining_time = f"{days}D, {hours}H, {minutes}M"
        
        expiry_time = remaining_time + datetime.datetime.now()
        expiry_date = expiry_time.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d %b %Y")
        
        # === PREMIUM USER DASHBOARD ===
        caption = f"""<b>👑 ᴘʀᴇᴍɪᴜᴍ ᴅᴀsʜʙᴏᴀʀᴅ</b>

Hello {user},
Aapka Premium account <b>Aᴄᴛɪᴠᴇ</b> hai.
<blockquote><b>🟢 Sᴜʙsᴄʀɪᴘᴛɪᴏɴ Dᴇᴛᴀɪʟs</b>
• <b>Sᴛᴀᴛᴜs:</b> 👑 Pʀᴇᴍɪᴜᴍ Mᴇᴍʙᴇʀ
• <b>ID:</b> <code>{user_id}</code>
• <b>Eхᴘɪʀʏ:</b> <code>{expiry_date}</code>
• <b>Tɪᴍᴇ Lᴇғᴛ:</b> <code>{formatted_remaining_time}</code></blockquote>

✨ <i>Tʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴄʜᴏᴏsɪɴɢ ᴘʀᴇᴍɪᴜᴍ!</i>"""
        
        btn = [[InlineKeyboardButton("🔙 Bᴀᴄᴋ Tᴏ Hᴏᴍᴇ", callback_data="start")]]
        
        try:
            from pyrogram.types import InputMediaPhoto
            await query.message.edit_media(
                media=InputMediaPhoto(media=MY_PLAN_IMG, caption=caption, parse_mode=enums.ParseMode.HTML),
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except Exception:
            pass
    else:
        # === FREE USER DASHBOARD ===
        caption = f"""<b>👤 Yᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ᴅᴀsʜʙᴏᴀʀᴅ</b>

Hello {user},
Aap abhi hamare <b>Bᴀsɪᴄ Pʟᴀɴ</b> par hain.

<blockquote><b>🔴 Cᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs</b>
• <b>Sᴛᴀᴛᴜs:</b> Fʀᴇᴇ Mᴇᴍʙᴇʀ
• <b>ID:</b> <code>{user_id}</code>
• <b>Aᴄᴄᴇss:</b> Sᴛᴀɴᴅᴀʀᴅ (Lɪᴍɪᴛᴇᴅ)</blockquote>

⚡ <b>Wʜʏ Sᴇᴛᴛʟᴇ Fᴏʀ Bᴀsɪᴄ?</b>
Smart users wait nahi karte! Premium me upgrade karein aur <b>ᴘʀᴇᴍɪᴜᴍ ғᴇᴀᴛᴜʀᴇs & ʙᴇɴᴇғɪᴛs turant unlock karein</b>

👇 <i>Abhi Free Trial try karein ya Premium plans dekhein!</i>"""
        
        btn = [ 
            [InlineKeyboardButton("🎁 Cʟᴀɪᴍ Fʀᴇᴇ Tʀɪᴀʟ 🎁", callback_data="give_trial")],
            [InlineKeyboardButton("💎 Bᴜʏ Pʀᴇᴍɪᴜᴍ 💎", callback_data="seeplans")],
            [InlineKeyboardButton("🔙 Bᴀᴄᴋ Tᴏ Hᴏᴍᴇ", callback_data="start")]
        ]
        
        try:
            from pyrogram.types import InputMediaPhoto
            await query.message.edit_media(
                media=InputMediaPhoto(media=NO_PLAN_IMG, caption=caption, parse_mode=enums.ParseMode.HTML),
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except Exception:
            pass
