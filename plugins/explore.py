import re
import math
import asyncio
import html
import time
import pytz
from datetime import datetime
from pyrogram import Client, filters, StopPropagation, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from pyrogram.errors import MessageNotModified, FloodWait
from bson.objectid import ObjectId
from database.ia_filterdb import Media
import info
from info import ADMINS, SUBSCRIPTION
from Script import script
from utils import temp

# 🔥 IMPORTING EXACT BOLD FONT
from plugins.pm_filter import to_bold
from database.users_chats_db import db

# ==========================================
# 🗄️ MONGODB NATIVE CATALOG SETUP
# ==========================================
catalog_db = Media.collection.database["explore_catalog"]
explore_bcast_db = Media.collection.database["explore_bcast_status"]
explore_user_msgs_db = Media.collection.database["explore_user_msgs"]
EXPLORE_BANNER = "https://i.ibb.co/ns2zqCYH/x.jpg" 

# ==========================================
# ✂️ TRUNCATOR & UNBOLD MODULES
# ==========================================
def smart_truncate(title, max_length=30):
    year_match = re.search(r'\s*(\(\d{4}\))$', title)
    if year_match:
        year_str = year_match.group(1)
        base_title = title[:year_match.start()]
    else:
        year_str = ""
        base_title = title

    if len(base_title) > max_length:
        base_title = base_title[:max_length].strip() + "..."
        
    return f"{base_title} {year_str}".strip()

def unbold_and_clean(text):
    bold_map = str.maketrans(
        "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇.",
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz."
    )
    normal_text = str(text).translate(bold_map)
    normal_text = re.sub(r'[🔸🔹↳]', '', normal_text)
    return normal_text.strip()

def categorize_title(clean_name, raw_name):
    check_name = f"{clean_name} {raw_name}".lower()
    if any(x in check_name for x in ['s0', 's1', 'season', 'episode', 'ep ']): return "Web Series"
    if any(x in check_name for x in ['tamil', 'telugu', 'malayalam', 'kannada', 'south']): return "South Movie"
    if any(x in check_name for x in ['anime', 'animation', 'cartoon']): return "Animation Movie"
    if 'punjabi' in check_name: return "Punjabi Movie"
    if any(x in check_name for x in ['english', 'eng', 'hollywood']): return "Hollywood Movie"
    if 'bengali' in check_name: return "Bengali Movie"
    if 'marathi' in check_name: return "Marathi Movie"
    if 'bhojpuri' in check_name: return "Bhojpuri Movie"
    if 'urdu' in check_name: return "Urdu Movie"
    if 'gujarati' in check_name: return "Gujarati Movie"
    if 'odia' in check_name: return "Odia Movie"
    return "Bollywood Movie"

async def fetch_native_premium_titles():
    try:
        db_instance = Media.collection.database
        titles = []
        async for doc in db_instance["prem_titles"].find({}):
            if doc.get("title"): titles.append(doc["title"])
        if not titles:
            async for doc in db_instance["premium_titles"].find({}):
                if doc.get("title"): titles.append(doc["title"])
        return titles
    except Exception as e:
        print(f"Error fetching premium titles: {e}")
        return []

# ==========================================
# 🛡️ THE PREMIUM PAYWALL INTERCEPTOR (ONLY FOR PREMIUM BLOCKS)
# ==========================================
@Client.on_message(filters.command("start") & filters.private, group=-99)
async def explore_query_interceptor(client, message):
    if len(message.command) > 1:
        payload = message.command[1]
        
        # 👑 Sirf Premium Subscription ke block ko pakdega
        if payload == "reqpremium":
            btn = [
                [InlineKeyboardButton("💳 Check Plans & Pricing 💰", callback_data="free")],
                [InlineKeyboardButton("❌ Close", callback_data="close_data")]
            ]
            try:
                caption_text = script.PREPLANS_TXT.format(message.from_user.mention)
            except Exception:
                caption_text = "👑 **Premium Subscription Required!**\n\nIs exclusive movie/series ko download karne ke liye aapko hamara Premium Plan chahiye."
                
            await message.reply_photo(
                photo=SUBSCRIPTION,
                caption=caption_text,
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.HTML
            )
            raise StopPropagation
            
        # 🚀 Note: Humne yahan se 'expqry-' completely nikal diya hai!
        # Normal files native getfile- prefix use karengi jo seedha commands.py me jayega.

# ==========================================
# 📝 ADMIN COMMAND: MANUAL CATALOG EDIT 
# ==========================================
@Client.on_message(filters.command("set_catalog") & filters.user(ADMINS))
async def set_catalog_cmd(client, message):
    if len(message.command) < 2 or "|" not in message.text:
        return await message.reply_text(
            "❌ **Format Galat Hai!**\n\n👉 `/set_catalog Exact Title Name (Year) | New Category`"
        )
    
    try:
        raw_args = message.text.split(None, 1)[1]
        parts = raw_args.split("|")
        title_raw = parts[0].strip()
        new_cat = parts[1].strip().title()
        
        title_clean = unbold_and_clean(title_raw)
        
        result = await catalog_db.update_one(
            {"clean_title": {"$regex": f"^{re.escape(title_clean)}$", "$options": "i"}},
            {"$set": {"category": new_cat, "is_manually_edited": True}}
        )
        
        # 🔥 PREMIUM TITLE SCALABLE FIX: Agar title DB me nahi hai, toh Force Insert karega!
        if result.matched_count == 0:
            await catalog_db.insert_one({
                "clean_title": title_clean,
                "search_query": title_clean.lower(),
                "category": new_cat,
                "is_manually_edited": True,
                "added_at": datetime.now()
            })
        
        await message.reply_text(
            f"✅ **Catalog Entry Updated Manually!**\n\n🎬 **Title:** `{title_clean}`\n🏷️ **New Category:** `{new_cat}`\n\n⚠️ *Ye title ab `/reset_catalog` karne par bhi delete nahi hoga!*"
        )
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")

# ==========================================
# 📝 ADMIN COMMAND: BULK MANUAL CATALOG EDIT
# ==========================================
@Client.on_message(filters.command(["bulk_set", "bulk_catalog"]) & filters.user(ADMINS))
async def bulk_set_catalog_cmd(client, message):
    lines = message.text.split('\n')[1:] # Command wali line ko chhod kar baaki sab read karega
    
    if not lines:
        return await message.reply_text(
            "❌ **Format Galat Hai!**\n\n"
            "Sahi Format:\n"
            "`/bulk_set`\n"
            "`Movie Name 1 (2023) | Bollywood Movie`\n"
            "`Movie Name 2 (2021) | Hollywood Movie`\n"
            "`Web Series Name 1 | Web Series`"
        )
    
    m = await message.reply_text("⏳ **Bulk processing start ho rahi hai...**")
    success, failed = 0, 0
    failed_titles = []
    
    for line in lines:
        if "|" not in line:
            failed += 1
            continue
            
        try:
            parts = line.split("|")
            title_raw = parts[0].strip()
            new_cat = parts[1].strip().title()
            title_clean = unbold_and_clean(title_raw)
            
            result = await catalog_db.update_one(
                {"clean_title": {"$regex": f"^{re.escape(title_clean)}$", "$options": "i"}},
                {"$set": {"category": new_cat, "is_manually_edited": True}}
            )
            
            # Fallback loose search
            if result.matched_count == 0:
                result = await catalog_db.update_one(
                    {"clean_title": {"$regex": re.escape(title_clean), "$options": "i"}},
                    {"$set": {"category": new_cat, "is_manually_edited": True}}
                )
                
            if result.matched_count > 0:
                success += 1
            else:
                failed += 1
                failed_titles.append(title_clean)
        except Exception:
            failed += 1
            
    # Final Report Generation
    report = f"✅ **Bulk Update Complete!**\n━━━━━━━━━━━━━━━━━━━━\n📈 **Success:** `{success}`\n📉 **Failed:** `{failed}`\n"
    if failed_titles:
        report += f"\n❌ **Jo Titles Nahi Mile:**\n"
        for ft in failed_titles[:15]: # Limit to 15 to avoid telegram message length error
            report += f"↳ `{ft}`\n"
        if len(failed_titles) > 15:
            report += f"...aur {len(failed_titles) - 15} aur."
            
    await m.edit_text(report)

# ==========================================
# 🚀 INCREMENTAL SYNC ENGINE 
# ==========================================
@Client.on_message(filters.command("update_library") & filters.incoming)
async def update_lib_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return
    m = await message.reply_text("⏳ **Scanning for NEW titles only...**\n\nFast Sync Engine Active...")
    start_time = datetime.now()
    
    try:
        sync_state = await catalog_db.find_one({"_id": "sync_state"})
        last_synced_id = sync_state.get("last_synced_id") if sync_state else None
        
        cursor = Media.find({})
        cursor.sort("$natural", -1)
        
        docs_to_process = []
        newest_doc_id = None
        count = 0
        
        async for doc in cursor:
            if newest_doc_id is None:
                newest_doc_id = doc.file_id
            if last_synced_id and doc.file_id == last_synced_id:
                break
            docs_to_process.append(doc)
            count += 1
            if count % 2000 == 0: await asyncio.sleep(0.01) 
            
        if not docs_to_process:
            return await m.edit_text("✅ **Library is already up to date!**")
            
        docs_to_process.reverse() 
        added = 0
        
        for doc in docs_to_process:
            raw_name = getattr(doc, "file_name", "") or getattr(doc, "caption", "")
            if not raw_name: continue
                
            clean_name = html.unescape(str(raw_name))
            if '•' in clean_name: clean_name = clean_name.split('•')[-1].strip()
            if '[' in clean_name: clean_name = clean_name.split('[')[0].strip()
                
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', clean_name)
            year_str = f" ({year_match.group(1)})" if year_match else ""
            year_val = int(year_match.group(1)) if year_match else 0
            
            season_match = re.search(r'(?i)\b(s\d{1,2}|season\s*\d{1,2})\b', clean_name)
            cut_pattern = r'(?i)(1080p|720p|480p|2160p|4k|web-?dl|webrip|hdrip|camrip|dvdscr|x264|x265|hevc|esubs?|hindi|hin|tamil|telugu|english|eng|dual|multi|bluray|uncut|org|@\w+|www\.\S+)'
            match = re.search(cut_pattern, clean_name)
            if match: clean_name = clean_name[:match.start()]
                
            clean_name = re.sub(r'(?i)\s+(mkv|mp4|avi|webm)$', '', clean_name)
            if year_match: clean_name = clean_name.replace(year_match.group(1), '')
            if season_match: clean_name = re.sub(r'(?i)\b(s\d{1,2}|season\s*\d{1,2})\b', '', clean_name)
            
            clean_name = re.sub(r'(?i)\b(e\d{1,3}\s*-\s*e\d{1,3}|e\d{1,3}\s*e\d{1,3})\b', '', clean_name)
            clean_name = re.sub(r'(?i)\b(ep\d{1,3}\s*-\s*ep\d{1,3}|ep\d{1,3}\s*ep\d{1,3})\b', '', clean_name)
            clean_name = re.sub(r'(?i)\b(e\d{1,3}|ep\d{1,3}|episode\s*\d{1,3})\b', '', clean_name)
            clean_name = re.sub(r'(?i)\b(complete|batch|all episodes|part\s*\d+|s\d{1,2}e\d{1,3})\b', '', clean_name)
                
            clean_name = re.sub(r'[._]+', ' ', clean_name)
            clean_name = re.sub(r'[^a-zA-Z0-9À-ÿ\s\-:\',\+&]', '', clean_name)
            clean_name = ' '.join(clean_name.split()).strip(' -:,').title()
            clean_name = re.sub(r"\'S\b", "'s", clean_name)
            
            if len(clean_name) < 2 or clean_name.lower() in ["season", "movie file"]:
                continue
                
            final_title = f"{clean_name} ({year_val})".strip() if year_val else clean_name
            
            dup_check = await catalog_db.find_one({"clean_title": final_title})
            if dup_check:
                continue

            search_query = f"{clean_name} {year_val}".strip().lower() if year_val else clean_name.lower()
            category = categorize_title(final_title, raw_name)
            
            doc_data = {
                "media_id": doc.file_id, 
                "clean_title": final_title,
                "search_query": search_query,
                "year": year_val,
                "category": category,
                "added_at": datetime.now(),
                "is_manually_edited": False
            }
            await catalog_db.insert_one(doc_data)
            added += 1
            if added % 50 == 0: await asyncio.sleep(0.01)
        
        if newest_doc_id:
            await catalog_db.update_one({"_id": "sync_state"}, {"$set": {"last_synced_id": newest_doc_id}}, upsert=True)
        await m.edit_text(f"⚡ **Sync Done!**\n\n🆕 New Unique Titles Added: `{added}`\n⏱️ Time Taken: `{(datetime.now() - start_time).seconds} seconds`")
    except Exception as e:
        await m.edit_text(f"❌ **Sync Failed!**\n\nError: `{str(e)}`")

@Client.on_message(filters.command("reset_catalog") & filters.incoming)
async def reset_catalog_cmd(client, message):
    if message.from_user.id not in ADMINS:
        return
    m = await message.reply_text("💣 **Executing Hard Reset Sequence...**")
    try:
        result = await catalog_db.delete_many({"is_manually_edited": {"$ne": True}})
        await catalog_db.delete_one({"_id": "sync_state"})
        await m.edit_text(f"🗑️ **Catalog Reset Complete!**\n\n❌ Automatic Records Deleted: `{result.deleted_count}`\n⚙️ Manual Custom Entries Saved: Safe!\n👉 Ab fresh build ke liye `/update_library` chalao.")
    except Exception as e:
        await m.edit_text(f"❌ **Reset Failed!**\nError: `{e}`")

# ==========================================
# 🌍 UI: MASTER HOME SCREEN
# ==========================================
@Client.on_message(filters.command(["explore", "discover"]) & filters.private)
async def explore_cmd(client, message):
    await send_explore_home(message)

# ==========================================
# 🌍 UI: MASTER HOME SCREEN CALLBACK (NEW MESSAGE FIX)
# ==========================================
@Client.on_callback_query(filters.regex(r"^exp_main$"))
async def exp_main_cb(client, query):
    await query.answer()
    
    # 🔥 PRO-FIX: Ab hum query ko hi pass karenge taaki same message seamlessly edit ho.
    # Naya message create karne wala logic (is_broadcast=True) band kar diya.
    await send_explore_home(
        message=query.message, 
        query=query, 
        is_broadcast=False, 
        mention=query.from_user.mention, 
        greeting="Welcome"
    )

async def send_explore_home(message, query=None, is_broadcast=False, mention="User", greeting="Welcome"):
    btn = [
        [InlineKeyboardButton("👑 ᴘʀᴇᴍɪᴜᴍ ᴍᴏᴠɪᴇs & sᴇʀɪᴇs 👑", callback_data="exp_premium#0")],
        [InlineKeyboardButton("🇮🇳 Bᴏʟʟʏᴡᴏᴏᴅ", callback_data="exp_feed#cat:Bollywood Movie#0"),
          InlineKeyboardButton("🇺🇸 Hᴏʟʟʏᴡᴏᴏᴅ", callback_data="exp_feed#cat:Hollywood Movie#0")],
        [InlineKeyboardButton("🎬 Sᴏᴜᴛʜ ᴍᴏᴠɪᴇs", callback_data="exp_feed#cat:South Movie#0"),
          InlineKeyboardButton("📺 Wᴇʙ Sᴇʀɪᴇs", callback_data="exp_feed#cat:Web Series#0")],
        [InlineKeyboardButton("🎞 Aɴɪᴍᴀᴛɪᴏɴ", callback_data="exp_feed#cat:Animation Movie#0"),
          InlineKeyboardButton("👳 Pᴜɴᴊᴀʙɪ", callback_data="exp_feed#cat:Punjabi Movie#0")],
        [InlineKeyboardButton("🌍 Oᴛʜᴇʀ Lᴀɴɢᴜᴀɢᴇs", callback_data="exp_lang_menu"),
          InlineKeyboardButton("🔎 Sᴇᴀʀᴄʜ Mᴏᴠɪᴇs ↗️", url="https://t.me/+jUo32x8VbPdlNTE1")],
        [InlineKeyboardButton("🆕 Rᴇᴄᴇɴᴛʟʏ Aᴅᴅᴇᴅ", callback_data="exp_feed#recent#0")],
        [InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close_data")]
    ]
    
    if is_broadcast:
        caption = f"👋  **{greeting} {mention}!**\n\n🍿  **Select Your Next Entertainment**\n🎬 Explore thousands of Movies & Web Series with just a few taps."
    else:
        # User ka mention safely uthana
        if query:
            user_mention = query.from_user.mention
        else:
            user_mention = message.from_user.mention if hasattr(message, "from_user") and message.from_user else "User"
            
        caption = f"👋 **Welcome {user_mention}!**\n\n🍿 **Select Your Next Entertainment**\n\n🎬 Explore thousands of Movies & Web Series with just a few taps."
        
    if query:
        # Edit Same Message (UX Upgrade)
        try: 
            await query.edit_message_media(
                media=InputMediaPhoto(media=EXPLORE_BANNER, caption=caption), 
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except MessageNotModified: 
            pass
    else:
        # New Message (Sirf Command ya Broadcast se aane par)
        return await message.reply_photo(
            photo=EXPLORE_BANNER, 
            caption=caption, 
            reply_markup=InlineKeyboardMarkup(btn)
        )

# ==========================================
# 🌐 UI: OTHER LANGUAGES SUB-MENU
# ==========================================
@Client.on_callback_query(filters.regex(r"^exp_lang_menu$"))
async def exp_lang_menu_cb(client, query):
    btn = [
        [InlineKeyboardButton("🇧🇩 Bᴇɴɢᴀʟɪ", callback_data="exp_feed#cat:Bengali Movie#0"), InlineKeyboardButton("🚩 Mᴀʀᴀᴛʜɪ", callback_data="exp_feed#cat:Marathi Movie#0")],
        [InlineKeyboardButton("🌾 Bʜᴏᴊᴘᴜʀɪ", callback_data="exp_feed#cat:Bhojpuri Movie#0"), InlineKeyboardButton("🇵🇰 Uʀᴅᴜ", callback_data="exp_feed#cat:Urdu Movie#0")],
        [InlineKeyboardButton("💠 Gᴜᴊᴀʀᴀᴛɪ", callback_data="exp_feed#cat:Gujarati Movie#0"), InlineKeyboardButton("🔱 Oᴅɪᴀ", callback_data="exp_feed#cat:Odia Movie#0")],
        [InlineKeyboardButton("🏠 Mᴀɪɴ Mᴇɴᴜ", callback_data="exp_main")]
    ]
    try: await query.edit_message_media(InputMediaPhoto(media=EXPLORE_BANNER, caption="🌐 **Other Regional Languages**\n━━━━━━━━━━━━━━━━━━━━\nSelect kijiye aapko kis language ka content dekhna hai:"), reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified: pass

# ==========================================
# 📅 UI: YEAR FILTER MENU 
# ==========================================
@Client.on_callback_query(filters.regex(r"^exp_year_menu#(.*)$"))
async def exp_year_menu_cb(client, query):
    base_filter = query.matches[0].group(1)
    current_year = datetime.now().year
    btn, row = [], []
    for y in range(current_year, current_year - 9, -1):
        row.append(InlineKeyboardButton(f"🎬 {y}", callback_data=f"exp_feed#{base_filter}_year:{y}#0"))
        if len(row) == 3:
            btn.append(row); row = []
    if row: btn.append(row)
    
    if base_filter.startswith("cat:") and base_filter.split(":")[1] in ["Bengali Movie", "Marathi Movie", "Bhojpuri Movie", "Urdu Movie", "Gujarati Movie", "Odia Movie"]:
        btn.append([InlineKeyboardButton("🔙 Bᴀᴄᴋ", callback_data="exp_lang_menu")])
    else:
        btn.append([InlineKeyboardButton("🔙 Bᴀᴄᴋ Tᴏ Mᴀɪɴ Mᴇɴᴜ", callback_data="exp_main")])
        
    try: await query.edit_message_media(InputMediaPhoto(media=EXPLORE_BANNER, caption="📅 **Filter By Year**\nSelect a year:"), reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified: pass

# ==========================================
# 👑 UI: EXCLUSIVE PREMIUM FEED
# ==========================================
@Client.on_callback_query(filters.regex(r"^exp_premium#(\d+)"))
async def exp_premium_cb(client, query):
    page = int(query.matches[0].group(1))
    user_id = query.from_user.id
    
    has_premium = False
    try:
        if hasattr(db, "has_premium_access"):
            has_premium = await db.has_premium_access(user_id)
        else:
            user = await db.get_user(user_id)
            if user:
                expiry = user.get("premium_expiry", 0)
                if isinstance(expiry, datetime): has_premium = expiry > datetime.now()
                else: has_premium = expiry > time.time()
    except Exception as e:
        print(f"Premium Check Error: {e}")

    premium_titles = await fetch_native_premium_titles()
    if not premium_titles: return await query.answer("📝 Koi Premium Title abhi database me nahi hai!", show_alert=True)
        
    premium_titles = premium_titles[::-1]
    items_per_page = 5  
    total_pages = math.ceil(len(premium_titles) / items_per_page)
    skip = page * items_per_page
    current_items = premium_titles[skip:skip+items_per_page]
    
    text = f"**👑 PREMIUM MOVIE'S & SERIES**\n━━━━━━━━━━━━━━━━━━━━\n📄 **Page:** {page + 1} / {total_pages}\n━━━━━━━━━━━━━━━━━━━━\n\n"
    bot_username = temp.U_NAME if hasattr(temp, "U_NAME") and temp.U_NAME else (await client.get_me()).username
    
    bold_get_file = f"[{to_bold('Get File')}]"
    bold_get_premium = f"[{to_bold('Get Premium')}]"
    
    for raw_title in current_items:
        # 🔥 TITLE FORMAT FIX: Lowercase ko Original jaisa Title Case banayega
        proper_title = raw_title.title().replace("'S", "'s")
        truncated_title = smart_truncate(proper_title)
        bold_title = to_bold(truncated_title) 
        
        # 🔥 PREMIUM CATEGORY ENGINE FIX: DB se Custom Category Check Karega
        clean_premium_title = unbold_and_clean(raw_title)
        cat_entry = await catalog_db.find_one({
            "clean_title": {"$regex": f"^{re.escape(clean_premium_title)}$", "$options": "i"}
        })
        
        if cat_entry and cat_entry.get("is_manually_edited"):
            cat = cat_entry.get("category")
        else:
            cat = categorize_title(raw_title, raw_title)
            
        short_cat = cat.replace(" Movie", "") 
        bold_cat = to_bold(short_cat) # 🔥 TO_BOLD CATEGORY
        
        safe_title = re.sub(r'[^a-zA-Z0-9\s]', '', raw_title)
        search_format = safe_title.strip().replace(" ", "-")
        
        if has_premium: 
            btn_link = f"<a href='https://t.me/{bot_username}?start=getfile-{search_format}'>{to_bold('[ Get File ]')}</a>"
        else: 
            btn_link = f"<a href='https://t.me/{bot_username}?start=reqpremium'>{to_bold('[ Get Premium ]')}</a>"
             
        text += f"🔸 **{bold_title}**\n↳ <code>[{bold_cat}]</code> — {btn_link}\n\n"
        
    text += "━━━━━━━━━━━━━━━━━━━━"
    
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("◀️ Pʀᴇᴠ", callback_data=f"exp_premium#{page-1}"))
    nav.append(InlineKeyboardButton("🏠 Hᴏᴍᴇ", callback_data="exp_main"))
    if page + 1 < total_pages: nav.append(InlineKeyboardButton("Nᴇxᴛ ▶️", callback_data=f"exp_premium#{page+1}"))
    
    try: await query.edit_message_media(InputMediaPhoto(media=EXPLORE_BANNER, caption=text), reply_markup=InlineKeyboardMarkup([nav]))
    except MessageNotModified: pass

# ==========================================
# 🚀 CORE ENGINE: DYNAMIC MULTI-FILTER FEED
# ==========================================
@Client.on_callback_query(filters.regex(r"^exp_feed#(.*?)#(\d+)"))
async def exp_feed_cb(client, query):
    filter_data = query.matches[0].group(1)
    page = int(query.matches[0].group(2))
    
    db_query = {"_id": {"$ne": "sync_state"}}
    title_header = "⚡ RECENTLY ADDED"
    
    is_global_feed = True
    for f in filter_data.split("_"):
        if f.startswith("cat:"):
            cat_name = f.split(":")[1]
            if cat_name != "recent":
                db_query["category"] = cat_name
                title_header = f"🏷️ {cat_name}"
                is_global_feed = False
        elif f.startswith("year:"):
            year_val = int(f.split(":")[1])
            db_query["year"] = year_val
            title_header += f" 📅 ({year_val})"

    items_per_page = 5  
    skip = page * items_per_page
    
    total_items = await catalog_db.count_documents(db_query)
    if total_items == 0: return await query.answer("Is filter me koi data nahi mila!", show_alert=True)
        
    total_pages = math.ceil(total_items / items_per_page)
    cursor = catalog_db.find(db_query).sort([("added_at", -1)]).skip(skip).limit(items_per_page)
    
    text = f"**{title_header}**\n━━━━━━━━━━━━━━━━━━━━\n📄 **Page:** {page + 1} / {total_pages}\n━━━━━━━━━━━━━━━━━━━━\n\n"
    bot_username = temp.U_NAME if hasattr(temp, "U_NAME") and temp.U_NAME else (await client.get_me()).username
    bold_get_file = f"[{to_bold('Get File')}]"
    
    async for doc in cursor:
        raw_title = doc.get('clean_title', 'Unknown')
        # 🔥 UNIFORM FORMAT FAILSAFE
        proper_title = raw_title.title().replace("'S", "'s")
        truncated_title = smart_truncate(proper_title)
        bold_title = to_bold(truncated_title) 
        cat = doc.get('category', 'Movie')
        
        search_query = doc.get('search_query', raw_title.lower())
        search_format = search_query.replace(" ", "-")
        bold_get_file = to_bold('[ Get File ]')
        
        if is_global_feed:
             bold_cat = to_bold(cat)
             text += f"🔹 **{bold_title}**\n↳ <code>[{bold_cat}]</code> — <a href='https://t.me/{bot_username}?start=getfile-{search_format}'>{bold_get_file}</a>\n\n"
        else:
             text += f"🔹 **{bold_title}**\n↳ <a href='https://t.me/{bot_username}?start=getfile-{search_format}'>{bold_get_file}</a>\n\n"
        
    text += "━━━━━━━━━━━━━━━━━━━━"
    
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"exp_feed#{filter_data}#{page-1}"))
    nav.append(InlineKeyboardButton("🏠 Home", callback_data="exp_main"))
    if page + 1 < total_pages: nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"exp_feed#{filter_data}#{page+1}"))
    btn = [nav]
    
    if "cat:" in filter_data and "year:" not in filter_data and not is_global_feed:
        btn.append([InlineKeyboardButton("📅 Fɪʟᴛᴇʀ Bʏ Yᴇᴀʀ", callback_data=f"exp_year_menu#{filter_data}")])
        
    if "year:" in filter_data: 
        base_cat = filter_data.split("_")[0]
        btn.append([InlineKeyboardButton("🔄 Cʟᴇᴀʀ Yᴇᴀʀ Fɪʟᴛᴇʀ", callback_data=f"exp_feed#{base_cat}#0")])
    elif filter_data.startswith("cat:") and filter_data.split(":")[1] in ["Bengali Movie", "Marathi Movie", "Bhojpuri Movie", "Urdu Movie", "Gujarati Movie", "Odia Movie"]:
        btn.append([InlineKeyboardButton("🌍 Bᴀᴄᴋ Tᴏ Lᴀɴɢᴜᴀɢᴇs", callback_data="exp_lang_menu")])
    elif filter_data.startswith("cat:") and filter_data.split(":")[1] in ["Hollywood Movie", "South Movie", "Punjabi Movie", "Animation Movie"]:
        btn.append([InlineKeyboardButton("🔙 Bᴀᴄᴋ Tᴏ Mᴀɪɴ Dᴀsʜʙᴏᴀʀᴅ", callback_data="exp_main")])
        
    try: await query.edit_message_media(InputMediaPhoto(media=EXPLORE_BANNER, caption=text), reply_markup=InlineKeyboardMarkup(btn))
    except MessageNotModified: pass

# ==========================================
# 🌟 BACKGROUND AUTO-BROADCASTER ENGINE (FIXED & SCALABLE)
# ==========================================
@Client.on_message(filters.command("auto_explore") & filters.user(ADMINS))
async def toggle_auto_explore(client, message):
    if len(message.command) == 2:
        cmd = message.command[1].lower()
        if cmd == "on":
            await explore_bcast_db.update_one({"_id": "settings"}, {"$set": {"is_on": True}}, upsert=True)
            await message.reply_text("✅ **Auto Explore Broadcast is now ON.**\n\n(Sends at 09:00 AM & 09:00 PM IST daily)")
        elif cmd == "off":
            await explore_bcast_db.update_one({"_id": "settings"}, {"$set": {"is_on": False}}, upsert=True)
            await message.reply_text("🚫 **Auto Explore Broadcast is now OFF.**")
        else:
            await message.reply_text("❌ Usage: `/auto_explore on` or `/auto_explore off`")
    else:
        settings = await explore_bcast_db.find_one({"_id": "settings"})
        status = "ON ✅" if settings and settings.get("is_on") else "OFF 🚫"
        await message.reply_text(f"**Auto Explore Status:** {status}\n\nUsage: `/auto_explore on` or `/auto_explore off`")

@Client.on_message(filters.command("test_bcast") & filters.user(ADMINS))
async def test_bcast_cmd(client, message):
    await message.reply_text("🚀 **Test Broadcast Started...**\nChecking users and sending menus...")
    asyncio.create_task(run_explore_broadcast(client, ""))

async def run_explore_broadcast(client, greeting):
    users = await db.get_all_users()
    success, failed = 0, 0
    
    btn = [
        [InlineKeyboardButton("👑 Pʀᴇᴍɪᴜᴍ Mᴏᴠɪᴇs & Sᴇʀɪᴇs 👑", callback_data="exp_premium#0")],
        [InlineKeyboardButton("🇮🇳 Bᴏʟʟʏᴡᴏᴏᴅ", callback_data="exp_feed#cat:Bollywood Movie#0"), 
         InlineKeyboardButton("🇺🇸 Hᴏʟʟʏᴡᴏᴏᴅ", callback_data="exp_feed#cat:Hollywood Movie#0")],
        [InlineKeyboardButton("🎬 Sᴏᴜᴛʜ Mᴏᴠɪᴇs", callback_data="exp_feed#cat:South Movie#0"), 
         InlineKeyboardButton("📺 Wᴇʙ Sᴇʀɪᴇs", callback_data="exp_feed#cat:Web Series#0")],
        [InlineKeyboardButton("🎞 Aɴɪᴍᴀᴛɪᴏɴ", callback_data="exp_feed#cat:Animation Movie#0"), 
         InlineKeyboardButton("👳‍♂️ Pᴜɴᴊᴀʙɪ", callback_data="exp_feed#cat:Punjabi Movie#0")],
        [InlineKeyboardButton("🌍 Oᴛʜᴇʀ Lᴀɴɢᴜᴀɢᴇs", callback_data="exp_lang_menu"), 
         InlineKeyboardButton("🔎 Sᴇᴀʀᴄʜ Mᴏᴠɪᴇs", url="https://t.me/+jUo32x8VbPdlNTE1")],
        [InlineKeyboardButton("🆕 Rᴇᴄᴇɴᴛʟʏ Aᴅᴅᴇᴅ", callback_data="exp_feed#recent#0")],
        [InlineKeyboardButton("❌ Cʟᴏsᴇ", callback_data="close_data")]
    ]
    
    async for user in users:
        user_id = user.get('id')
        first_name = user.get('name', 'User')
        mention = f"<a href='tg://user?id={user_id}'>{first_name}</a>"
        
        old_msg_data = await explore_user_msgs_db.find_one({"user_id": user_id})
        if old_msg_data and old_msg_data.get("msg_id"):
            try:
                await client.delete_messages(chat_id=user_id, message_ids=old_msg_data["msg_id"])
            except Exception:
                pass
                
        caption = f"👋 **{greeting} {mention}!**\n\n🍿 **Select Your Next Entertainment**\n━━━━━━━━━━━━━━━━━━━━\n🎬 Explore thousands of Movies & Web Series with just a few taps."
        
        try:
            sent_msg = await client.send_photo(
                chat_id=user_id,
                photo=EXPLORE_BANNER,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(btn)
            )
            if sent_msg:
                await explore_user_msgs_db.update_one(
                    {"user_id": user_id},
                    {"$set": {"msg_id": sent_msg.id}},
                    upsert=True
                )
                success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            try:
                sent_msg = await client.send_photo(chat_id=user_id, photo=EXPLORE_BANNER, caption=caption, reply_markup=InlineKeyboardMarkup(btn))
                await explore_user_msgs_db.update_one({"user_id": user_id}, {"$set": {"msg_id": sent_msg.id}}, upsert=True)
                success += 1
            except Exception:
                failed += 1
        except Exception as e:
            print(f"Broadcast Failed for user {user_id}: {e}")
            failed += 1
            
        await asyncio.sleep(0.1) 
        
    for admin in ADMINS:
        try:
            await client.send_message(admin, f"🚀 **Auto-Explore Broadcast Completed!**\n\n🌅 **Shift:** {greeting}\n📈 **Success:** {success}\n📉 **Failed:** {failed}")
        except: pass

async def bcast_loop(client):
    ist = pytz.timezone('Asia/Kolkata')
    while True:
        try:
            settings = await explore_bcast_db.find_one({"_id": "settings"})
            if settings and settings.get("is_on", False):
                now = datetime.now(ist)
                if (now.hour == 9 or now.hour == 21) and now.minute == 0:
                    last_run = settings.get("last_run", "")
                    current_run_id = f"{now.year}{now.month}{now.day}_{now.hour}"
                    
                    if last_run != current_run_id:
                        await explore_bcast_db.update_one({"_id": "settings"}, {"$set": {"last_run": current_run_id}})
                        greeting = "Good Morning ☀️" if now.hour == 9 else "Good Evening 🌙"
                        asyncio.create_task(run_explore_broadcast(client, greeting))
        except asyncio.CancelledError:
            break # Loop safely stop karne ke liye
        except Exception:
            pass # DB Network timeout hone par silently ignore karega aur bot hang nahi hoga
        
        await asyncio.sleep(45)

BCAST_TASK_STARTED = False

@Client.on_message(filters.all, group=-1000)
async def init_bcast_task(client, message):
    global BCAST_TASK_STARTED
    if not BCAST_TASK_STARTED:
        BCAST_TASK_STARTED = True
        asyncio.create_task(bcast_loop(client))
