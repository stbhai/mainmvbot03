import logging
from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid
from info import AUTH_CHANNEL, LONG_IMDB_DESCRIPTION, IS_VERIFY , SETTINGS , START_IMG, TMDB_API_KEY
import asyncio
from pyrogram.types import Message
from pyrogram import enums
import pytz, re, os 
import aiohttp
import urllib.parse
from shortzy import Shortzy
from datetime import datetime
from typing import Any
from database.users_chats_db import db


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BANNED = {}
 
class temp(object):
    ME = None
    CURRENT=int(os.environ.get("SKIP", 2))
    CANCEL = False
    U_NAME = None
    B_NAME = None
    B_LINK = None
    SETTINGS = {}
    FILES_ID = {}
    USERS_CANCEL = False
    GROUPS_CANCEL = False    
    CHAT = {}
    BANNED_USERS = []
    BANNED_CHATS = []
def formate_file_name(file_name):
    file_name = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file_name.split()))
    return file_name
async def is_req_subscribed(bot, query):
    if await db.find_join_req(query.from_user.id):
        return True
    try:
        user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
    except UserNotParticipant:
        pass
    except Exception as e:
        logger.exception(e)
    else:
        if user.status != enums.ChatMemberStatus.BANNED:
            return True
    return False

async def get_poster(query, bulk=False, id=False, file=None, type="movie"):
    if not id:
        query = (query.strip()).lower()
        title = query
        year = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
        if year:
            year = list_to_str(year[:1])
            title = (query.replace(year, "")).strip()
        elif file is not None:
            year = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
            if year:
                year = list_to_str(year[:1])
        else:
            year = None

        search_query = urllib.parse.quote_plus(title)
        search_url = f"https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={search_query}"
        
        # 🔥 PRO-FIX 3: 3-Second Strict Timeout to stop TMDB from hanging the bot
        timeout = aiohttp.ClientTimeout(total=3)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(search_url) as resp:
                    data = await resp.json()
        except Exception:
            return None # Drop silently if TMDB fails
        
        if not data or not data.get("results"):
            return None
            
        filtered = [res for res in data["results"] if res.get("media_type") in ["movie", "tv"]]
        
        if year:
            year_filtered = []
            for res in filtered:
                release_date = res.get("release_date") or res.get("first_air_date") or ""
                if release_date.startswith(str(year)):
                    year_filtered.append(res)
            if year_filtered:
                filtered = year_filtered

        if not filtered:
            return None

        if bulk:
            bulk_data = []
            for res in filtered[:10]:
                bulk_title = res.get("title") or res.get("name")
                release_date = res.get("release_date") or res.get("first_air_date") or ""
                bulk_year = release_date.split("-")[0] if release_date else ""
                
                bulk_data.append({
                    'title': bulk_title, 
                    'id': res.get("id"), 
                    'year': bulk_year,   
                    'media_type': res.get("media_type")
                })
            return bulk_data
            
        item = filtered[0]
        tmdb_id = item["id"]
        media_type = item["media_type"]
    else:
        tmdb_id = query
        media_type = type # FIXED: Ab ye hardcoded 'movie' nahi hai, request ke hisab se set hoga

    details_url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=credits"
    
    timeout = aiohttp.ClientTimeout(total=3)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(details_url) as resp:
                movie = await resp.json()
    except Exception:
        return None

    if not movie or "id" not in movie:
        return None

    title = movie.get("title") or movie.get("name")
    release_date = movie.get("release_date") or movie.get("first_air_date") or "N/A"
    year_extracted = release_date.split("-")[0] if release_date != "N/A" else "N/A"
    
    genres = [g["name"] for g in movie.get("genres", [])]
    
    crew = movie.get("credits", {}).get("crew", [])
    cast_list = movie.get("credits", {}).get("cast", [])
    directors = [c["name"] for c in crew if c.get("job") == "Director"]
    cast = [c["name"] for c in cast_list[:5]]

    poster_path = movie.get("poster_path")
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://telegra.ph/file/default_poster.jpg"
    
    plot = movie.get("overview", "")
    if plot and len(plot) > 800:
        plot = plot[0:800] + "..."

    return {
        'title': title,
        'votes': movie.get("vote_count", 0),
        "aka": title,
        "seasons": movie.get("number_of_seasons", "N/A"),
        "box_office": f"${movie.get('revenue', 0):,}" if movie.get("revenue") else "N/A",
        'localized_title': title,
        'kind': media_type,
        "imdb_id": movie.get("imdb_id", f"tmdb{tmdb_id}"),
        "cast": list_to_str(cast),
        "runtime": f"{movie.get('runtime') or int(movie.get('episode_run_time', [0])[0] if movie.get('episode_run_time') else 0)} min",
        "countries": list_to_str([c.get("name") for c in movie.get("production_countries", [])]),
        "certificates": "N/A",
        "languages": list_to_str([l.get("english_name") for l in movie.get("spoken_languages", [])]),
        "director": list_to_str(directors),
        "writer": "N/A",
        "producer": "N/A",
        "composer": "N/A",
        "cinematographer": "N/A",
        "music_team": "N/A",
        "distributors": "N/A",
        'release_date': release_date,
        'year': year_extracted,
        'genres': list_to_str(genres),
        'poster': poster_url,
        'plot': plot,
        'rating': str(round(movie.get("vote_average", 0), 1)),
        'url': f'https://www.themoviedb.org/{media_type}/{tmdb_id}'
    }

async def users_broadcast(user_id, message, is_pin):
    try:
        m=await message.copy(chat_id=user_id)
        if is_pin:
            await m.pin(both_sides=True)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await users_broadcast(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        await db.delete_user(user_id)
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"

async def groups_broadcast(chat_id, message, is_pin):
    try:
        m = await message.copy(chat_id=chat_id)
        if is_pin:
            try:
                await m.pin()
            except:
                pass
        return "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await groups_broadcast(chat_id, message)
    except Exception as e:
        await db.delete_chat(chat_id)
        return "Error"

async def get_settings(group_id, pm_mode=False):
    # 🧠 SMART DETECTOR: Telegram User IDs positive hote hain (>=0) aur Groups negative hote hain.
    if group_id >= 0 or pm_mode:
        settings = SETTINGS.copy()
        
        from database.users_chats_db import db
        # ID '0' ko hum Master Global PM Database ki tarah treat kar rahe hain
        pm_settings = await db.get_settings(0)
        
        if pm_settings:
            settings["imdb"] = pm_settings.get("imdb", settings["imdb"])
            settings["spell_check"] = pm_settings.get("spell_check", settings["spell_check"])
            settings["auto_delete"] = pm_settings.get("auto_delete", settings["auto_delete"])
            settings["link"] = pm_settings.get("link", settings["link"])
            # 🔥 NEW: Ab PM mein bhi custom caption database se uthayega
            settings["caption"] = pm_settings.get("caption", settings.get("caption", "")) 
            
        return settings
        
    # Standard group settings (For Negative IDs)
    from database.users_chats_db import db
    settings = await db.get_settings(group_id)
    return settings
    
async def save_group_settings(group_id, key, value):
    current = await get_settings(group_id)
    current.update({key: value})
    temp.SETTINGS.update({group_id: current})
    await db.update_settings(group_id, current)

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def get_name(name):
    regex = re.sub(r'@\w+', '', name)
    return regex

def list_to_str(k):    
    if not k:
        return "N/A"
    elif len(k) == 1:
        return str(k[0])
    else:
        return ', '.join(str(item) for item in k)


async def get_shortlink(link, grp_id, is_second_shortener=False, is_third_shortener=False , pm_mode=False):
    if not pm_mode:
        settings = await get_settings(grp_id)
    else:
        settings = SETTINGS
    if IS_VERIFY:
        if is_third_shortener:             
            api, site = settings['api_three'], settings['shortner_three']
        else:
            if is_second_shortener:
                api, site = settings['api_two'], settings['shortner_two']
            else:
                api, site = settings['api'], settings['shortner']
        shortzy = Shortzy(api, site)
        try:
            link = await shortzy.convert(link)
        except Exception as e:
            link = await shortzy.get_quick_link(link)
    return link

def get_file_id(message: "Message") -> Any:
    media_types = (
        "audio",
        "document",
        "photo",
        "sticker",
        "animation",
        "video",
        "voice",
        "video_note",
    )    
    if message.media:
        for attr in media_types:
            media = getattr(message, attr, None)
            if media:
                setattr(media, "message_type", attr)
                return media

#def get_hash(media_msg: Message) -> str:
#    media = get_file_id(media_msg)
 #   return getattr(media, "file_unique_id", "")[:6]

def get_status():
    tz = pytz.timezone('Asia/Kolkata')
    hour = datetime.now(tz).time().hour
    if 5 <= hour < 12:
        sts = "𝐺𝑜𝑜𝑑 𝑀𝑜𝑟𝑛𝑖𝑛𝑔"
    elif 12 <= hour < 18:
        sts = "𝐺𝑜𝑜𝑑 𝐴𝑓𝑡𝑒𝑟𝑛𝑜𝑜𝑛"
    else:
        sts = "𝐺𝑜𝑜𝑑 𝐸𝑣𝑒𝑛𝑖𝑛𝑔"
    return sts

async def is_check_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except:
        return False

async def get_seconds(time_string):
    def extract_value_and_unit(ts):
        value = ""
        unit = ""
        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1
        unit = ts[index:].lstrip()
        if value:
            value = int(value)
        return value, unit
    value, unit = extract_value_and_unit(time_string)
    if unit == 's':
        return value
    elif unit == 'min':
        return value * 60
    elif unit == 'hour':
        return value * 3600
    elif unit == 'day':
        return value * 86400
    elif unit == 'month':
        return value * 86400 * 30
    elif unit == 'year':
        return value * 86400 * 365
    else:
        return 0

def get_readable_time(seconds):
    periods = [('days', 86400), ('hour', 3600), ('min', 60), ('sec', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name}'
    return result

async def save_default_settings(id):
    await db.reset_group_settings(id)
    current = await db.get_settings(id)
    temp.SETTINGS.update({id: current})
