import sys
import os
import subprocess

# === AUTO-DEPENDENCY INJECTOR ===
try:
    import rapidfuzz
except ImportError:
    print("🚨 RapidFuzz missing! Auto-Installing in background. Please wait...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rapidfuzz"])
    print("✅ RapidFuzz Installed Successfully!")
    import rapidfuzz
# ================================
# === CACHETOOLS INJECTOR ===
try:
    import cachetools
except ImportError:
    print("🚨 Cachetools missing! Auto-Installing in background. Please wait...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cachetools"])
    print("✅ Cachetools Installed Successfully!")
    import cachetools
# ===========================

import glob
import importlib
from pathlib import Path
from pyrogram import idle
import logging
import logging.config

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)


from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import *
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from Script import script 
from datetime import date, datetime 
import pytz
from aiohttp import web
from plugins import web_server
import pyrogram.utils
import asyncio

# 🔥 THE ULTIMATE FIX: Loop ko kisi bhi pyrogram client import se pehle banana zaruri hai!
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import idle
from Jisshu.bot import JisshuBot
from Jisshu.util.keepalive import ping_server
from Jisshu.bot.clients import initialize_clients

ppath = "plugins/*.py"
files = glob.glob(ppath)

# 🔥 YAHAN SE 'JisshuBot.start()' UDA DIYA HAI. WO SIRF NEECHE ASYNC FUNCTION MEIN HOGA.

pyrogram.utils.MIN_CHANNEL_ID = -1009147483647
# --- NAYA AUTO EXPIRY CHECKER LOOP (Yeh 24/7 background mein chalega) ---
# --- 🚀 THE 3-2-1 SALES & EXPIRY DRIP CAMPAIGN ENGINE ---
async def premium_management_loop():
    logging.info("Premium Sales CRM Engine Started...")
    while True:
        try:
            now = datetime.now()
            
            # Get all users (Filtering memory load)
            users_cursor = db.users.find({"expiry_time": {"$ne": None}})
            
            async for user in users_cursor:
                # 🚀 PRO-FIX: Inner Try-Except taaki ek bad user baki loop ko block na kare
                try:
                    user_id = user.get('id')
                    expiry_time = user.get('expiry_time')
                    
                    if not expiry_time: continue
                    
                    # Type Safety: Agar DB me string format me time hai, toh crash hone se bachao
                    if isinstance(expiry_time, str):
                        try:
                            expiry_time = datetime.fromisoformat(expiry_time)
                        except ValueError:
                            # Invalid time string milne par clean karo aur aage badho
                            await db.users.update_one({"id": user_id}, {"$set": {"expiry_time": None}})
                            continue
                    
                    # LEGACY PROTECTION: Tag nahi hai toh PAID manega. Data loss = 0.
                    premium_type = user.get('premium_type', 'paid') 
                    
                    time_left = expiry_time - now
                    days_left = time_left.days
                    hours_left = time_left.total_seconds() / 3600

                    # ----------------------------------------------------
                    # 🔴 1. EXPIRED USERS LOGIC
                    # ----------------------------------------------------
                    if hours_left <= 0:
                        # 1. DB se access hatao (Bina ispar condition lagaye)
                        await db.remove_premium_access(user_id)
                        
                        # 🚀 SMART KICK ENGINE & EXPIRY NOTIFICATION
                        from info import PRN_ID, VIP_GROUP_ID, NEW_PREMIUM_CHANNEL
                        from pyrogram import enums
                        import pyrogram
                        import asyncio
                        
                        channels_to_kick = [PRN_ID, VIP_GROUP_ID, NEW_PREMIUM_CHANNEL]
                        
                        # 1. PEHLE USER KO KICK KARO
                        for ch_id in channels_to_kick:
                            if not ch_id: 
                                continue
                            try:
                                await JisshuBot.ban_chat_member(chat_id=ch_id, user_id=user_id)
                                await asyncio.sleep(0.5)
                                await JisshuBot.unban_chat_member(chat_id=ch_id, user_id=user_id)
                            except pyrogram.errors.FloodWait as e:
                                await asyncio.sleep(e.value + 1)
                                try:
                                    await JisshuBot.ban_chat_member(chat_id=ch_id, user_id=user_id)
                                    await JisshuBot.unban_chat_member(chat_id=ch_id, user_id=user_id)
                                except Exception:
                                    pass
                            except Exception:
                                pass
                        
                        # 2. EXPIRY MESSAGE TEXT GENERATE KARO
                        if premium_type == 'paid':
                            expiry_msg = (
                                f"🚨 <b><u>ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss ᴇxᴘɪʀᴇᴅ</u></b>\n\n"
                                f"Hello,\n"
                                f"Aapki <b>Premium membership</b> ki validity khatam ho chuki hai. 📉\n\n"
                                f"💔 <b>Ab aap miss kar rahe hain:</b>\n"
                                f"<blockquote>"
                                f"⚡ Ultra Fast Direct Download Link\n"
                                f"🎬 Access To Newly Added Movies\n"
                                f"∞︎︎ Unlimited Downloads Everyday\n"
                                f"🎥 480p To 4K Files Access\n"                        
                                f"💬 Admin support\n"
                                f"🎯 Fast request completion\n"
                                f"👑 Premium Request channel access\n"                        
                                f"🔞 Private 18+ Adult channel access"
                                f"</blockquote>\n\n"
                                f"⚡ <b>Renew karke turant apna Premium access wapas pao:</b>\n\n"
                                f"<b>👉 Abhi /plan par click karo aur turant unlock karo</b>\n"
                                f"<i>👉 /plan 👈 click here</i>\n\n"
                            )
                            log_msg = f"🔴 #PAID_EXPIRED | ID: <code>{user_id}</code> | <a href='tg://user?id={user_id}'>DM Customer</a>\n💡 ACTION: Send voice note offering 20% discount!"
                        elif premium_type == 'referral':
                            expiry_msg = "⚠️ <b>Referral Premium Expired!</b>\n\n🎁 Dobara FREE Premium unlock karne ke liye aur friends ko invite karein: /refer"
                            log_msg = f"🟡 #REFERRAL_EXPIRED | ID: <code>{user_id}</code> | <a href='tg://user?id={user_id}'>View Profile</a>"
                        else:
                            expiry_msg = "<b>👉 /plan</b>"
                            log_msg = f"⚪️ #TRIAL_EXPIRED | ID: <code>{user_id}</code>"
                        
                        # 3. MESSAGE BHEJO (WITH HTML PARSE MODE)
                        try: 
                            await JisshuBot.send_message(
                                chat_id=user_id, 
                                text=expiry_msg,
                                parse_mode=enums.ParseMode.HTML
                            )
                        except Exception as msg_err:
                            # PRO-FIX: Ignore USER_IS_BLOCKED & PEER_ID_INVALID silently to prevent loop choking
                            if "USER_IS_BLOCKED" in str(msg_err) or "PEER_ID_INVALID" in str(msg_err):
                                pass
                            else:
                                logging.error(f"Failed to send expiry msg to {user_id}: {msg_err}")
                        
                        # 4. ADMIN KO LOG BHEJO
                        if premium_type in ['paid', 'referral']:
                            try:
                                try:
                                    from info import PREMIUM_LOG_CHANNEL
                                    target_log = PREMIUM_LOG_CHANNEL
                                except Exception:
                                    target_log = LOG_CHANNEL
                                await JisshuBot.send_message(
                                    chat_id=target_log, 
                                    text=log_msg,
                                    parse_mode=enums.ParseMode.HTML
                                )
                            except Exception: 
                                pass

                    # ----------------------------------------------------
                    # 🟡 2. THE 3-2-1 PRE-EXPIRY DRIP CAMPAIGN
                    # ----------------------------------------------------
                    elif premium_type in ['paid', 'referral']:
                        notified_3d = user.get('notified_3d', False)
                        notified_2d = user.get('notified_2d', False)
                        notified_1d = user.get('notified_1d', False)

                        # T-3 Days Reminder
                        if 2 < days_left <= 3 and not notified_3d:
                            try:
                                await JisshuBot.send_message(user_id, "👋 <b>Reminder:</b> Aapka Premium Subscription <b>3 Din</b> mein khatam hone wala hai. Uninterrupted access ke liye samay par renew karein! (/plan)", parse_mode=enums.ParseMode.HTML)
                                await db.users.update_one({"id": user_id}, {"$set": {"notified_3d": True}})
                            except: pass

                        # T-2 Days Reminder
                        elif 1 < days_left <= 2 and not notified_2d:
                            try:
                                await JisshuBot.send_message(user_id, "⚠️ <b>Alert:</b> Sirf <b>48 Ghante</b> bache hain! Kal raat aapka VIP access khatam ho jayega. Apni files block hone se bachayein. (/plan)", parse_mode=enums.ParseMode.HTML)
                                await db.users.update_one({"id": user_id}, {"$set": {"notified_2d": True}})
                            except: pass

                        # T-1 Day (Final FOMO)
                        elif 0 <= days_left <= 1 and not notified_1d:
                            try:
                                await JisshuBot.send_message(user_id, "🚨 <b>FINAL DAY ALERT!</b> 🚨\n\nAapka Premium Access aaj raat khatam ho raha hai! Kal aapko VIP Channel se remove kar diya jayega.\n\n🎁 <b>SPECIAL OFFER:</b> Agar aap aagle 12 ghante ke andar apna plan renew karte hain, toh hum aapko Flat 20% Discount denge.\n\nAbhi Admin ko message karein aur offer claim karein!", parse_mode=enums.ParseMode.HTML)
                                await db.users.update_one({"id": user_id}, {"$set": {"notified_1d": True}})
                            except: pass
                
                except Exception as inner_e:
                    # Agar kisi user ka loop process fail hota hai, toh isko log karo aur next user pe jao.
                    logging.error(f"Error processing user {user.get('id', 'Unknown')}: {inner_e}")

        except Exception as e:
            logging.error(f"Error in Premium Management Loop: {e}")
            
        await asyncio.sleep(3600) # 🔥 ULTRA SCALABLE: Har 1 ghante mein 1 baar chalega (No lag at all)
# ------------------------------------------------------------------------

async def Jisshu_start():
    print('\n')
    print('Initalizing Jisshu Filter Bot')
    
    # 🔥 MOVE TO ASYNC: Ab bot tab shuru hoga jab event loop already running hoga.
    # Ye Python 3.14 par crash hone se 100% rokega.
    await JisshuBot.start()
    
    bot_info = await JisshuBot.get_me()
    JisshuBot.username = bot_info.username
    await initialize_clients()
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = "plugins.{}".format(plugin_name)
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            print("Jisshu Filter Bot Imported => " + plugin_name)
    
    if ON_HEROKU:
        asyncio.create_task(ping_server())
        
    # --- YAHAN NAYA AUTO CHECKER START KIYA GAYA HAI ---
    asyncio.create_task(premium_management_loop())
    # ---------------------------------------------------

    b_users, b_chats = await db.get_banned()
    temp.BANNED_USERS = b_users
    temp.BANNED_CHATS = b_chats
    await Media.ensure_indexes()
    me = await JisshuBot.get_me()
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
    temp.B_LINK = me.mention
    JisshuBot.username = '@' + me.username
    logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
    logging.info(script.LOGO)
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    await JisshuBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(me.mention, today, time))
    await JisshuBot.send_message(chat_id=SUPPORT_GROUP, text=f"<b>{me.mention} ʀᴇsᴛᴀʀᴛᴇᴅ 🤖</b>")
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()
    await idle()
    for admin in ADMINS:
        await JisshuBot.send_message(chat_id=admin, text=f"<b>{me.mention} ʙᴏᴛ ʀᴇsᴛᴀʀᴛᴇᴅ ✅</b>")

if __name__ == '__main__':
    # 🔥 Python 3.14+ loop handling logic
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        loop.run_until_complete(Jisshu_start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
