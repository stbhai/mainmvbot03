from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import CHANNELS, MOVIE_UPDATE_CHANNEL, ADMINS , LOG_CHANNEL
from database.ia_filterdb import save_file, unpack_new_file_id
from utils import get_poster, temp
import re
from database.users_chats_db import db

processed_movies = set()
media_filter = filters.document | filters.video

@Client.on_message(filters.chat(CHANNELS) & media_filter)
async def media(bot, message):
    bot_id = bot.me.id
    media = getattr(message, message.media.value, None)
    if media.mime_type in ['video/mp4', 'video/x-matroska']: 
        media.file_type = message.media.value
        media.caption = message.caption
        success_sts = await save_file(media)
        if success_sts == 'suc' and await db.get_send_movie_update_status(bot_id):
            file_id, file_ref = unpack_new_file_id(media.file_id)
            await send_movie_updates(bot, file_name=media.file_name, caption=media.caption, file_id=file_id)
            
    return None
    
async def movie_name_format(file_name):
  filename = re.sub(r'http\S+', '', re.sub(r'@\w+|#\w+', '', file_name).replace('_', ' ').replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace('{', '').replace('}', '').replace('.', ' ').replace('@', '').replace(':', '').replace(';', '').replace("'", '').replace('-', '').replace('!', '')).strip()
  return filename

async def check_qualities(text, qualities: list):
    quality = []
    for q in qualities:
        if q in text:
            quality.append(q)
    quality = ", ".join(quality)
    return quality[:-2] if quality.endswith(", ") else quality

async def send_movie_updates(bot, file_name, caption, file_id):
    try:
        # --- FIXED LOGIC: Truncate hone se pehle original naam save kar lo ---
        raw_text = f"{caption} {file_name}"
        
        # Purana logic jo file name ko chota karta hai title ke liye
        year_match = re.search(r"\b(19|20)\d{2}\b", caption)
        year = year_match.group(0) if year_match else None      
        pattern = r"(?i)(?:s|season)0*(\d{1,2})"
        season = re.search(pattern, caption)
        if not season:
            season = re.search(pattern, file_name) 
        if year:
            file_name = file_name[:file_name.find(year) + 4]      
        if not year:
            if season:
                season = season.group(1) if season else None       
                file_name = file_name[:file_name.find(season) + 1]
            
        qualities = ["ORG", "org", "hdcam", "HDCAM", "HQ", "hq", "HDRip", "hdrip", 
                     "camrip", "WEB-DL", "CAMRip", "hdtc", "predvd", "DVDscr", "dvdscr", 
                     "dvdrip", "dvdscr", "HDTC", "dvdscreen", "HDTS", "hdts"]
        quality = await check_qualities(caption, qualities) or "HDRip"
        
        language = ""
        nb_languages = ["Hindi", "Bengali", "English", "Marathi", "Tamil", "Telugu", "Malayalam", "Kannada", "Punjabi", "Gujrati", "Korean", "Japanese", "Bhojpuri", "Dual", "Multi", "Japanese", "Spanish"]    
        for lang in nb_languages:
            if lang.lower() in caption.lower():
                language += f"{lang}, "
        language = language.strip(", ") or "ᴅᴏɴ'ᴛ ᴋɴᴏᴡ"
        
        movie_name = await movie_name_format(file_name)    
        
        if movie_name in processed_movies:
            return 
        processed_movies.add(movie_name)    
        
        # --- FIXED LOGIC: Original raw text mein season check karna ---
        season_match = re.search(r'(?i)(?:^|[\s._\-\[\]\(\)])(?:s|season)[\s._\-]*([0oO]?\d{1,2})(?:[\s._\-\[\]\(\)]|$)', raw_text)

        if season_match:
            label = "𝗡𝗘𝗪 𝗪𝗘𝗕 𝗦𝗘𝗥𝗜𝗘𝗦 𝗔𝗗𝗗𝗘𝗗"
            raw_season = season_match.group(1).upper().replace('O', '0')
            season_number = f"S{raw_season.zfill(2)}" 
            
            caption_message = (
                f"🚨 {label} 🚨\n\n"
                f"🎬<b>Title:</b> <code>{movie_name}</code>\n"
                f"🎯 <b>Season:</b> {season_number}\n"
                f"🎧 <b>Audio:</b> {language}\n"
                f"📀 <b>Quality:</b> {quality}\n\n"
                f"🌐 <b>Official Group:</b> <a href='https://t.me/+pEUmki3XiYI1OWI1'>Join Now</a>\n\n"
                f"👇 <b>Download ke liye niche button par click karein</b>"
            )
        else:
            label = "𝗡𝗘𝗪 𝗠𝗢𝗩𝗜𝗘 𝗔𝗗𝗗𝗘𝗗"
            
            caption_message = (
                f"🚨 {label} 🚨\n\n"
                f"🎬 <b>Title:</b> <code>{movie_name}</code>\n"
                f"🎧 <b>Audio:</b> {language}\n"
                f"📀 <b>Quality:</b> {quality}\n\n"
                f"🌐 <b>Official Group:</b> <a href='https://t.me/+pEUmki3XiYI1OWI1'>Join Now</a>\n\n"
                f"👇 <b>Download ke liye niche button par click karein</b>"
            )

        search_movie = movie_name.replace(" ", '-')
        movie_update_channel = await db.movies_update_channel_id()    
        
        btn = [[
            InlineKeyboardButton('📂 ɢᴇᴛ ғɪʟᴇ 📂', url=f'https://telegram.me/{temp.U_NAME}?start=getfile-{search_movie}')
        ],[
            InlineKeyboardButton('📥 ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ 📥', url=f'https://t.me/howtodownload_moviestorage/3')
        ]]
        reply_markup = InlineKeyboardMarkup(btn)
        
        # === TMDB POSTER FETCH LOGIC ===
        try:
            movie_data = await get_poster(movie_name)
            if movie_data and movie_data.get('poster'):
                poster_url = movie_data.get('poster')
            else:
                poster_url = "https://i.ibb.co/HpRDS9X5/x.jpg" # Fallback agar TMDB ko image na mile
        except Exception as e:
            print(f"Poster Fetch Error: {e}")
            poster_url = "https://i.ibb.co/HpRDS9X5/x.jpg"
            
        await bot.send_photo(movie_update_channel if movie_update_channel else MOVIE_UPDATE_CHANNEL, 
                             photo=poster_url, caption=caption_message, reply_markup=reply_markup)

  # === PHASE 4: PRO AUTO-NOTIFIER (SAFE BROADCAST) ===
        try:
            pending_requests = await db.get_pending_requests()
            sent_count = 0 # Telegram ban se bachne ka counter
            
            for req in pending_requests:
                req_movie_name = req.get("movie_name", "").lower()
                
                # 🛠️ BUG FIX 1: Exact Match Logic (Taaki Iron Man mangne par Iron Man 3 na chali jaye)
                # Word boundary (\b) use karke exact phrase match kar rahe hain
                if re.search(r'\b' + re.escape(req_movie_name) + r'\b', raw_text.lower()) or req_movie_name == movie_name.lower():
                    try:
                        # Same Pro-Minimal format with Year included
                        notify_text = (
                            f"✅ **'{movie_name}' is Uploaded!**\n\n"
                            f"➖➖➖➖➖➖➖➖➖➖\n"
                            f"🎬 Aapki requested file upload kar di gayi hai.\n"
                            f"👇 Download karne ke liye niche click karein."
                        )
                        notify_btn = [[
                            InlineKeyboardButton('🔍 Get File', url=f'https://telegram.me/{temp.U_NAME}?start=getfile-{search_movie}')
                        ]]
                        
                        # User ko DM bhejna
                        await bot.send_photo(
                            chat_id=req['user_id'],
                            photo=poster_url,
                            caption=notify_text,
                            reply_markup=InlineKeyboardMarkup(notify_btn)
                        )
                        
                        # Request puri ho gayi, toh DB se delete kar do
                        await db.delete_movie_request(req['user_id'], req['tmdb_id'])
                        
                        # 🛠️ BUG FIX 2: THE ANTI-BAN SHIELD
                        sent_count += 1
                        if sent_count % 15 == 0:
                            await asyncio.sleep(2) # Har 15 message ke baad 2 second ruko, taaki Telegram gussa na ho
                            
                    except pyrogram.errors.exceptions.flood_420.FloodWait as e:
                        print(f"FloodWait! Sleeping for {e.value} seconds...")
                        await asyncio.sleep(e.value + 1)
                    except Exception as e:
                        print(f"Failed to notify user {req['user_id']}: {e}")
                        
        except Exception as e:
            print(f"Auto-Notifier Error: {e}")
        # ====================================================
                             
    except Exception as e:
        print('Failed to send movie update. Error - ', e)
        await bot.send_message(LOG_CHANNEL, f'Failed to send movie update. Error - {e}')
