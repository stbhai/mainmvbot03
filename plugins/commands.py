import logging
import random
import asyncio
import string
import pytz
from datetime import timedelta
from datetime import datetime as dt
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup , ForceReply, ReplyKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, get_bad_files, unpack_new_file_id
from database.users_chats_db import db
from database.config_db import mdb
from database.topdb import JsTopDB
from database.jsreferdb import referdb
from plugins.pm_filter import auto_filter
from utils import formate_file_name,  get_settings, save_group_settings, is_req_subscribed, get_size, get_shortlink, is_check_admin, get_status, temp, get_readable_time, save_default_settings, get_poster
import re
import base64
from info import *
import traceback
from database.jsreferdb import referdb
from datetime import timedelta
logger = logging.getLogger(__name__)
movie_series_db = JsTopDB(DATABASE_URI)
verification_ids = {}

# CHECK COMPONENTS FOLDER FOR MORE COMMANDS
@Client.on_message(filters.command("invite") & filters.private & filters.user(ADMINS))
async def invite(client, message):
    toGenInvLink = message.command[1]
    if len(toGenInvLink) != 14:
        return await message.reply("Invalid chat id\nAdd -100 before chat id if You did not add any yet.") 
    try:
        link = await client.export_chat_invite_link(toGenInvLink)
        await message.reply(link)
    except Exception as e:
        print(f'Error while generating invite link : {e}\nFor chat:{toGenInvLink}')
        await message.reply(f'Error while generating invite link : {e}\nFor chat:{toGenInvLink}')


@Client.on_message(filters.command("start") & filters.incoming, group=-1)
async def start(client:Client, message):
    user_id = message.from_user.id
    
    #   THE CRASH FIX: Variable pehle define karna zaroori tha
    is_old_user = await db.is_user_exist(user_id)
    
    # 🔥 1. USER ADDITION & MYSTERY BOX (TOP PRIORITY) 🔥
    # Isey sabse upar rakha hai taaki deep-link (getfile, refer) se aane wale users bhi miss na hon!
    if not is_old_user:
        await db.add_user(user_id, message.from_user.first_name)
        try:
            await client.send_message(LOG_CHANNEL, script.NEW_USER_TXT.format(temp.B_LINK, user_id, message.from_user.mention))
        except:
            pass
            
        # === 🔥 SILENT 1-HOUR PREMIUM FOR NORMAL NEW USERS ===
        # Pehle check karo ki user referral link (reff_) se toh nahi aaya
        is_referral = len(message.command) == 2 and message.command[1].startswith("reff_")
        
        # Agar referral se nahi aaya (normal user hai), toh automatically 1 hour trial de do bina kisi message ke
        if not is_referral:
            expiry_time = dt.now() + timedelta(hours=1)
            await db.update_user({
                "id": user_id, 
                "expiry_time": expiry_time, 
                "premium_type": "trial",
                "notified_3d": False,
                "notified_2d": False,
                "notified_1d": False
            })

    if await db.has_premium_access(user_id):
        user_status = "👑 Pʀᴇᴍɪᴜᴍ Mᴇᴍʙᴇʀ"
    else:
        user_status = "Fʀᴇᴇ Usᴇʀ"

    ist = pytz.timezone('Asia/Kolkata')
    time = dt.now(ist)
    hour = time.hour
    if 5 <= hour < 12: greeting = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ ☀️"
    elif 12 <= hour < 17: greeting = "ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ 🌤️"
    elif 17 <= hour < 21: greeting = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 🌙"
    else: greeting = "ɢᴏᴏᴅ ɴɪɢʜᴛ 😴"

    try: await message.react(emoji=random.choice(REACTIONS))
    except Exception: pass

    pm_mode = False
    try:
         data = message.command[1]
         if data.startswith('pm_mode_'):
             pm_mode = True
    except: pass
    
    m = message
    if len(m.command) == 2 and m.command[1].startswith('notcopy'):
        _, userid, verify_id, file_id = m.command[1].split("_", 3)
        user_id = int(userid)
        grp_id = temp.CHAT.get(user_id, 0)
        settings = await get_settings(grp_id)         
        verify_id_info = await db.get_verify_id_info(user_id, verify_id)
        if not verify_id_info or verify_id_info["verified"]:
            await message.reply("<b>ʟɪɴᴋ ᴇxᴘɪʀᴇᴅ ᴛʀʏ ᴀɢᴀɪɴ...</b>")
            return  
        ist_timezone = pytz.timezone('Asia/Kolkata')
        if await db.user_verified(user_id): key = "third_time_verified"
        else: key = "second_time_verified" if await db.is_user_verified(user_id) else "last_verified"
        current_time = dt.now(tz=ist_timezone)
        await db.update_notcopy_user(user_id, {key:current_time})
        await db.update_verify_id_info(user_id, verify_id, {"verified":True})
        num = 3 if key == "third_time_verified" else (2 if key == "second_time_verified" else 1) 
        msg = script.THIRDT_VERIFY_COMPLETE_TEXT if key == "third_time_verified" else (script.SECOND_VERIFY_COMPLETE_TEXT if key == "second_time_verified" else script.VERIFY_COMPLETE_TEXT)
        await client.send_message(settings['log'], script.VERIFIED_LOG_TEXT.format(m.from_user.mention, user_id, dt.now(pytz.timezone('Asia/Kolkata')).strftime('%d %B %Y'), num))
        btn = [[InlineKeyboardButton("‼️ ᴄʟɪᴄᴋ ʜᴇʀе ᴛᴏ ɢᴇᴛ ꜰɪʟе ‼️", url=f"https://telegram.me/{temp.U_NAME}?start=file_{grp_id}_{file_id}")]]
        try:
            await m.reply_photo(photo=VERIFYED_IMG, caption=msg.format(message.from_user.mention, get_readable_time(TWO_VERIFY_GAP)), reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
        except:
            await m.reply_text(text=msg.format(message.from_user.mention, get_readable_time(TWO_VERIFY_GAP)), reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML)
        return

    # === 🗺️ ROUTE A: UPGRADED REFERRED USER ENGINE (WITH AUTO-CLAIM) ===
    if len(message.command) == 2 and message.command[1].startswith("reff_"):
        if is_old_user:
            await message.reply_text("⚠️ **Aap purane member hain!** Referral bonus sirf naye users ke liye hota hai.")
            return
            
        try: 
            inviter_id = int(message.command[1].split("_")[1])
        except: 
            inviter_id = 0
            
        if inviter_id == user_id:
            return await message.reply_text("❌ **Chalaki nahi!** Aap khud ko refer nahi kar sakte.")
            
        if inviter_id != 0:
            await db.add_user(user_id, message.from_user.first_name)
            expiry_time = dt.now() + timedelta(hours=6)
            # 🔥 SALE UPDATE: 'trial' tag for 6 hours
            await db.update_user({
                "id": user_id, 
                "expiry_time": expiry_time, 
                "premium_type": "trial",
                "notified_3d": False,
                "notified_2d": False,
                "notified_1d": False
            })
            
            referdb.add_invite(inviter_id, user_id)
            
            # 🚀 THE AUTO-CLAIM LOGIC INJECTOR 🚀
            inviter_data = referdb.get_refer_data(inviter_id)
            invites = inviter_data.get('total_invites', 0)
            claimed = inviter_data.get('claimed_milestones', [])
            inf_claims = inviter_data.get('infinite_claims', 0)
            
            hours_to_add = 0
            milestone_tag = ""
            reward_name = ""
            
            # Check for milestones
            if invites == 1 and 'm1' not in claimed:
                hours_to_add, milestone_tag, reward_name = 12, "m1", "12 Hours Premium"
                next_req = 2
            elif invites == 3 and 'm2' not in claimed:
                hours_to_add, milestone_tag, reward_name = 72, "m2", "3 Days Premium"
                next_req = 4
            elif invites == 7 and 'm3' not in claimed:
                hours_to_add, milestone_tag, reward_name = 240, "m3", "10 Days Premium"
                next_req = 8
            elif invites == 15 and 'm4' not in claimed:
                hours_to_add, milestone_tag, reward_name = 720, "m4", "1 Month Premium"
                next_req = 5
            elif invites > 15 and (invites - 15) % 5 == 0 and (invites - 15) // 5 > inf_claims:
                hours_to_add, milestone_tag, reward_name = 168, "inf", "7 Days Premium"
                next_req = 5
            
            try:
                if hours_to_add > 0:
                    # Milestone Hit! (Auto-Claim condition met)
                    inviter_doc = await db.get_user(inviter_id)
                    current_expiry = inviter_doc.get("expiry_time") if inviter_doc else None
                    
                    if isinstance(current_expiry, str):
                        try: current_expiry = dt.fromisoformat(current_expiry)
                        except ValueError: current_expiry = None
                    if current_expiry and hasattr(current_expiry, "tzinfo") and current_expiry.tzinfo is not None:
                        current_expiry = current_expiry.replace(tzinfo=None)
                        
                    if current_expiry and current_expiry > dt.now():
                        new_expiry = current_expiry + timedelta(hours=hours_to_add)
                    else:
                        new_expiry = dt.now() + timedelta(hours=hours_to_add)
                        
                    await db.update_user({
                        "id": inviter_id, 
                        "expiry_time": new_expiry, 
                        "premium_type": "referral",
                        "notified_3d": False, "notified_2d": False, "notified_1d": False
                    })
                    
                    if milestone_tag == "inf": referdb.log_infinite_claim(inviter_id)
                    else: referdb.log_claimed_milestone(inviter_id, milestone_tag)
                    
                    push_msg = (
                        f"🎉 **JACKPOT! REWARD UNLOCKED!** 🎉\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"👤 {message.from_user.mention} ke join karte hi aapne naya milestone hit kar liya hai!\n\n"
                        f"🎁 **Reward Added:** `{reward_name}`\n"
                        f"⚙️ **Action:** Automatically aapke account mein add kar diya gaya hai. Koi button dabane ki zarurat nahi!\n\n"
                        f"💎 **Current Status:** Premium Member Active\n"
                        f"🚀 **Next Target:** Sirf **{next_req} invites** aur chahiye next reward ke liye.\n\n"
                        f"*Enjoy your uninterrupted high-speed access!*"
                    )
                else:
                    # Normal Invite (No Milestone Hit)
                    if invites < 1: next_req = 1 - invites
                    elif invites < 3: next_req = 3 - invites
                    elif invites < 7: next_req = 7 - invites
                    elif invites < 15: next_req = 15 - invites
                    else: next_req = 5 - ((invites - 15) % 5)
                    
                    push_msg = (
                        f"⚡ **Boom! New Referral Joined!**\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"👤 {message.from_user.mention} ne abhi aapke link se bot join kiya hai.\n\n"
                        f"📈 **Total Invites:** `{invites}` Users\n"
                        f"🎯 **Next Milestone:** Sirf **{next_req} aur invite** chahiye next Premium Reward unlock karne ke liye!\n\n"
                        f"👉 Keep sharing your link and earn more!"
                    )
                    
                await client.send_message(chat_id=inviter_id, text=push_msg)
            except Exception as e: 
                print(f"Auto-Claim Push Error: {e}")

        # 🧠 HYBRID ENGINE: Manual Override OR Auto-Fetch Smart Titles
        manual_movies = await mdb.get_configuration_value("welcome_movies")
        
        if manual_movies and len(manual_movies) >= 2:
            # 1. Admin ne Manually Set Kiya Hai (God-Mode)
            m1 = manual_movies[0]
            m2 = manual_movies[1]
        else:
            # 2. Automation: Fetch from Premium DB (Smart Length Filter)
            premium_list = await db.get_premium_titles()
            valid_movies = []
            
            if premium_list:
                premium_list.reverse() # Sabse latest pehle
                for doc in premium_list:
                    title = doc.get("title", "").strip()
                    # 🔥 UI FIX: Sirf wahi title uthayega jo 22 character se chhota ho!
                    if title and len(title) <= 22:
                        valid_movies.append(title)
                    if len(valid_movies) == 2:
                        break # 2 perfect titles mil gaye toh loop rok do
                        
            # Failsafe Fallbacks
            m1 = valid_movies[0] if len(valid_movies) > 0 else "Pushpa 2"
            m2 = valid_movies[1] if len(valid_movies) > 1 else "Stree 2"

        route_a_caption = (
            f"🎟️ <b>𝗩𝗜𝗣 𝗧𝗥𝗜𝗔𝗟 𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗘𝗗</b> 🎟️\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👋 **Hello {message.from_user.first_name}! Congratulations**\n\n"
            f"➤ Aapke friend ne aapko <b>Movie Storage Bot</b> ka Premium Invite bheja hai, isliye aapka <b>6-Hour FREE Premium Trial</b> automatically activate ho gaya hai.\n\n"
            f"⚡ <b>Current Status:</b> 6-Hours Premium\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 Ab apni favorite Movies & Web Series explore karna shuru karein!"
        )
        
        buttons = [
            [InlineKeyboardButton('  🍿 Exᴘʟᴏʀᴇ Mᴏᴠɪᴇs & Sᴇʀɪᴇs 🍿', callback_data='exp_main')],
            [InlineKeyboardButton(f'  {m1.title()}', callback_data=f'fuz#{m1}'), 
             InlineKeyboardButton(f'  {m2.title()}', callback_data=f'fuz#{m2}')],
            [InlineKeyboardButton('  🎁 Gᴇᴛ Mᴏʀᴇ Pʀᴇᴍɪᴜᴍ', callback_data='reffff'),
             InlineKeyboardButton("🔎 Sᴇᴀʀᴄʜ Mᴏᴠɪᴇs", url="https://t.me/+jUo32x8VbPdlNTE1")]
        ]
        
        await message.reply_photo(
            photo=random.choice(START_IMG), 
            caption=route_a_caption, 
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return            

        
    if len(message.command) == 2 and message.command[1].startswith('getfile'):
        searches = message.command[1].split("-", 1)[1] 
        search = searches.replace('-',' ')
        message.text = search 
        await auto_filter(client, message) 
        return

    # === 🔥 THE MAGIC AD-GATE INTERCEPTOR (SCROLL TRAP INIT) 🔥 ===
    if len(message.command) == 2 and message.command[1].startswith("adgate_"):
        try:
            data = message.command[1].replace("pm_mode_", "")
            _, chat_id, fileid = data.split("_", 2)
            
            # 👑 PREMIUM BYPASS LOGIC: Agar user premium hai toh AdGate skip kardo
            is_premium = await db.has_premium_access(message.from_user.id)
            if is_premium:
                if "batch-" in fileid:
                    real_msg_id = fileid.replace("batch-", "")
                    new_data = f"allfiles_{chat_id}-{real_msg_id}"
                else:
                    new_data = f"file_{chat_id}_{fileid}"
                
                # Command data update kar diya taaki niche wala native file sender execute ho jaye
                message.command[1] = new_data
                data = new_data 
                pass # Niche ki taraf execution continue karne do
                
            else:
                # 🆓 FREE USERS: HIGH-CONVERTING CAPTION UI
                btn = [[InlineKeyboardButton("👁️ View Ad & Unlock File 🔓", callback_data=f"adopen#{chat_id}#{fileid}")]]
                
                caption_text = (
                    f"🔒 **FILE LOCKED! (Quick Ad Check)**\n\n"
                    f"Aapki file bilkul ready hai! Server ka kharcha nikalne aur bot ko free rakhne ke liye isey ek chhote se Ad ke peeche lock kiya gaya hai.\n\n"
                    f"👉 **Bas ek chhota sa Ad dekhein aur apni file turant le lein.**\n\n"
                    f"👇 **Unlock karne ke liye niche button dabayein:**"
                )
                
                await message.reply_text(
                    text=caption_text, 
                    reply_markup=InlineKeyboardMarkup(btn),
                    parse_mode=enums.ParseMode.MARKDOWN
                )
                return
        except Exception as e:
            print(f"AdGate Error: {e}")
            pass

    # === GHOST REQUEST DEEP LINK LOGIC ===
    if len(message.command) == 2 and message.command[1].startswith('ghostreq_'):
        try: _, tmdb_id, m_char = message.command[1].split("_")
        except: return await message.reply_text("Invalid Request Format!")
                    
        m_type = "tv" if m_char == "t" else "movie"
        try: REQ_CHNL = int(REQUEST_CHANNEL)
        except: return await message.reply_text("info.py me REQUEST_CHANNEL ki ID galat hai.")

        # 🔥 THE REAL SPAM BLOCKER: API Call se pehle Database check karega
        try:
            tmdb_int = int(tmdb_id)
        except:
            tmdb_int = tmdb_id
            
        existing_req = await db.req.find_one({
            "user_id": user_id, 
            "tmdb_id": {"$in": [str(tmdb_id), tmdb_int]}
        })
        
        if existing_req:
            return await message.reply_text("⚠️ **Already Requested!** Aap is movie/series ki request pehle hi bhej chuke hain. Please upload hone ka wait karein.")
                    
        wait_msg = await message.reply_text("⏳ Fetching Data & Sending Request...")
        
        # 🔥 PRE-SAVE LOCK: TMDB se data aane me time lagta hai. 
        # Hum pehle hi DB me ek dummy entry daal rahe hain taaki agar user lagatar 'Start' dabaye, toh upar wala block usay rok de.
        await db.save_movie_request(user_id, "Fetching...", str(tmdb_id))
        
        movie = await get_poster(tmdb_id, id=True, type=m_type)
        if not movie: 
            # Agar TMDB fetch fail ho gaya, toh dummy entry uda do taaki user wapas try kar sake
            await db.req.delete_one({"user_id": user_id, "tmdb_id": str(tmdb_id)})
            return await wait_msg.edit_text("❌ Error processing request! Movie details not found.")
                    
        movie_name = movie.get('title')
        year = movie.get('year') or "N/A"
        admin_text = (
            f"🚨 **NEW UPLOAD REQUEST** 🚨\n━━━━━━━━━━━━━━━━━━\n"
            f"🎬 **Title:** `{movie_name} ({year})`\n"
            f"📺 **Type:** `{'TV Series' if m_type == 'tv' else 'Movie'}`\n━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **User:** {message.from_user.mention}\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"🔗 **TMDB ID:** `{tmdb_id}`\n━━━━━━━━━━━━━━━━━━\n"
        )
        
        admin_btn = [
            [InlineKeyboardButton("📥 Add to Queue (Leeching)", callback_data=f"req_queued#{user_id}#{tmdb_id}#{m_char}")],
            [InlineKeyboardButton("✅ Uploaded (Direct)", callback_data=f"notify_user#{user_id}#{tmdb_id}#{m_char}"),
             InlineKeyboardButton("⏳ Not Released", callback_data=f"req_notrel#{user_id}#{tmdb_id}")],
            [InlineKeyboardButton("🚫 Not Available", callback_data=f"req_notavail#{user_id}#{tmdb_id}"),
             InlineKeyboardButton("🗑 Silent Delete", callback_data="delete_admin_msg")]
        ]
        try:
            # Asli naam milne ke baad Database Update karo
            await db.save_movie_request(user_id, movie_name, str(tmdb_id))
            try:
                await client.send_photo(chat_id=REQ_CHNL, photo=movie.get('poster') or "https://i.ibb.co/HpRDS9X5/x.jpg", caption=admin_text, reply_markup=InlineKeyboardMarkup(admin_btn), parse_mode=enums.ParseMode.MARKDOWN)
            except:
                await client.send_message(chat_id=REQ_CHNL, text=admin_text, reply_markup=InlineKeyboardMarkup(admin_btn), parse_mode=enums.ParseMode.MARKDOWN)
            
            success_text = f"✅ **REQUEST SUBMITTED!**\n\n🎬 `{movie_name}`\n\nAapki request hamari admin team ko bhej di gayi hai. Jaise hi yeh file upload hogi, aapko isi bot par ek notification aa jayega. Please wait karein!"
            await wait_msg.delete()
            await message.reply_photo(photo=movie.get('poster') or "https://i.ibb.co/HpRDS9X5/x.jpg", caption=success_text, parse_mode=enums.ParseMode.MARKDOWN)
        except Exception as e:
            # Agar kisi wajah se admin ko message na jaye, toh DB se entry delete karo
            await db.req.delete_one({"user_id": user_id, "tmdb_id": str(tmdb_id)})
            await wait_msg.edit_text("❌ Error sending request! Terminal logs check kar.")
        return
    
    if len(message.command) == 2 and message.command[1] in ["ads"]:
        msg, _, impression = await mdb.get_advirtisment()
        user = await db.get_user(message.from_user.id)
        seen_ads = user.get("seen_ads", False)
        JISSHU_ADS_LINK = await db.jisshu_get_ads_link()
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('❌ ᴄʟᴏꜱᴇ ❌', callback_data='close_data')]])
        if msg:
            await message.reply_photo(photo=JISSHU_ADS_LINK if JISSHU_ADS_LINK else URL, caption=msg, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            if impression is not None and not seen_ads:
                await mdb.update_advirtisment_impression(int(impression) - 1)
                await db.update_value(message.from_user.id, "seen_ads", True)
        else:
            await message.reply("<b>No Ads Found</b>")
        await mdb.reset_advertisement_if_expired()
        if msg is None and seen_ads:
            await db.update_value(message.from_user.id, "seen_ads", False)
        return

    # 💥 THE LOCK FIX: Updating the outdated text here!
    if len(message.command) == 2 and message.command[1] == "reqprem":
        btn = [
            [InlineKeyboardButton("💎 GET PREMIUM NOW 💎", callback_data="seeplans")],
            [InlineKeyboardButton("🚫 CLOSE 🚫", callback_data="close_data")]
        ]
        
        caption = f"""
<b>🚫 1080p / 4K Files Are LOCKED! 🚫</b>

Free users ke liye sirf 480p aur 720p available hai. Ultra-HD quality ka maza lene ke liye Premium upgrade karein.

<b>💎 PREMIUM KE ASLI FAYDE:</b>
🎬 Pure 1080p & 4K Ultra-HD Prints
🚀 Unlimited Downloads (Koi Daily Limit Nahi)
🔥 Early Access (Nayi movies sabse pehle)
♾️ <i>List aur bhi lambi hai... baaki ke faayde khud 'Get Premium' me dekh lo.</i>

Saste prints dekhna chodo. Premium Member bano aur direct files lo.

👇 <b>Abhi niche click karo aur PREMIUM Access unlock karo:</b>"""

        await message.reply_photo(
            photo="https://i.ibb.co/QFwnjH5q/x.jpg",
            caption=caption,
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )
        return
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        status = get_status()
        aks=await message.reply_text(f"<b>🔥 ʏᴇs {status},\nʜᴏᴡ ᴄᴀɴ ɪ ʜᴇʟᴘ ʏᴏᴜ??</b>")
        await asyncio.sleep(600)
        await aks.delete()
        await m.delete()
        if (str(message.chat.id)).startswith("-100") and not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            group_link = await message.chat.export_invite_link()
            user = message.from_user.mention if message.from_user else "Dear" 
            await client.send_message(LOG_CHANNEL, script.NEW_GROUP_TXT.format(temp.B_LINK, message.chat.title, message.chat.id, message.chat.username, group_link, total, user))       
            await db.add_chat(message.chat.id, message.chat.title)
        return 
        
            
    # --- 2. ORGANIC ONBOARDING (/start ONLY) ---
    if len(message.command) != 2:
        buttons = [
            [InlineKeyboardButton('🎬 Explore Movies & Web Series', callback_data='exp_main')],
            [InlineKeyboardButton('🔎 Sᴇᴀʀᴄʜ Mᴏᴠɪᴇs', url="https://t.me/+jUo32x8VbPdlNTE1"), InlineKeyboardButton('📖 Search Guide', callback_data='search_guide')],
            [InlineKeyboardButton('👑 Get Premium', callback_data='seeplans'), InlineKeyboardButton('👤 My Account', callback_data='check_myplan')],
            [InlineKeyboardButton('🎁 Refer & Earn', callback_data="reffff"), InlineKeyboardButton('⚙️ Bot Settings', callback_data='features')],
            [InlineKeyboardButton('📢 Updates Channel', url='https://t.me/+1P-7PXGIyDg4MmE1'), InlineKeyboardButton('📢 Backup Channel', url='https://t.me/moviestorage_official')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        await message.reply_photo(
            photo=random.choice(START_IMG), 
            caption=script.START_TXT.format(
                greeting=greeting,
                mention=message.from_user.mention, 
                status=user_status
            ),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
        
    # --- 3. FORCESUB LOGIC (EXACTLY AS IT WAS, UNTOUCHED) ---
    fsub_status = await db.get_fsub_status(client.me.id)
    if fsub_status and AUTH_CHANNEL and not await is_req_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL), creates_join_request=True)
        except ChatAdminRequired:
            logger.error("Make Sure Bot Is Admin In Forcesub Channel")
            return
        btn = [[InlineKeyboardButton("🎗️ ᴊᴏɪɴ ɴᴏᴡ 🎗️", url=invite_link.invite_link)]]

        if message.command[1] != "subscribe":
            try:
                chksub_data = message.command[1].replace('pm_mode_', '') if pm_mode else message.command[1]
                kk, grp_id, file_id = chksub_data.split('_', 2)
                pre = 'checksubp' if kk == 'filep' else 'checksub'
                btn.append([InlineKeyboardButton("♻️ ᴛʀʏ ᴀɢᴀɪɴ ♻️", callback_data=f"checksub#{file_id}#{int(grp_id)}")])
            except (IndexError, ValueError):
                btn.append([InlineKeyboardButton("♻️ ᴛʀʏ ᴀɢᴀɪɴ ♻️", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])

        reply_markup=InlineKeyboardMarkup(btn)
        await client.send_photo(
            chat_id=message.from_user.id,
            photo=FORCESUB_IMG, 
            caption=script.FORCESUB_TEXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return

    # --- 4. MENU BUTTON CLICKS LOGIC ---
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [
            [InlineKeyboardButton('🎬 Explore Movies & Web Series', callback_data='exp_main')],
            [InlineKeyboardButton('🔎 Sᴇᴀʀᴄʜ Mᴏᴠɪᴇs', url="https://t.me/+jUo32x8VbPdlNTE1"), InlineKeyboardButton('📖 Search Guide', callback_data='search_guide')],
            [InlineKeyboardButton('👑 Get Premium', callback_data='seeplans'), InlineKeyboardButton('👤 My Account', callback_data='check_myplan')],
            [InlineKeyboardButton('🎁 Refer & Earn', callback_data="reffff"), InlineKeyboardButton('⚙️ Bot Settings', callback_data='features')],
            [InlineKeyboardButton('📢 Updates Channel', url='https://t.me/+1P-7PXGIyDg4MmE1'), InlineKeyboardButton('📢 Backup Channel', url='https://t.me/moviestorage_official')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        await message.reply_photo(
            photo=random.choice(START_IMG), 
            caption=script.START_TXT.format(
                greeting=greeting,
                mention=message.from_user.mention, 
                status=user_status
            ),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
        
    # Ye line Paste karein (Status check karne ke liye)
    fsub_status = await db.get_fsub_status(client.me.id)

    # Ye line Replace karein (Purani line ki jagah ye nayi line)
    if fsub_status and AUTH_CHANNEL and not await is_req_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL), creates_join_request=True)
        except ChatAdminRequired:
            logger.error("Make Sure Bot Is Admin In Forcesub Channel")
            return
        btn = [[
            InlineKeyboardButton("🎗️ ᴊᴏɪɴ ɴᴏᴡ 🎗️", url=invite_link.invite_link)
        ]]

        if message.command[1] != "subscribe":
            
            try:
                chksub_data = message.command[1].replace('pm_mode_', '') if pm_mode else message.command[1]
                kk, grp_id, file_id = chksub_data.split('_', 2)
                pre = 'checksubp' if kk == 'filep' else 'checksub'
                btn.append(
                    [InlineKeyboardButton("♻️ ᴛʀʏ ᴀɢᴀɪɴ ♻️", callback_data=f"checksub#{file_id}#{int(grp_id)}")]
                )
            except (IndexError, ValueError):
                print('IndexError: ', IndexError)
                btn.append(
                    [InlineKeyboardButton("♻️ ᴛʀʏ ᴀɢᴀɪɴ ♻️", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")]
                )
        reply_markup=InlineKeyboardMarkup(btn)
        await client.send_photo(
            chat_id=message.from_user.id,
            photo=FORCESUB_IMG, 
            caption=script.FORCESUB_TEXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return

    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [
            [InlineKeyboardButton('🎬 Explore Movies & Web Series', callback_data='exp_main')],
            [InlineKeyboardButton('🔎 Sᴇᴀʀᴄʜ Mᴏᴠɪᴇs', url="https://t.me/+jUo32x8VbPdlNTE1"), InlineKeyboardButton('📖 Search Guide', callback_data='search_guide')],
            [InlineKeyboardButton('👑 Get Premium', callback_data='seeplans'), InlineKeyboardButton('👤 My Account', callback_data='check_myplan')],
            [InlineKeyboardButton('🎁 Refer & Earn', callback_data="reffff"), InlineKeyboardButton('⚙️ Bot Settings', callback_data='features')],
            [InlineKeyboardButton('📢 Updates Channel', url='https://t.me/+1P-7PXGIyDg4MmE1'), InlineKeyboardButton('📢 Backup Channel', url='https://t.me/moviestorage_official')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)

        # Caption update (Format check karein)
        await message.reply_photo(
            photo=random.choice(START_IMG), 
            caption=script.START_TXT.format(
                greeting=greeting,
                mention=message.from_user.mention, 
                status=user_status
            ),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        
    if data.startswith('pm_mode_'):
        pm_mode = True
        data = data.replace('pm_mode_', '')
    try:
        pre, grp_id, file_id = data.split('_', 2)
    except:
        pre, grp_id, file_id = "", 0, data
        
    # 🔥 THE FATAL BUG FIX: Dono users (Free + Premium) ke liye grp_id int mein convert hoga
    try:
        grp_id = int(grp_id)
    except:
        grp_id = 0

    user_id = m.from_user.id
    if not await db.has_premium_access(user_id):
        user_verified = await db.is_user_verified(user_id)
        settings = await get_settings(grp_id , pm_mode=pm_mode)
        is_second_shortener = await db.use_second_shortener(user_id, settings.get('verify_time', TWO_VERIFY_GAP)) 
        is_third_shortener = await db.use_third_shortener(user_id, settings.get('third_verify_time', THREE_VERIFY_GAP))
        is_verify_enabled = False

        if is_verify_enabled and (not user_verified or is_second_shortener or is_third_shortener):
            verify_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
            await db.create_verify_id(user_id, verify_id)
            temp.CHAT[user_id] = grp_id
            verify = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=notcopy_{user_id}_{verify_id}_{file_id}", grp_id, is_second_shortener, is_third_shortener , pm_mode=pm_mode)
            if is_third_shortener:
                howtodownload = settings.get('tutorial_3', TUTORIAL_3)
            else:
                howtodownload = settings.get('tutorial_2', TUTORIAL_2) if is_second_shortener else settings.get('tutorial', TUTORIAL)
            buttons = [[
                InlineKeyboardButton(text="✅ ᴠᴇʀɪғʏ ✅", url=verify),
                InlineKeyboardButton(text="ʜᴏᴡ ᴛᴏ ᴠᴇʀɪғʏ❓", url=howtodownload)
                ],[
                InlineKeyboardButton(text="😁 ʙᴜʏ sᴜʙsᴄʀɪᴘᴛɪᴏɴ - ɴᴏ ɴᴇᴇᴅ ᴛᴏ ᴠᴇʀɪғʏ 😁", callback_data='seeplans'),
            ]]
            reply_markup=InlineKeyboardMarkup(buttons)
            if await db.user_verified(user_id): 
                msg = script.THIRDT_VERIFICATION_TEXT
            else:            
                msg = script.SECOND_VERIFICATION_TEXT if is_second_shortener else script.VERIFICATION_TEXT
            
            try:
                d = await m.reply_photo(
                    photo=VERIFY_IMG,
                    caption=msg.format(message.from_user.mention, get_status()),
                    reply_markup=reply_markup,
                    parse_mode=enums.ParseMode.HTML
                )
            except Exception as e:
                print(f"2nd Image Error: {e}")
                d = await m.reply_text(
                    text=msg.format(message.from_user.mention, get_status()),
                    reply_markup=reply_markup,
                    parse_mode=enums.ParseMode.HTML
                )
            
            await asyncio.sleep(300) 
            await d.delete()
            await m.delete()
            return

    if data and data.startswith("allfiles"):
        _, key = data.split("_", 1)
        files = temp.FILES_ID.get(key)
        if not files:
            await message.reply_text("<b>⚠️ ᴀʟʟ ꜰɪʟᴇs ɴᴏᴛ ꜰᴏᴜɴᴅ ⚠️</b>")
            return
            
        files_to_delete = []
        for file in files:
            user_id = message.from_user.id 
            # 🔥 SAFE FALLBACK: Agar chat id nahi mili toh 0 pass hoga, crash nahi.
            grp_id = temp.CHAT.get(user_id, 0) 
            settings = await get_settings(grp_id, pm_mode=pm_mode)
            CAPTION = settings['caption']
            raw_caption = getattr(file, 'caption', None)
            if not raw_caption or str(raw_caption).strip() == "":
                raw_caption = file.file_name
            f_caption = CAPTION.format(
                file_name=raw_caption,
                file_size=get_size(file.file_size),
                file_caption=file.caption
            )
            btn = [[
                InlineKeyboardButton("Movie Storage Official", url=f'https://t.me/moviestorage_official')
            ]]
            toDel = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file.file_id,
                caption=f_caption,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            files_to_delete.append(toDel)

        is_premium = await db.has_premium_access(message.from_user.id)
        if is_premium:
            delCap = (
                "👑 <b>Premium Access:</b>\n\n"
                "Aap Premium user hain, isliye ye files aapke liye <b>delete nahi hongi</b>. Ab seedha download karein aur enjoy karein! 🍿\n\n"
                "🔈 <b>Audio Problem (No Sound)?</b>\n"
                "Agar video mein awaaz nahi aa rahi, toh file ko <b>'Save to Downloads'</b> karein aur VLC Player download karke usme open karein:\n <b>Download Now</b> 👉 <a href='https://play.google.com/store/apps/details?id=org.videolan.vlc'>Android</a> | <a href='https://apps.apple.com/app/vlc-media-player/id650377962'>iOS</a>"
            )
            return await message.reply(delCap, disable_web_page_preview=True)
        else:
            time_str = f'{FILE_AUTO_DEL_TIMER / 60} ᴍɪɴᴜᴛᴇs' if FILE_AUTO_DEL_TIMER >= 60 else f'{FILE_AUTO_DEL_TIMER} sᴇᴄᴏɴᴅs'
            
            delCap = (
                f"⚠️ <b>Important Notice:</b>\n"
                f"Copyright issues ke karan ye <b>{len(files_to_delete)} files</b> theek <b>{time_str}</b> mein 🗑 <i>automatically delete</i> ho jayengi.\n\n"
                f"✅ <b>Files ko Save kaise karein?</b>\n"
                f"👉 Ise turant apne kisi dost ko <b>Forward ➡</b> kar dein.\n"
                f"👉 Ya fir apne <b>'Saved Messages'</b> mein forward kar lein.\n\n"
                f"🔈 <b>Audio Problem (No Sound)?</b>\n"
                f"Agar video play karne par awaaz nahi aa rahi, toh file ko pehle <b>'Save to Downloads'</b> karein aur VLC Player download karke usme open karein:\n <b>Download Now</b> 👉 <a href='https://play.google.com/store/apps/details?id=org.videolan.vlc'>Android</a> | <a href='https://apps.apple.com/app/vlc-media-player/id650377962'>iOS</a>\n\n"
                f"⏳ <i>Jaldi karein, warna file Delete ho jayegi!</i>"
            )
            
            afterDelCap = f"🗑 <b>Files Delete Ho Chuki Hain!</b>\n\nAgar aap inhe save karna bhool gaye the, toh kripya wapas group mein jakar search karein."
            
            replyed = await message.reply(delCap, disable_web_page_preview=True)
            await asyncio.sleep(FILE_AUTO_DEL_TIMER)
            
            for file in files_to_delete:
                try:
                    await file.delete()
                except:
                    pass
            return await replyed.edit(afterDelCap)
            
    if not data:
        return
        
    files_ = await get_file_details(file_id)               
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        return await message.reply('<b>⚠️ ᴀʟʟ ꜰɪʟᴇs ɴᴏᴛ ꜰᴏᴜɴᴅ ⚠️</b>')
    
    files = files_[0]

    settings = await get_settings(grp_id , pm_mode=pm_mode)
    CAPTION = settings['caption']
    raw_caption = getattr(files, 'caption', None)
    if not raw_caption or str(raw_caption).strip() == "":
        raw_caption = files.file_name
    f_caption = CAPTION.format(
        file_name=raw_caption,
        file_size = get_size(files.file_size),
        file_caption=files.caption
    )
    btn = [[
        InlineKeyboardButton("Movie Storage Official", url=f'https://t.me/moviestorage_official')
    ]]
    toDel=await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        reply_markup=InlineKeyboardMarkup(btn)
    )
    
    is_premium = await db.has_premium_access(message.from_user.id)
    if is_premium:
        delCap = (
            "👑 <b>Premium Access:</b>\n\n"
            "Aap Premium user hain, isliye ye file aapke liye <b>delete nahi hogi</b>. Ab seedha download karein aur enjoy karein! 🍿\n\n"
            "🔈 <b>Audio Problem (No Sound)?</b>\n"
            "Agar video play karne par awaaz nahi aa rahi, toh file ko pehle <b>'Save to Downloads'</b> karein aur VLC Player download karke usme open karein:\n <b>Download Now</b> 👉 <a href='https://play.google.com/store/apps/details?id=org.videolan.vlc'>Android</a> | <a href='https://apps.apple.com/app/vlc-media-player/id650377962'>iOS</a>"
        )
        return await message.reply(delCap, reply_to_message_id=toDel.id, disable_web_page_preview=True)
    else:
        time_str = f'{FILE_AUTO_DEL_TIMER / 60} ᴍɪɴᴜᴛᴇs' if FILE_AUTO_DEL_TIMER >= 60 else f'{FILE_AUTO_DEL_TIMER} sᴇᴄᴏɴᴅs'
        
        delCap = (
            f"⚠️ <b>Important Notice:</b>\n"
            f"Copyright issues ke karan ye file theek <b>{time_str}</b> mein 🗑 <i>automatically delete</i> ho jayegi.\n\n"
            f"✅ <b>File ko Save kaise karein?</b>\n"
            f"👉 Ise turant apne kisi dost ko <b>Forward ➡</b> kar dein.\n"
            f"👉 Ya fir apne <b>'Saved Messages'</b> mein forward kar lein.\n\n"
            f"🔈 <b>Audio Problem (No Sound)?</b>\n"
            f"Agar video play karne par awaaz nahi aa rahi, toh file ko pehle <b>'Save to Downloads'</b> karein aur VLC Player download karke usme open karein:\n <b>Download Now</b> 👉 <a href='https://play.google.com/store/apps/details?id=org.videolan.vlc'>Android</a> | <a href='https://apps.apple.com/app/vlc-media-player/id650377962'>iOS</a>\n\n"
            f"⏳ <i>Jaldi karein, warna file Delete ho jayegi!</i>"
        )
        
        afterDelCap = f"🗑 <b>File Delete Ho Chuki Hai!</b>\n\nAgar aap ise save karna bhool gaye the, toh kripya wapas group mein jakar search karein."
        
        replyed = await message.reply(delCap, reply_to_message_id=toDel.id, disable_web_page_preview=True)
        await asyncio.sleep(FILE_AUTO_DEL_TIMER)
        await toDel.delete()
        return await replyed.edit(afterDelCap)

@Client.on_message(filters.command('delete'))
async def delete(bot, message):
    if message.from_user.id not in ADMINS:
        await message.reply('ᴏɴʟʏ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ... 😑')
        return
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("ᴘʀᴏᴄᴇssɪɴɢ...⏳", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return
    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('<b>ᴛʜɪs ɪs ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ ꜰɪʟᴇ ꜰᴏʀᴍᴀᴛ</b>')
        return
    
    file_id, file_ref = unpack_new_file_id(media.file_id)
    result = await Media.collection.delete_one({
        '_id': file_id,
    })
    if result.deleted_count:
        await msg.edit('<b>ꜰɪʟᴇ ɪs sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ 💥</b>')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count:
            await msg.edit('<b>ꜰɪʟᴇ ɪs sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ 💥</b>')
        else:
            result = await Media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count:
                await msg.edit('<b>ꜰɪʟᴇ ɪs sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ 💥</b>')
            else:
                await msg.edit('<b>ꜰɪʟᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀsᴇ</b>')

@Client.on_message(filters.command('deleteall'))
async def delete_all_index(bot, message):
    files = await Media.count_documents()
    if int(files) == 0:
        return await message.reply_text('Not have files to delete')
    btn = [[
            InlineKeyboardButton(text="ʏᴇs", callback_data="all_files_delete")
        ],[
            InlineKeyboardButton(text="ᴄᴀɴᴄᴇʟ", callback_data="close_data")
        ]]
    if message.from_user.id not in ADMINS:
        await message.reply('ᴏɴʟʏ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ... 😑')
        return
    await message.reply_text('<b>ᴛʜɪs ᴡɪʟʟ ᴅᴇʟᴇᴛᴇ ᴀʟʟ ɪɴᴅᴇxᴇᴅ ꜰɪʟᴇs.\nᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ??</b>', reply_markup=InlineKeyboardMarkup(btn))

@Client.on_message(filters.command('settings'))
async def settings(client, message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return await message.reply("<b>💔 ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ...</b>")
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<code>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜ force.</code>")
    grp_id = message.chat.id
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    settings = await get_settings(grp_id)
    title = message.chat.title
    if settings is not None:
            buttons = [[
                InlineKeyboardButton('ᴀᴜᴛᴏ ꜰɪʟᴛᴇʀ', callback_data=f'setgs#auto_filter#{settings["auto_filter"]}#{grp_id}'),
                InlineKeyboardButton('ᴏɴ ✓' if settings["auto_filter"] else 'ᴏғғ ✗', callback_data=f'setgs#auto_filter#{settings["auto_filter"]}#{grp_id}')
            ],[
                InlineKeyboardButton('ɪᴍᴅʙ', callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}'),
                InlineKeyboardButton('ᴏɴ ✓' if settings["imdb"] else 'ᴏғғ ✗', callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}')
            ],[
                InlineKeyboardButton('sᴘᴇʟʟ ᴄʜᴇᴄᴋ', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}'),
                InlineKeyboardButton('ᴏɴ ✓' if settings["spell_check"] else 'ᴏғғ ✗', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}')
            ],[
                InlineKeyboardButton('ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}'),
                InlineKeyboardButton(f'{get_readable_time(DELETE_TIME)}' if settings["auto_delete"] else 'ᴏғғ ✗', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}')
            ],[
                InlineKeyboardButton('ʀᴇsᴜʟᴛ ᴍᴏᴅᴇ', callback_data=f'setgs#link#{settings["link"]}#{str(grp_id)}'),
                InlineKeyboardButton('⛓ ʟɪɴᴋ' if settings["link"] else '🧲 ʙᴜᴛᴛᴏɴ', callback_data=f'setgs#link#{settings["link"]}#{str(grp_id)}')
            ],[
                InlineKeyboardButton('❌ ᴄʟᴏsᴇ ❌', callback_data='close_data')
            ]]
            await message.reply_text(
                text=f"ᴄʜᴀɴɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ꜰᴏʀ <b>'{title}'</b> ᴀs ʏᴏᴜʀ ᴡɪsʜ ✨",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.HTML
            )
    else:
        await message.reply_text('<b>ꜱᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ</b>')

@Client.on_message(filters.command('set_template'))
async def save_template(client, message):
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    try:
        template = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("Command Incomplete!")    
    await save_group_settings(grp_id, 'template', template)
    await message.reply_text(f"Successfully changed template for {title} to\n\n{template}", disable_web_page_preview=True)
    
@Client.on_message(filters.command("send"))
async def send_msg(bot, message):
    if message.from_user.id not in ADMINS:
        await message.reply('<b>ᴏɴʟʏ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ...</b>')
        return
    if message.reply_to_message:
        target_ids = message.text.split(" ")[1:]
        if not target_ids:
            await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴏɴᴇ ᴏʀ ᴍᴏʀᴇ ᴜꜱᴇʀ ɪᴅꜱ ᴀꜱ ᴀ ꜱᴘᴀᴄᴇ...</b>")
            return
        out = "\n\n"
        success_count = 0
        try:
            users = await db.get_all_users()
            for target_id in target_ids:
                try:
                    user = await bot.get_users(target_id)
                    out += f"{user.id}\n"
                    await message.reply_to_message.copy(int(user.id))
                    success_count += 1
                except Exception as e:
                    out += f"‼️ ᴇʀʀᴏʀ ɪɴ ᴛʜɪꜱ ɪᴅ - <code>{target_id}</code> <code>{str(e)}</code>\n"
            await message.reply_text(f"<b>✅️ ꜱᴜᴄᴄᴇꜱꜱfully ᴍᴇꜱꜱᴀɢе ꜱеɴᴛ ɪɴ `{success_count}` ɪᴅ\n<code>{out}</code></b>")
        except Exception as e:
            await message.reply_text(f"<b>‼️ ᴇʀʀᴏʀ - <code>{e}</code></b>")
    else:
        await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴀꜱ ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴍᴇꜱꜱᴀɢᴇ, ꜰᴏʀ ᴇɢ - <code>/send userid1 userid2</code></b>")

@Client.on_message(filters.command("request"))
async def send_request(bot, message):
    try:
        request = message.text.split(" ", 1)[1]
    except:
        await message.reply_text("<b>‼️ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ɪɴᴄᴏᴍᴘʟᴇᴛᴇ</b>")
        return
    buttons = [[
        InlineKeyboardButton('👀 ᴠɪᴇᴡ ʀᴇǫᴜᴇꜱᴛ 👀', url=f"{message.link}")
    ],[
        InlineKeyboardButton('⚙ sʜᴏᴡ ᴏᴘᴛɪᴏɴ ⚙', callback_data=f'show_options#{message.from_user.id}#{message.id}')
    ]]
    sent_request = await bot.send_message(REQUEST_CHANNEL, script.REQUEST_TXT.format(message.from_user.mention, message.from_user.id, request), reply_markup=InlineKeyboardMarkup(buttons))
    btn = [[
         InlineKeyboardButton('✨ ᴠɪᴇᴡ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ✨', url=f"{sent_request.link}")
    ]]
    await message.reply_text("<b>✅ sᴜᴄᴄᴇssғᴜʟʟʏ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ᴀᴅᴅᴇᴅ, ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ꜱᴏᴍᴇᴛɪᴍᴇ...</b>", reply_markup=InlineKeyboardMarkup(btn))

@Client.on_message(filters.command("search"))
async def search_files(bot, message):
    if message.from_user.id not in ADMINS:
        await message.reply('Only the bot owner can use this command... 😑')
        return
    chat_type = message.chat.type
    if chat_type != enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>Hey {message.from_user.mention}, this command won't work in groups. It only works in my PM!</b>")  
    try:
        keyword = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply_text(f"<b>Hey {message.from_user.mention}, give me a keyword along with the command to delete files.</b>")
    files, total = await get_bad_files(keyword)
    if int(total) == 0:
        await message.reply_text('<i>I could not find any files with this keyword 😐</i>')
        return 
    file_names = "\n\n".join(f"{index + 1}. {item['file_name']}" for index, item in enumerate(files))
    file_data = f"🚫 Your search - '{keyword}':\n\n{file_names}"    
    with open("file_names.txt", "w" , encoding='utf-8') as file:
        file.write(file_data)
    await message.reply_document(
        document="file_names.txt",
        caption=f"<b>♻️ ʙʏ ʏᴏᴜʀ ꜱᴇᴀʀᴄʜ, ɪ ꜰᴏᴜɴᴅ - <code>{total}</code> ꜰɪʟᴇs</b>",
        parse_mode=enums.ParseMode.HTML
    )
    os.remove("file_names.txt")

@Client.on_message(filters.command("deletefiles"))
async def deletemultiplefiles(bot, message):
    if message.from_user.id not in ADMINS:
        await message.reply('ᴏɴʟʏ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ... 😑')
        return
    chat_type = message.chat.type
    if chat_type != enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention}, ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏɴ'ᴛ ᴡᴏʀᴋ ɪɴ ɢʀᴏᴜᴘs. ɪᴛ ᴏɴʟʏ ᴡᴏʀᴋs ᴏɴ ᴍʏ ᴘᴍ !!</b>")
    else:
        pass
    try:
        keyword = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention}, ɢɪᴠᴇ ᴍᴇ ᴀ ᴋᴇʏᴡᴏʀᴅ ᴀʟᴏɴɢ ᴡɪᴛʜ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ꜰɪʟᴇs.</b>")
    files, total = await get_bad_files(keyword)
    if int(total) == 0:
        await message.reply_text('<i>ɪ ᴄᴏᴜʟᴅ ɴᴏᴛ ꜰɪɴᴅ ᴀɴʏ ꜰɪʟᴇs ᴡɪᴛʜ ᴛʜɪs ᴋᴇʏᴡᴏʀᴅ 😐</i>')
        return 
    btn = [[
       InlineKeyboardButton("ʏᴇs, ᴄᴏɴᴛɪɴᴜᴇ ✅", callback_data=f"killfilesak#{keyword}")
       ],[
       InlineKeyboardButton("¼ᴏ, ᴀʙᴏʀᴛ ᴏᴘᴇʀᴀᴛɪᴏɴ  operativa 😢", callback_data="close_data")
    ]]
    await message.reply_text(
        text=f"<b>ᴛᴏᴛᴀʟ ꜰɪʟᴇs ꜰᴏᴜɴᴅ - <code>{total}</code>\n\nᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ?\n\nɴᴏᴛᴇ:- ᴛʜɪs ᴄᴏᴜʟᴅ ʙᴇ ᴀ ᴅᴇsᴛʀᴜᴄᴛɪᴠᴇ ᴀᴄᴛɪᴏɴ!!</b>",
        reply_markup=InlineKeyboardMarkup(btn),
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.command("del_file"))
async def delete_files(bot, message):
    if message.from_user.id not in ADMINS:
        await message.reply('Only the bot owner can use this command... 😑')
        return
    chat_type = message.chat.type
    if chat_type != enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>Hey {message.from_user.mention}, this command won't work in groups. It only works on my PM!</b>")    
    try:
        keywords = message.text.split(" ", 1)[1].split(",")
    except IndexError:
        return await message.reply_text(f"<b>Hey {message.from_user.mention}, give me keywords separated by commas along with the command to delete files.</b>")   
    deleted_files_count = 0
    not_found_files = []
    for keyword in keywords:
        result = await Media.collection.delete_many({'file_name': keyword.strip()})
        if result.deleted_count:
            deleted_files_count += 1
        else:
            not_found_files.append(keyword.strip())
    if deleted_files_count > 0:
        await message.reply_text(f'<b>{deleted_files_count} file successfully deleted from the database 💥</b>')
    if not_found_files:
        await message.reply_text(f'<b>Files not found in the database - <code>{", ".join(not_found_files)}</code></b>')

@Client.on_message(filters.command('set_caption'))
async def save_caption(client, message):
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    try:
        caption = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("Command Incomplete!")
    await save_group_settings(grp_id, 'caption', caption)
    await message.reply_text(f"Successfully changed caption for {title} to\n\n{caption}", disable_web_page_preview=True) 
    
@Client.on_message(filters.command('set_tutorial'))
async def save_tutorial(client, message):
    grp_id = message.chat.id
    title = message.chat.title
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    try:
        tutorial = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("<b>Command Incomplete!!\n\nuse like this -</b>\n\n<code>/set_caption https://t.me/+4uFxyl0TAL0xMTg0</code>")    
    await save_group_settings(grp_id, 'tutorial', tutorial)
    await message.reply_text(f"<b>Successfully Changed 1st Verification Tutorial For {title} To</b>\n\n{tutorial}", disable_web_page_preview=True)

@Client.on_message(filters.command('set_tutorial_2'))
async def set_tutorial_2(client, message):
    grp_id = message.chat.id
    title = message.chat.title
    invite_link = await client.export_chat_invite_link(grp_id)
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text(f"<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...\n\nGroup Name: {title}\nGroup ID: {grp_id}\nGroup Invite Link: {invite_link}</b>")
    try:
        tutorial = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("<b> may ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ !!\n\nᴜꜱᴇ ʟɪᴋᴇ ᴛʜɪꜱ -</b>\n\n<code>/set_tutorial_2 https://t.me/DwldMS/2</code>")
    await save_group_settings(grp_id, 'tutorial_2', tutorial)
    await message.reply_text(f"<b>Successfully Changed 2nd Verification Tutorial For {title} To</b>\n\n{tutorial}", disable_web_page_preview=True)
    
@Client.on_message(filters.command('set_tutorial_3'))
async def set_tutorial_3(client, message):
    grp_id = message.chat.id
    title = message.chat.title
    invite_link = await client.export_chat_invite_link(grp_id)
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text(f"<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...\n\nGroup Name: {title}\nGroup ID: {grp_id}\nGroup Invite Link: {invite_link}</b>")
    try:
        tutorial = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("<b>Command Incomplete!!\n\nuse like this -</b>\n\n<code>/set_tutorial https://t.me/Aksbackup</code>")
    await save_group_settings(grp_id, 'tutorial_3', tutorial)
    await message.reply_text(f"<b>Successfully Changed 3rd Verification Tutorial For {title} To</b>\n\n{tutorial}", disable_web_page_preview=True)

@Client.on_message(filters.command('set_verify'))
async def set_shortner(c, m):
    grp_id = m.chat.id
    chat_type = m.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await m.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    if not await is_check_admin(c, grp_id, m.from_user.id):
        return await m.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')        
    if len(m.text.split()) == 1:
        await m.reply("<b>Use this command like this - \n\n`/set_shortner tnshort.net 06b24eb6bbb025713cd522fb3f696b6d5de11354`</b>")
        return        
    sts = await m.reply("<b>♻️ ᴄʜᴇᴄᴋɪɴɢ...</b>")
    await asyncio.sleep(1.2)
    await sts.delete()
    try:
        URL = m.command[1]
        API = m.command[2]
        resp = requests.get(f'https://{URL}/api?api={API}&url=https://telegram.dog/Jisshu_support').json()
        if resp['status'] == 'success':
            SHORT_LINK = resp['shortenedUrl']
        await save_group_settings(grp_id, 'shortner', URL)
        await save_group_settings(grp_id, 'api', API)
        await m.reply_text(f"<b><u>✓ sᴜᴄᴄᴇssꜰᴜʟʟʏ 🇳🇬 ʏᴏᴜʀ sʜᴏʀᴛɴᴇʀ ɪs ᴀᴅᴅᴇᴅ</u>\n\nᴅᴇᴍᴏ - {SHORT_LINK}\n\nsɪᴛᴇ - `{URL}`\n\nᴀᴘɪ - `{API}`</b>", quote=True)
        user_id = m.from_user.id
        user_info = f"@{m.from_user.username}" if m.from_user.username else f"{m.from_user.mention}"
        link = (await c.get_chat(m.chat.id)).invite_link
        grp_link = f"[{m.chat.title}]({link})"
        log_message = f"#New_Shortner_Set_For_1st_Verify\n\nName - {user_info}\nId - `{user_id}`\n\nDomain name - {URL}\nApi - `{API}`\nGroup link - {grp_link}"
        await c.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
    except Exception as e:
        await save_group_settings(grp_id, 'shortner', SHORTENER_WEBSITE)
        await save_group_settings(grp_id, 'api', SHORTENER_API)
        await m.reply_text(f"<b><u>💢 ᴇʀʀᴏʀ ᴏᴄᴄᴏᴜʀᴇᴅ!!</u>\n\nᴀᴜᴛᴏ ᴀᴅᴅᴇᴅ ʙᴏᴛ ᴏᴡɴᴇʀ ᴅᴇꜰᴜʟᴛ sʜᴏʀᴛɴᴇʀ\n\nɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʜᴀɴɢᴇ ᴛʜेɴ ᴜsе ᴄᴏʀʀеᴄᴛ ꜰᴏʀᴍᴀᴛ ᴏʀ ᴀᴅᴅ ᴠᴀʟɪᴅ sʜᴏʀᴛʟɪɴᴋ ᴅᴏᴍᴀɪɴ ɴᴀᴍе & ᴀᴘɪ\n\nʏᴏu ᴄᴀɴ ᴀʟsᴏ ᴄᴏɴᴛᴀᴄᴛ ᴏᴜʀ <a href=https://t.me/+4uFxyl0TAL0xMTg0>sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ</a> ꜰᴏʀ sᴏʟᴠᴇ ᴛʜɪs ɪssᴜᴇ...\n\nʟɪᴋе -\n\n`/set_shortner mdiskshortner.link e7beb3c8f756dfa15d0bec495abc65f58c0dfa95`\n\n💔 ᴇʀʀᴏʀ - <code>{e}</code></b>", quote=True)

@Client.on_message(filters.command('set_verify_2'))
async def set_shortner_2(c, m):
    grp_id = m.chat.id
    chat_type = m.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await m.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    if not await is_check_admin(c, grp_id, m.from_user.id):
        return await m.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    if len(m.text.split()) == 1:
        await m.reply("<b>Use this command like this - \n\n`/set_shortner_2 tnshort.net 06b24eb6bbb025713cd522fb3f696b6d5de11354`</b>")
        return
    sts = await m.reply("<b>♻️ ᴄʜᴇᴄᴋɪɴɢ...</b>")
    await asyncio.sleep(1.2)
    await sts.delete()
    try:
        URL = m.command[1]
        API = m.command[2]
        resp = requests.get(f'https://{URL}/api?api={API}&url=https://telegram.dog/bisal_files').json()
        if resp['status'] == 'success':
            SHORT_LINK = resp['shortenedUrl']
        await save_group_settings(grp_id, 'shortner_two', URL)
        await save_group_settings(grp_id, 'api_two', API)
        await m.reply_text(f"<b><u>✅ sᴜᴄᴄеssꜰᴜʟʟʏ ʏᴏᴜʀ sʜᴏʀᴛɴᴇʀ ɪs ᴀᴅᴅᴇᴅ</u>\n\nᴅеᴍᴏ - {SHORT_LINK}\n\nsɪᴛе - `{URL}`\n\nᴀᴘɪ - `{API}`</b>", quote=True)
        user_id = m.from_user.id
        user_info = f"@{m.from_user.username}" if m.from_user.username else f"{m.from_user.mention}"
        link = (await c.get_chat(m.chat.id)).invite_link
        grp_link = f"[{m.chat.title}]({link})"
        log_message = f"#New_Shortner_Set_For_2nd_Verify\n\nName - {user_info}\nId - `{user_id}`\n\nDomain name - {URL}\nApi - `{API}`\nGroup link - {grp_link}"
        await c.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
    except Exception as e:
        await save_group_settings(grp_id, 'shortner_two', SHORTENER_WEBSITE2)
        await save_group_settings(grp_id, 'api_two', SHORTENER_API2)
        await m.reply_text(f"<b><u>💢 ᴇʀʀᴏʀ ᴏᴄᴄᴏᴜʀеᴅ!!</u>\n\nᴀᴜᴛo ᴀᴅᴅеᴅ ʙᴏᴛ ᴏᴡɴеr ᴅеꜰᴜʟᴛ sʜᴏʀᴛɴеr\n\nɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛo ᴄʜᴀɴɢе ᴛʜеɴ ᴜsе ᴄᴏʀʀеᴄᴛ ꜰᴏʀᴍᴀᴛ ᴏʀ ᴀᴅᴅ ᴠᴀʟɪᴅ sʜshortʟɪɴᴋ ᴅᴏᴍᴀɪɴ ɴᴀᴍе & ᴀᴘɪ\n\nʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ ᴄᴏɴᴛᴀᴄᴛ ᴏᴜʀ <a href=https://t.me/+4uFxyl0TAL0xMTg0>sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ</a> ꜰᴏʀ sᴏʟᴠᴇ ᴛʜɪs ɪssᴜᴇ...\n\n饰 ʟɪᴋе -\n\n`/set_shortner_2 mdiskshortner.link e7beb3c8f756dfa15d0bec495abc65f58c0dfa95`\n\n💔 ᴇʀʀᴏʀ - <code>{e}</code></b>", quote=True)

@Client.on_message(filters.command('set_verify_3'))
async def set_shortner_3(c, m):
    chat_type = m.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await m.reply_text("<b>Use this command in Your group ! Not in Private</b>")
    if len(m.text.split()) == 1:
        return await m.reply("<b>Use this command like this - \n\n`/set_shortner_3 tnshort.net 06b24eb6bbb025713cd522fb3f696b6d5de11354`</b>")
    sts = await m.reply("<b>♻️ ᴄʜᴇᴄᴋɪɴɢ...</b>")
    await sts.delete()
    userid = m.from_user.id if m.from_user else None
    if not userid:
        return await m.reply(f"<b>⚠️ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ᴏꜰ ᴛʜɪs ɢʀᴏᴜᴘ</b>")
    grp_id = m.chat.id
    #check if user admin or not
    if not await is_check_admin(c, grp_id, userid):
        return await m.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    if len(m.command) == 1:
        await m.reply_text("<b>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴀᴅᴅ sʜᴏʀᴛɴᴇʀ & ᴀᴘɪ\n\nᴇx - `/set_shortner_3 mdiskshortner.link e7beb3c8f756dfa15d0bec495abc65f58c0dfa95`</b>", quote=True)
        return
    try:
        URL = m.command[1]
        API = m.command[2]
        resp = requests.get(f'https://{URL}/api?api={API}&url=https://telegram.dog/Jisshu_support').json()
        if resp['status'] == 'success':
            SHORT_LINK = resp['shortenedUrl']
        await save_group_settings(grp_id, 'shortner_three', URL)
        await save_group_settings(grp_id, 'api_three', API)
        await m.reply_text(f"<b><u>✅ sᴜᴄᴄеssꜰᴜʟʟʏ ʏᴏᴜʀ sʜᴏʀᴛɴᴇʀ ɪs ᴀᴅᴅеᴅ</u>\n\nᴅеᴍᴏ - {SHORT_LINK}\n\nsɪᴛе - `{URL}`\n\nᴀᴘɪ - `{API}`</b>", quote=True)
        user_id = m.from_user.id
        if m.from_user.username:
            user_info = f"@{m.from_user.username}"
        else:
            user_info = f"{m.from_user.mention}"
        link = (await c.get_chat(m.chat.id)).invite_link
        grp_link = f"[{m.chat.title}]({link})"
        log_message = f"#New_Shortner_Set_For_3rd_Verify\n\nName - {user_info}\nId - `{user_id}`\n\nDomain name - {URL}\nApi - `{API}`\nGroup link - {grp_link}"
        await c.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
    except Exception as e:
        await save_group_settings(grp_id, 'shortner_three', SHORTENER_WEBSITE3)
        await save_group_settings(grp_id, 'api_three', SHORTENER_API3)
        await m.reply_text(f"<b><u>💢 ᴇʀʀᴏʀ ᴏᴄᴄᴏᴜʀеᴅ!!</u>\n\nᴀᴜᴛo ᴀᴅᴅеded ʙᴏᴛ ᴏᴡɴеr ᴅеꜰᴜʟᴛ sʜᴏʀᴛɴеr\n\nɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛo ᴄʜᴀɴɢе ᴛʜеɴ ᴜsе ᴄᴏʀʀеᴄᴛ ꜰᴏʀᴍᴀᴛ ᴏʀ ᴀᴅᴅ ᴠᴀʟɪᴅ sʜshortʟɪɴᴋ ᴅᴏᴍᴀɪɴ ɴᴀᴍе & ᴀᴘɪ\n\nʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ ᴄᴏɴᴛᴀᴄᴛ ᴏᴜʀ <a href=https://t.me/+4uFxyl0TAL0xMTg0>sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ</a> ꜰᴏʀ sᴏʟᴠᴇ ᴛʜɪs ɪssᴜᴇ...\n\n饰 ʟɪᴋе -\n\n`/set_shortner_3 mdiskshortner.link e7beb3c8f756dfa15d0bec495abc65f58c0dfa95`\n\n💔 ᴇʀʀᴏʀ - <code>{e}</code></b>", quote=True)
        

@Client.on_message(filters.command('set_log'))
async def set_log(client, message):
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>¼ʜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏuᴘ</b>')
    if len(message.text.split()) == 1:
        await message.reply("<b><u>ɪɴᴠᴀɪʟᴅ ꜰᴏʀᴍᴀᴛ!!</u>\n\nᴜsᴇ ʟɪᴋе ᴛʜɪs -\n`/log -100xxxxxxxx`</b>")
        return
    sts = await message.reply("<b>♻️ ᴄʜᴇᴄᴋɪɴɢ...</b>")
    await asyncio.sleep(1.2)
    await sts.delete()
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜSᴇ ᴛʜɪS ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏuᴘ...</b>")
    try:
        log = int(message.text.split(" ", 1)[1])
    except IndexError:
        return await message.reply_text("<b><u>ɪɴᴠᴀɪʟᴅ ꜰᴏʀᴍᴀᴛ!!</u>\n\n... ᴜsе ʟɪᴋе ᴛʜɪs -\n`/log -100xxxxxxxx`</b>")
    except ValueError:
        return await message.reply_text('<b>ᴍᴀᴋе sᴜʀе ɪᴅ ɪs ɪɴᴛеɢеʀ...</b>')
    try:
        t = await client.send_message(chat_id=log, text="<b>ʜеʏ ᴡʜᴀᴛ's ᴜᴘ!!</b>")
        await asyncio.sleep(3)
        await t.delete()
    except Exception as e:
        return await message.reply_text(f'<b><u>😐 ᴍᴀᴋе sᴜʀе ᴛʜɪs ʙᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴеʟ...</u>\n\n💔 ᴇʀʀᴏʀ - <code>{e}</code></b>')
    await save_group_settings(grp_id, 'log', log)
    await message.reply_text(f"<b>✅ sᴜᴄᴄеssꜰᴜʟʟʏ sеᴛ ʏᴏuʀ ʟᴏɢ ᴄʜᴀɴɴеʟ ꜰᴏʀ {title}\n\nɪᴅ `{log}`</b>", disable_web_page_preview=True)
    user_id = m.from_user.id
    user_info = f"@{m.from_user.username}" if m.from_user.username else f"{m.from_user.mention}"
    link = (await client.get_chat(message.chat.id)).invite_link
    grp_link = f"[{message.chat.title}]({link})"
    log_message = f"#New_Log_Channel_Set\n\nName - {user_info}\nId - `{user_id}`\n\nLog channel id - `{log}`\nGroup link - {grp_link}"
    await client.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)  
    

@Client.on_message(filters.command('details'))
async def all_settings(client, message):
    grp_id = message.chat.id
    title = message.chat.title
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    settings = await get_settings(grp_id)
    text = f"""<b><u>⚙️ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ꜰᴏʀ -</u> {title}

<u>✅️ 1sᴛ ᴠᴇʀɪꜰʏ sʜᴏʀᴛɴᴇʀ ɴᴀᴍᴇ/ᴀᴘɪ</u>
ɴᴀᴍᴇ - `{settings["shortner"]}`
ᴀᴘɪ - `{settings["api"]}`

<u>✅️ 2ɴ打 ᴠᴇʀɪꜰʏ sʜᴏʀᴛɴᴇʀ ɴᴀᴍᴇ/ᴀᴘɪ</u>
ɴᴀᴍᴇ - `{settings["shortner_two"]}`
ᴀᴘɪ - `{settings["api_two"]}`

<u>✅️ 3ʀᴅ ᴠᴇʀɪꜰʏ sʜᴏʀᴛɴᴇʀ ɴᴀᴍᴇ/ᴀᴘɪ</u>
ɴᴀᴍᴇ - `{settings["shortner_three"]}`
ᴀᴘɪ - `{settings["api_three"]}`

🧭 𝟸ɴᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ - `{settings['verify_time']}`

🧭 𝟹ʀᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ - `{settings['third_verify_time']}`

📝 ʟᴏɢ ᴄʜᴀɴɴᴇʟ ɪᴅ - `{settings['log']}`

🌀 ꜰꜱᴜʙ ᴄʜᴀɴɴᴇʟ ɪᴅ - /show_fsub

📍1 ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ - {settings['tutorial']}

📍2 ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ - {settings['tutorial_2']}

📍3 ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ - {settings['tutorial_3']}

🎯 ɪᴍᴅʙ ᴛᴇᴍᴘʟᴀᴛᴇ - `{settings['template']}`

📂 ꜰɪʟᴇ ᴄᴀᴘᴛɪᴏɴ - `{settings['caption']}`</b>"""
    
    btn = [[
        InlineKeyboardButton("ʀᴇꜱᴇᴛ ᴅᴀᴛᴀ", callback_data="reset_grp_data")
    ],[
        InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close_data")
    ]]
    reply_markup=InlineKeyboardMarkup(btn)
    dlt=await message.reply_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await asyncio.sleep(300)
    await dlt.delete()


@Client.on_message(filters.command('set_time_2'))
async def set_time_2(client, message):
    userid = message.from_user.id if message.from_user else None
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")       
    if not userid:
        return await message.reply("<b>ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ...</b>")
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    try:
        time = int(message.text.split(" ", 1)[1])
    except:
        return await message.reply_text("Command Incomplete!")   
    await save_group_settings(grp_id, 'verify_time', time)
    await message.reply_text(f"Successfully set 1st verify time for {title}\n\nTime is - <code>{time}</code>")

@Client.on_message(filters.command('set_time_3'))
async def set_time_3(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply("<b>ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ...</b>")
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")       
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    try:
        time = int(message.text.split(" ", 1)[1])
    except:
        return await message.reply_text("Command Incomplete!")   
    await save_group_settings(grp_id, 'third_verify_time', time)
    await message.reply_text(f"Successfully set 1st verify time for {title}\n\nTime is - <code>{time}</code>")


@Client.on_callback_query(filters.regex("mostsearch"))
async def most(client, callback_query):
    def is_alphanumeric(string):
        return bool(re.match('^[a-zA-Z0-9 ]*$', string))
    limit = 20  
    top_messages = await mdb.get_top_messages(limit)
    seen_messages = set()
    truncated_messages = []
    for msg in top_messages:
        msg_lower = msg.lower()
        if msg_lower not in seen_messages and is_alphanumeric(msg):
            seen_messages.add(msg_lower)
            
            if len(msg) > 35:
                truncated_messages.append(msg[:32] + "...")
            else:
                truncated_messages.append(msg)

   
    keyboard = [truncated_messages[i:i+2] for i in range(0, len(truncated_messages), 2)]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        one_time_keyboard=True, 
        resize_keyboard=True, 
        placeholder="Most searches of the day"
    )
    
    await callback_query.message.reply_text("<b>Hᴇʀᴇ ɪꜱ ᴛʜе ᴍᴏꜱᴛ ꜱеᴀʀᴄʜеꜱ ʟɪꜱᴛ 👇</b>", reply_markup=reply_markup)
    await callback_query.answer()


@Client.on_callback_query(filters.regex(r"^trending$"))
async def top(client, query):
    movie_series_names = await movie_series_db.get_movie_series_names(1)
    if not movie_series_names:
        await query.message.reply("Tʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴍᴏᴠɪᴇ ᴏʀ sᴇʀɪᴇs ɴᴀᴍᴇs ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛʜᴇ ᴛᴏᴘ sᴇᴀʀᴄʜᴇs.")
        return
    buttons = [movie_series_names[i:i + 2] for i in range(0, len(movie_series_names), 2)]
    spika = ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True
    )
    await query.message.reply("<b>Here Is The Top Trending List 👇</b>", reply_markup=spika)
    
# ==========================================
# 📊 ADMIN ONLY: LIVE REFERRAL ANALYTICS DASHBOARD
# ==========================================
@Client.on_message(filters.command("refer_stats") & filters.user(ADMINS))
async def refer_stats_command(client, message):
    daily, weekly, monthly, total = referdb.get_analytics()
    stats_text = (
        f"📊 **𝗥𝗘𝗙𝗘𝗥𝗥𝗔𝗟 𝗔𝗡𝗔𝗟𝗬𝗧𝗜𝗖𝗦 𝗗𝗔𝗦𝗛𝗕𝗢𝗔𝗥𝗗**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 **Aaj Aaye Users:** `{daily}`\n"
        f"📅 **Pichle 7 Din:** `{weekly}`\n"
        f"📆 **Pichle 30 Din:** `{monthly}`\n"
        f"🔥 **Total Referrals:** `{total}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *Organic growth loops are running smoothly in real-time.*"
    )
    await message.reply_text(stats_text)

@Client.on_message(filters.private & filters.command("pm_search_on"))
async def set_pm_search_on(client, message):
    user_id = message.from_user.id
    bot_id = client.me.id
    if user_id not in ADMINS:
        await message.delete()
        return
    
    await db.update_pm_search_status(bot_id, enable=True)
    await message.reply_text("<b><i>✅️ ᴘᴍ ꜱᴇᴀʀᴄʜ ᴇɴᴀʙʟᴇᴅ, ꜰʀᴏᴍ ɴᴏᴡ ᴜꜱᴇʀꜱ ᴀʙʟᴇ ᴛᴏ ꜱᴇᴀʀᴄʜ ᴍᴏᴠɪᴇ ɪɴ ʙᴏᴛ ᴘᴍ.</i></b>")

@Client.on_message(filters.private & filters.command("pm_search_off"))
async def set_pm_search_off(client, message):
    user_id = message.from_user.id
    bot_id = client.me.id
    if user_id not in ADMINS:
        await message.delete()
        return
    
    await db.update_pm_search_status(bot_id, enable=False)
    await message.reply_text("<b><i>❌️ ᴘᴍ ꜱᴇᴀʀᴄʜ ᴅɪꜱᴀʙʟᴇᴅ, ꜰʀᴏᴍ ɴᴏᴡ ɴᴏ ᴏɴᴇ ᴄᴀɴ ᴀʙʟᴇ ᴛᴏ ꜱᴇᴀʀᴄʜ ᴍᴏᴠɪᴇ ɪɴ ʙᴏᴛ ᴘᴍ.</i></b>")


@Client.on_message(filters.private & filters.command("movie_update_on"))
async def set_send_movie_on(client, message):
    user_id = message.from_user.id
    bot_id = client.me.id
    if user_id not in ADMINS:
        await message.delete()
        return    
    await db.update_send_movie_update_status(bot_id, enable=True)
    await message.reply_text("<b><i>✅️ ꜱᴇɴᴅ ᴍᴏᴠɪᴇ ᴜᴘᴅᴀᴛᴇ ᴇɴᴀʙʟᴇᴅ.</i></b>")

@Client.on_message(filters.private & filters.command("movie_update_off"))
async def set_send_movie_update_off(client, message):
    user_id = message.from_user.id
    bot_id = client.me.id
    if user_id not in ADMINS:
        await message.delete()
        return    
    await db.update_send_movie_update_status(bot_id, enable=False)
    await message.reply_text("<b><i>❌️ ꜱᴇɴᴅ ᴍᴏᴠɪᴇ ᴜᴘᴅᴀᴛᴇ ᴅɪꜱᴀʙʟᴇᴅ.</i></b>")
    
@Client.on_message(filters.command("verify_id"))
async def generate_verify_id(bot, message):
    if message.from_user.id not in ADMINS:
        await message.reply('Only the bot Admin can use this command... 😑')
        return
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("This command only works in groups!")
    grpid = message.chat.id   
    if grpid in verification_ids:
        await message.reply_text(f"An active Verify ID already exists for this group: `/verifyoff {verification_ids[grpid]}`")
        return
    
    verify_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    verification_ids[grpid] = verify_id
    await message.reply_text(f"Verify ID: `/verifyoff {verify_id}` (Valid for this group, one-time use)")
    return

@Client.on_message(filters.command("verifyoff"))
async def verifyoff(bot, message):
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("This command only works in groups!")
    
    grpid = message.chat.id
    if not await is_check_admin(bot, grpid, message.from_user.id):  # Changed client to bot
        return await message.reply_text('<b>You are not an admin in this group!</b>')
    
    try:
        input_id = message.command[1]
    except IndexError:
        return await message.reply_text("Please provide the Verify ID along with the command.\nUsage: `/verifyoff {id}`")
    
    if grpid not in verification_ids or verification_ids[grpid] != input_id:
        return await message.reply_text("Invalid Verify ID! Please contact the admin for the correct ID.")
    
    await save_group_settings(grpid, 'is_verify', False)
    del verification_ids[grpid]
    return await message.reply_text("Verification successfully disabled.")


@Client.on_message(filters.command("verifyon"))
async def verifyon(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("This command only works in groups!")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    
    if not await is_check_admin(bot, grpid, message.from_user.id):  # Changed client to bot
        return await message.reply_text('<b>You are not an admin in this group!</b>')
    
    await save_group_settings(grpid, 'is_verify', True)
    return await message.reply_text("Verification successfully enabled.")

@Client.on_message(filters.command("reset_group"))
async def reset_group_command(client, message):
    grp_id = message.chat.id
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    sts = await message.reply("<b>♻️ ᴄʜᴇᴄᴋɪɴɢ...</b>")
    await asyncio.sleep(1.2)
    await sts.delete()
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    btn = [[
        InlineKeyboardButton('🚫 ᴄʟᴏsᴇ 🚫', callback_data='close_data')
    ]]
    reply_markup = InlineKeyboardMarkup(btn)
    await save_default_settings(grp_id)
    await message.reply_text('ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ʀᴇꜱᴇᴛ ɢʀᴏᴜᴘ ꜱᴇᴛᴛɪɴɢꜱ...')
    
import os
from pyrogram import Client, filters
from info import ADMINS

@Client.on_message(filters.command("logs") & filters.user(ADMINS))
async def get_logs_handler(client, message):
    log_file_name = "TELEGRAM BOT.LOG" 
    
    if os.path.exists(log_file_name):
        # File size check karega
        if os.path.getsize(log_file_name) > 0:
            try:
                await message.reply_document(
                    document=log_file_name,
                    caption="⚙️ Here are your bot logs."
                )
            except Exception as e:
                await message.reply_text(f"❌ Error sending logs: {e}")
        else:
            # Agar file 0 byte ki hai
            await message.reply_text("✅ Log file ekdum khali hai (0 bytes). Iska matlab bot mein abhi tak koi error record nahi hua hai, sab makkhan chal raha hai!")
    else:
        await message.reply_text("❌ Logs file not found on server.")

@Client.on_message(filters.private & filters.command("fsub_on") & filters.user(ADMINS))
async def force_sub_on(client, message):
    bot_id = client.me.id
    await db.update_fsub_status(bot_id, enable=True)
    await message.reply_text("<b>✅ Force Sub feature ENABLED successfully!</b>")

@Client.on_message(filters.private & filters.command("fsub_off") & filters.user(ADMINS))
async def force_sub_off(client, message):
    bot_id = client.me.id
    await db.update_fsub_status(bot_id, enable=False)
    await message.reply_text("<b>❌ Force Sub feature DISABLED successfully!</b>")

@Client.on_callback_query(filters.regex("^search_guide$"))
async def search_guide_callback(client, query):
    await query.answer()
    btn = [[InlineKeyboardButton("🔙 Bᴀᴄᴋ Tᴏ Hᴏᴍᴇ", callback_data="start")]]
    
    try:
        from pyrogram.types import InputMediaPhoto
        await query.message.edit_media(
            media=InputMediaPhoto(media="https://i.ibb.co/xSGHw9dj/x.jpg", caption=script.SEARCH_GUIDE_TXT, parse_mode=enums.ParseMode.HTML),
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except Exception:
        await query.message.edit_caption(
            caption=script.SEARCH_GUIDE_TXT,
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )

@Client.on_message(filters.command('set_pm_caption') & filters.private)
async def set_pm_caption_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return await message.reply_text("Only the bot owner can use this command... 😑")
    try:
        caption = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("<b>Command Incomplete!</b>\n\nExample:\n`/set_pm_caption {file_name}`")
    
    await mdb.update_configuration("pm_caption", caption)
    await message.reply_text(f"<b>✅ PM Caption Successfully Saved!</b>\n\n<b>New PM Caption:</b>\n{caption}", disable_web_page_preview=True)

@Client.on_message(filters.command("guide") & filters.private & filters.incoming)
async def guide_command(client, message):
    btn = [[InlineKeyboardButton("🔙 Bᴀᴄᴋ Tᴏ Hᴏᴍᴇ", callback_data="start")]]
    
    try:
        await message.reply_photo(
            photo="https://i.ibb.co/xSGHw9dj/x.jpg", 
            caption=script.SEARCH_GUIDE_TXT, 
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )
    except Exception:
        await message.reply_text(
            text=script.SEARCH_GUIDE_TXT,
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )

import os
from database.ia_filterdb import Media

@Client.on_message(filters.command("export_titles") & filters.private & filters.user(ADMINS))
async def export_db_titles(client, message):
    msg = await message.reply_text("⏳ **Extracting Database...**\nIsme 10-15 seconds lag sakte hain, please wait.")
    
    try:
        # Database se saari files fetch karna
        cursor = Media.find({})
        
        # Ek nayi text file banakar usme saare naam likhna
        with open("db_titles.txt", "w", encoding="utf-8") as f:
            count = 0
            async for doc in cursor:
                # Sirf file ka naam text file me likhega
                f.write(f"{doc.file_name}\n")
                count += 1
        
        if count == 0:
            return await msg.edit_text("❌ **Database ekdum khali hai!**")
            
        # File ready hone ke baad user ko send karna
        await message.reply_document(
            document="db_titles.txt",
            caption=f"✅ **Database Export Successful!**\n\nTotal Extracted Titles: `{count}`"
        )
        
        # Server ka kachra saaf karna (Text file delete)
        await msg.delete()
        os.remove("db_titles.txt")
        
    except Exception as e:
        await msg.edit_text(f"❌ **Error Occurred:** `{e}`")
        print(f"Export Error: {e}")

@Client.on_message(filters.command("uploadall") & filters.user(ADMINS))
async def mark_all_queued_as_uploaded(client, message):
    m = await message.reply_text("🔄 **Scanning Database for Queued Requests...**")
    
    queued_requests = await db.get_queued_requests()
    
    if not queued_requests:
        return await m.edit_text("✅ **Koi bhi file Queue mein nahi hai!** Sab clear hai.")
        
    success = 0
    failed = 0
    deleted_msgs = 0
    
    await m.edit_text(f"⏳ **Processing {len(queued_requests)} Requests...**\nKripya wait karein. (Anti-Ban Active 🛡️)")
    
    for req in queued_requests:
        user_id = req.get("user_id")
        tmdb_id = req.get("tmdb_id")
        msg_id = req.get("msg_id")
        chat_id = req.get("chat_id")
        m_char = req.get("m_char", "m")
        m_type = "tv" if m_char == "t" else "movie"
        
        try:
            # 1. TMDB se fresh Poster aur Name fetch karo (Exactly like notify_user)
            movie = await get_poster(tmdb_id, id=True, type=m_type)
            
            base_title = movie.get('title') if movie else req.get("movie_name", "Requested File")
            year = movie.get('year') if movie else ""
            
            if year and year != "N/A":
                movie_name = f"{base_title} ({year})"
                search_movie = f"{base_title}-{year}".replace(" ", "-")
            else:
                movie_name = base_title
                search_movie = base_title.replace(" ", "-")
                
            poster_url = movie.get('poster') if movie else "https://i.ibb.co/HpRDS9X5/x.jpg"
            
            # 2. EXACT SAME CAPTION AND BUTTON (As requested)
            notify_text = (
                f"✅ **'{movie_name}' is Uploaded!**\n\n"
                f"➖➖➖➖➖➖➖➖➖➖\n"
                f"🎬 Aapki requested file upload kar di gayi hai.\n"
                f"👇 Download karne ke liye niche click karein."
            )
            notify_btn = [[
                InlineKeyboardButton('🔍 Get File', url=f'https://telegram.me/{temp.U_NAME}?start=getfile-{search_movie}')
            ]]
            
            # 3. User ko PM bhejo
            await client.send_photo(
                chat_id=user_id,
                photo=poster_url,
                caption=notify_text,
                reply_markup=InlineKeyboardMarkup(notify_btn)
            )
            success += 1
        except Exception as e:
            failed += 1
            
        # 4. Database se request uda do (Success ho ya Fail)
        await db.delete_movie_request(user_id, tmdb_id)
        
        # 5. Admin Channel se "IN QUEUE" wala message udha do
        if msg_id and chat_id:
            try:
                await client.delete_messages(chat_id=chat_id, message_ids=msg_id)
                deleted_msgs += 1
            except Exception:
                pass
        
        # 🛡️ THE TELEGRAM BAN BYPASS (Super Important)
        await asyncio.sleep(0.5) 
            
    await m.edit_text(
        f"🎉 **BATCH PROCESSING COMPLETE!**\n\n"
        f"✅ Users Notified: **{success}**\n"
        f"❌ Users Blocked Bot: **{failed}**\n"
        f"🗑️ Admin Messages Cleaned: **{deleted_msgs}**\n\n"
        f"Apka dashboard aur database puri tarah saaf ho chuka hai."
    )

# ==========================================
# ⚙️ ADMIN ONLY: PM SETTINGS PANEL
# ==========================================
@Client.on_message(filters.command('pm_settings') & filters.private & filters.user(ADMINS))
async def pm_settings_command(client, message):
    from database.config_db import mdb
    from utils import get_settings
    
    # PM Mode ki current settings fetch karo
    settings = await get_settings(0, pm_mode=True)
    
    buttons = [
        [
            InlineKeyboardButton('📸 IMDB', callback_data=f'setpm#pm_imdb#{settings["imdb"]}'),
            InlineKeyboardButton('ᴏɴ ✅' if settings["imdb"] else 'ᴏғғ ❌', callback_data=f'setpm#pm_imdb#{settings["imdb"]}')
        ],
        [
            InlineKeyboardButton('🪄 SPELL CHECK', callback_data=f'setpm#pm_spell_check#{settings["spell_check"]}'),
            InlineKeyboardButton('ᴏɴ ✅' if settings["spell_check"] else 'ᴏғғ ❌', callback_data=f'setpm#pm_spell_check#{settings["spell_check"]}')
        ],
        [
            InlineKeyboardButton('🗑 AUTO DELETE', callback_data=f'setpm#pm_auto_delete#{settings["auto_delete"]}'),
            InlineKeyboardButton('ᴏɴ ✅' if settings["auto_delete"] else 'ᴏғғ ❌', callback_data=f'setpm#pm_auto_delete#{settings["auto_delete"]}')
        ],
        [
            InlineKeyboardButton('❌ CLOSE', callback_data='close_data')
        ]
    ]
    
    await message.reply_text(
        text="<b>⚙️ BOT PRIVATE MESSAGE (PM) SETTINGS</b>\n\n━━━━━━━━━━━━━━━━━━━━\nYahan se aap bot ke Personal Message ke features ON/OFF kar sakte hain. Yeh settings sabhi users ke liye PM mein strictly apply hongi.",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )

# ==========================================
# ⚙️ ADMIN ONLY: PM SETTINGS PANEL (BULLETPROOF FIX)
# ==========================================
@Client.on_message(filters.command('pm_settings') & filters.private & filters.user(ADMINS))
async def pm_settings_command(client, message):
    from utils import get_settings
    
    # ID '0' Master PM settings ko point karta hai
    settings = await get_settings(0) 
    
    buttons = [
        [
            InlineKeyboardButton('📸 IMDB (Posters)', callback_data=f'setpm#imdb#{settings["imdb"]}'),
            InlineKeyboardButton('ᴏɴ ✅' if settings["imdb"] else 'ᴏғғ ❌', callback_data=f'setpm#imdb#{settings["imdb"]}')
        ],
        [
            InlineKeyboardButton('🪄 SPELL CHECK', callback_data=f'setpm#spell_check#{settings["spell_check"]}'),
            InlineKeyboardButton('ᴏɴ ✅' if settings["spell_check"] else 'ᴏғғ ❌', callback_data=f'setpm#spell_check#{settings["spell_check"]}')
        ],
        [
            InlineKeyboardButton('🗑 AUTO DELETE', callback_data=f'setpm#auto_delete#{settings["auto_delete"]}'),
            InlineKeyboardButton('ᴏɴ ✅' if settings["auto_delete"] else 'ᴏғғ ❌', callback_data=f'setpm#auto_delete#{settings["auto_delete"]}')
        ],
        [
            InlineKeyboardButton('❌ CLOSE', callback_data='close_data')
        ]
    ]
    
    await message.reply_text(
        text="<b>⚙️ PRIVATE MESSAGE (PM) SETTINGS</b>\n\n━━━━━━━━━━━━━━━━━━━━\nYahan se aap bot ke PM features ON/OFF kar sakte hain. Yeh sidha native database engine se connect hai aur 100% kaam karega.",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_callback_query(filters.regex(r"^setpm#"))
async def set_pm_settings_callback(client, query):
    if query.from_user.id not in ADMINS:
        return await query.answer("⚠️ You are not authorized!", show_alert=True)
        
    _, set_type, current_status = query.data.split("#")
    
    # Logic: Agar pehle 'True' (On) tha, toh ab False (Off) kar do
    new_status = False if current_status == "True" else True
    
    # 💥 THE CORE FIX: Hum existing group save logic ko ID '0' (PM) par redirect kar rahe hain
    from utils import save_group_settings, get_settings
    await save_group_settings(0, set_type, new_status) 
    
    await query.answer(f"✅ {set_type.upper()} status changed!", show_alert=False)
    
    # Nayi settings fetch karke button update karo
    settings = await get_settings(0)
    
    buttons = [
        [
            InlineKeyboardButton('📸 IMDB (Posters)', callback_data=f'setpm#imdb#{settings["imdb"]}'),
            InlineKeyboardButton('ᴏɴ ✅' if settings["imdb"] else 'ᴏғғ ❌', callback_data=f'setpm#imdb#{settings["imdb"]}')
        ],
        [
            InlineKeyboardButton('🪄 SPELL CHECK', callback_data=f'setpm#spell_check#{settings["spell_check"]}'),
            InlineKeyboardButton('ᴏɴ ✅' if settings["spell_check"] else 'ᴏғғ ❌', callback_data=f'setpm#spell_check#{settings["spell_check"]}')
        ],
        [
            InlineKeyboardButton('🗑 AUTO DELETE', callback_data=f'setpm#auto_delete#{settings["auto_delete"]}'),
            InlineKeyboardButton('ᴏɴ ✅' if settings["auto_delete"] else 'ᴏғғ ❌', callback_data=f'setpm#auto_delete#{settings["auto_delete"]}')
        ],
        [
            InlineKeyboardButton('❌ CLOSE', callback_data='close_data')
        ]
    ]
    
    try:
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
    except:
        pass

# ==========================================
# 📝 ADMIN ONLY: PM CAPTION ENGINE
# ==========================================
@Client.on_message(filters.command("set_pm_caption") & filters.user(ADMINS) & filters.private)
async def set_pm_caption_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "⚠️ **Format Galat Hai!**\n\n"
            "👉 `/set_pm_caption Aapka Naya Caption Yahan`\n\n"
            "**Variables jo aap use kar sakte ho:**\n"
            "`{file_name}`, `{file_size}`, `{file_caption}`"
        )
    
    new_caption = message.text.split(None, 1)[1]
    from utils import save_group_settings
    
    # 🔥 THE FIX: ID '0' me save kar rahe hain (Master PM Database)
    await save_group_settings(0, 'caption', new_caption)
    await message.reply_text(f"✅ **PM Caption Successfully Updated!**\n\nAb se PM mein files is caption ke sath jayengi:\n\n{new_caption}")

@Client.on_message(filters.command("del_pm_caption") & filters.user(ADMINS) & filters.private)
async def del_pm_caption_cmd(client, message):
    from utils import save_group_settings
    from info import FILE_CAPTION
    
    # Reset to default info.py caption
    await save_group_settings(0, 'caption', FILE_CAPTION)
    await message.reply_text("🗑 **PM Caption Deleted!**\nAb default caption use hoga.")

@Client.on_message(filters.command("see_pm_caption") & filters.user(ADMINS) & filters.private)
async def see_pm_caption_cmd(client, message):
    from utils import get_settings
    
    settings = await get_settings(0)
    current_caption = settings.get("caption", "Default Caption")
    await message.reply_text(f"👀 **Current PM Caption:**\n\n{current_caption}")


# ==========================================
# 🛠️ ADMIN TESTING: NUKE USER DATA
# ==========================================
@Client.on_message(filters.command("nuke_user") & filters.user(ADMINS))
async def nuke_user_test(client, message):
    try:
        target_id = int(message.command[1])
    except:
        return await message.reply("⚠️ Format: `/nuke_user 123456789`")
        
    await db.col.delete_one({"id": target_id})
    await db.users.delete_one({"id": target_id})
    
    from database.jsreferdb import referdb
    referdb.refer_collection.delete_one({"user_id": target_id})
    referdb.refer_logs.delete_many({"new_user_id": target_id})
    
    await message.reply(f"✅ User `{target_id}` ka poora data delete ho gaya hai. Ab wo ID click karegi toh 100% fresh naya user count hogi!")


# ==========================================
# 🎛️ ADMIN TOOLS: WELCOME UI BUTTON CONTROL
# ==========================================

@Client.on_message(filters.command("set_welcome") & filters.user(ADMINS))
async def set_welcome_buttons(client, message):
    try:
        # Example: /set_welcome Venom | Deadpool
        movies = message.text.split(" ", 1)[1].split("|")
        if len(movies) != 2:
            return await message.reply("⚠️ **Format Galat Hai!**\nSahi format: `/set_welcome Movie 1 | Movie 2`")
        
        m1 = movies[0].strip()
        m2 = movies[1].strip()
        
        await mdb.update_configuration("welcome_movies", [m1, m2])
        await message.reply(f"✅ **Welcome Buttons Manually Set!**\n\n🔘 Button 1: `{m1}`\n🔘 Button 2: `{m2}`\n\nAb naye users ko automation ki jagah yahi 2 movies dikhengi.")
    except Exception as e:
        await message.reply("⚠️ **Format:** `/set_welcome Movie 1 | Movie 2`")

@Client.on_message(filters.command("reset_welcome") & filters.user(ADMINS))
async def reset_welcome_buttons(client, message):
    await mdb.update_configuration("welcome_movies", [])
    await message.reply("✅ **Welcome Buttons Reset!**\n\nManual override hata diya gaya hai. Ab bot wapas automatically Premium Titles DB se **chhoti length** wali movies uthayega.")

# ==========================================
# 🎁 1-HOUR FREE PREMIUM CLAIM HANDLER (FIXED)
# ==========================================
@Client.on_callback_query(filters.regex(r"^activate_1h_premium$"))
async def claim_1h_premium_handler(client, query):
    user_id = query.from_user.id
    
    # User ne pehle trial toh nahi liya check karo
    has_free_trial = await db.check_trial_status(user_id)
    if has_free_trial:
        return await query.answer("❌ Aap pehle hi Free Trial claim kar chuke hain!\n\nCheck: /myplan", show_alert=True)

    # 1. Database me 1 Ghante ka Premium add karo aur "TRIAL" Tag lagao!
    from datetime import datetime, timedelta
    new_expiry = datetime.now() + timedelta(hours=1)
    
    # 🔥 THE FIX: Explicitly passing 'trial' tag and preventing duplicate claims
    await db.update_user({
        "id": user_id, 
        "expiry_time": new_expiry,
        "premium_type": "trial",
        "has_free_trial": True, 
        "notified_3d": False,
        "notified_2d": False,
        "notified_1d": False
    })
    
    # 2. User ko Instant Pop-up Alert do
    await query.answer("🎉 Congratulations! Your 1-Hour FREE Premium is now active. Enjoy! 🚀", show_alert=True)
    
    # 3. Message ko edit karke permanent Navigation Menu bana do (Delete nahi hoga)
    claimed_caption = (
        f"⚡ **𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗔𝗖𝗧𝗜𝗩𝗔𝗧𝗘𝗗!** ⚡\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 Aapka **1 Hour FREE Premium** successfully activate ho gaya hai.\n\n"
        f"🍿 Ab aap Premium Movies & Web Series enjoy kar sakte hain.\n"
        f"👇 **Niche diye buttons se search ya explore karna shuru karein:**"
    )
    
    # 🔥 Yahan url mein apne movie group ka actual link daal dena agar alag hai
    claimed_btns = [
        [InlineKeyboardButton("🎬 Explore Movies & Series", callback_data="exp_main")],
        [InlineKeyboardButton("🔍 Search Movies", url="https://t.me/+iEPY_wmIhu9mYTY1")] 
    ]
    
    await query.message.edit_text(
        text=claimed_caption,
        reply_markup=InlineKeyboardMarkup(claimed_btns),
        parse_mode=enums.ParseMode.MARKDOWN
    )
