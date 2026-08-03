import subprocess
import sys

# === AUTOMATIC LIBRARY CHECKPOINT ===
try:
    import cachetools
except ImportError:
    print("⚠️ 'cachetools' library nahi mili. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cachetools"])
    import cachetools
    print("✅ 'cachetools' successfully installed!")
import asyncio
import re
import math
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, ChatPermissions, WebAppInfo, InputMediaAnimation
from pyrogram import Client, filters, enums
from pyrogram.errors import *
from utils import temp, get_settings, is_check_admin, get_status, get_size, save_group_settings, is_req_subscribed, get_poster, get_readable_time , formate_file_name
from database.users_chats_db import db, mydb
from database.ia_filterdb import Media, get_search_results, get_bad_files, get_file_details
import random
lock = asyncio.Lock()
import traceback
from fuzzywuzzy import process
import os
from pymongo import UpdateOne
from cachetools import TTLCache
import urllib.parse

# RAM Saver: Maximum 2000 items rahenge, aur har item 2 ghante (7200 sec) baad khud delete ho jayega.
BUTTONS = TTLCache(maxsize=2000, ttl=7200)
FILES_ID = TTLCache(maxsize=2000, ttl=7200)
ACTIVE_FILTERS = TTLCache(maxsize=2000, ttl=7200)
CAP = TTLCache(maxsize=2000, ttl=7200)
DISAMBIGUATION_MAP = TTLCache(maxsize=2000, ttl=7200)
TMDB_MAP = TTLCache(maxsize=2000, ttl=7200)
import re
import html
import time
from rapidfuzz import process, fuzz

# === THE SMART CACHE SYSTEM (BULLETPROOF RAM SAVER) ===
GLOBAL_SEARCH_CACHE = {}
MAX_CACHE_SIZE = 200 # RAM me maximum 200 unique searches hi rahenge

from pyrogram import StopPropagation
from cachetools import TTLCache

# Naya RAM Cache sirf Firewall ke liye (Taaki bot slow na ho)
FIREWALL_CACHE = TTLCache(maxsize=5000, ttl=7200)

import re
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def generate_season_buttons(search_term, files):
    seasons_data = {}
    
    for file in files:
        fname = file.get("file_name", "") if isinstance(file, dict) else getattr(file, "file_name", "")
        
        # FIX 1: Sirf valid S01, Season 1 pakdega. "Vikings" ke last "s" ko ignore karega!
        s_match = re.search(r'(?i)(?:^|[\s_\[\(-])(?:s|season|sn)\s*0*(\d+)', fname)
        if s_match:
            s_num = int(s_match.group(1))
            y_match = re.search(r'(?i)(?:\(|\[)?(19\d{2}|20\d{2})(?:\)|\])?', fname)
            year = y_match.group(1) if y_match else ""
            
            if s_num not in seasons_data or (year and not seasons_data[s_num]):
                seasons_data[s_num] = year

    # 🔥 THE ULTIMATE BYPASS FIX: 
    # Agar koi season nahi mila, YA FIR sirf 1 hi season hai, toh menu mat banao, seedha Files de do!
    if not seasons_data or len(seasons_data) <= 1:
        return False
        
    sorted_seasons = sorted(seasons_data.items())
    btn = []
    
    for s_num, year in sorted_seasons[:15]:
         year_str = f" ({year})" if year else ""
         btn_text = f"🎬 {search_term.title()} S{s_num:02d}{year_str}"
         safe_search = f"{search_term[:25]} S{s_num:02d}".strip()
         
         # SMOOTH UI FIX: Changed 'spell#' to 'fuz#' for instant background fetching
         btn.append([InlineKeyboardButton(btn_text, callback_data=f"fuz#{safe_search}")])
         
    return btn
    
    
# =====================================================
# 🛡️ THE ULTIMATE GLOBAL BUTTON FIREWALL
# =====================================================
@Client.on_callback_query(group=-1)
async def global_button_firewall(client, query):
    # 1. Private chat mein firewall ki zaroorat nahi hai
    if query.message.chat.type == enums.ChatType.PRIVATE:
        return 
        
    # 2. Public buttons jo koi bhi daba sakta hai (Whitelisted)
    public_buttons = ["close_data", "seeplans", "reqprem", "about", "features", "start", "reffff"]
    if query.data in public_buttons or query.data.startswith("reqprem"):
        return
        
    # 3. Main Security Logic (Telegram Bug Bypass)
    msg_id = query.message.id
    chat_id = query.message.chat.id
    cache_key = f"{chat_id}_{msg_id}"
    
    try:
        # Check karo ki kya humne is message ka owner pehle se RAM me save kiya hai
        owner_id = FIREWALL_CACHE.get(cache_key)
        
        if not owner_id:
            # TELEGRAM LIMITATION BYPASS: Callback query me reply_to_message nahi aata.
            # Isliye humein API se original message fetch karna padega (Sirf pehli baar).
            fetched_msg = await client.get_messages(chat_id, msg_id)
            
            # 🔥 PRO-FIX 2: Added None check for Anonymous Admins & channel posts
            if fetched_msg.reply_to_message and fetched_msg.reply_to_message.from_user:
                owner_id = fetched_msg.reply_to_message.from_user.id
                FIREWALL_CACHE[cache_key] = owner_id # RAM me save kar lo taaki agli baar API hit na ho
            else:
                # Agar user ne apna original search message delete kar diya ho
                FIREWALL_CACHE[cache_key] = "DELETED"
                return # Allow kar do kyunki owner track karna ab impossible hai
                
        if owner_id == "DELETED":
            return
            
        # Asli Cheking: Agar click karne wala aur asli owner alag hain -> SEEDHA BLOCK
        if query.from_user.id != owner_id:
            try:
                await query.answer("❌ Not Your Request!\n\nYeh action sirf usi user ke liye hai jisne yeh Request bheji hai.", show_alert=True)
            except Exception:
                pass # QUERY_ID_INVALID bypass
            raise StopPropagation  # Yahi par code kill, aage ka koi function nahi chalega
            
    except StopPropagation:
        raise # Isko wapas raise karna zaroori hai varna Pyrogram flow nahi rokega
    except Exception as e:
        # Fail-safe mechanism taaki error aane par bot crash na ho
        print(f"Firewall Error: {e}")
        pass
# =====================================================
async def get_cached_sorted_dicts(search):
    global GLOBAL_SEARCH_CACHE
    current_time = time.time()
    
    # 1. Time-Based Cleanup: 10 minute purane searches ko kachre me daalo
    keys_to_delete = [k for k, v in GLOBAL_SEARCH_CACHE.items() if current_time - v['time'] > 600]
    for k in keys_to_delete:
        del GLOBAL_SEARCH_CACHE[k]
        
    search_lower = search.lower().strip()
    
    # 2. Agar result Memory me hai, toh bina Database hit kiye wahi se de do
    if search_lower in GLOBAL_SEARCH_CACHE:
        return GLOBAL_SEARCH_CACHE[search_lower]["data"]
        
    # 3. Agar Memory me nahi hai, toh Database se nikalo
    files, _, _ = await get_search_results(search, max_results=300, offset=0)
    if not files: 
        return []
        
    sorted_dicts = get_vip_sorted_files(files, search)
    
    # 4. OVERLOAD PROTECTION (RAM FULL HONE SE ROKEGA)
    # Agar cache ki limit 200 cross ho gayi, toh sabse purana search uda do
    if len(GLOBAL_SEARCH_CACHE) >= MAX_CACHE_SIZE:
        oldest_key = next(iter(GLOBAL_SEARCH_CACHE))
        del GLOBAL_SEARCH_CACHE[oldest_key]
        
    # Naye search ko RAM me save karo
    GLOBAL_SEARCH_CACHE[search_lower] = {"time": current_time, "data": sorted_dicts}
    return sorted_dicts
	
# === RAPID-FUZZ IN-MEMORY CACHE SYSTEM (VIP + PHONETIC EDITION) ===
IN_MEMORY_TITLES = []
TITLE_MAP = {} 
GLOBAL_RECENT_LIST = [] # 🔥 NAYA: Explore Menu ke liye
CACHE_LOADED = False

async def build_title_cache():
    global IN_MEMORY_TITLES, TITLE_MAP, GLOBAL_RECENT_LIST, CACHE_LOADED
    if CACHE_LOADED: return
    
    print("⏳ Building Unified Master Cache (RapidFuzz + Explore)...")
    from database.ia_filterdb import Media
    
    # 🔥 THE MASTER FIX: Database ko exactly Newest -> Oldest order me scan karna
    cursor = Media.find({}).sort("_id", -1)
    
    GLOBAL_RECENT_LIST.clear()
    seen_explore_names = set()
    
    async for doc in cursor:
        raw_name = str(doc.file_name)
        raw_name = html.unescape(raw_name)
        
        # --- TERA ORIGINAL CLEANING LOGIC ---
        if '•' in raw_name:
            clean_name = raw_name.split('•')[-1].strip()
        else:
            clean_name = raw_name

        if '[' in clean_name:
            clean_name = clean_name.split('[')[0].strip()
            
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', clean_name)
        year_str = f" ({year_match.group(1)})" if year_match else ""
        year_val = year_match.group(1) if year_match else ""
        
        season_match = re.search(r'(?i)\b(s\d{1,2}|season\s*\d{1,2})\b', clean_name)
        season_str = ""
        if season_match:
            s_num = int(re.sub(r'[^0-9]', '', season_match.group()) or 1)
            season_str = f" S{str(s_num).zfill(2)}"
            
        cut_pattern = r'(?i)(1080p|720p|480p|2160p|4k|web-?dl|webrip|hdrip|camrip|dvdscr|x264|x265|hevc|esubs?|hindi|hin|tamil|telugu|english|eng|dual|multi|bluray|uncut|org|@\w+|www\.\S+)'
        match = re.search(cut_pattern, clean_name)
        if match:
            clean_name = clean_name[:match.start()]
            
        clean_name = re.sub(r'(?i)\s+(mkv|mp4|avi|webm)$', '', clean_name)

        if year_match:
            clean_name = clean_name.replace(year_match.group(1), '')
        if season_match:
            clean_name = re.sub(r'(?i)\b(s\d{1,2}|season\s*\d{1,2})\b', '', clean_name)
            
        # 🔥 CACHE FIX: Remove E01-E10, Combined, Complete so Memory stays clean
        clean_name = re.sub(r'(?i)\b(e\d{1,3}(?:\-e?\d{1,3})?|ep\d{1,3}(?:\-ep?\d{1,3})?|episode\s*\d{1,3})\b', '', clean_name)
        clean_name = re.sub(r'(?i)\b(complete|combined|all episodes|comp|part\s*\d+)\b', '', clean_name)
            
        clean_name = re.sub(r'[._]+', ' ', clean_name)
        clean_name = re.sub(r'[^a-zA-Z0-9\s\-:\',\+&]', '', clean_name)
        clean_name = ' '.join(clean_name.split()).strip(' -:,').title()
        clean_name = re.sub(r"\'S\b", "'s", clean_name)

        if len(clean_name) < 2 or clean_name.lower() in ["season", "complete", "combined", "movie file"]:
            continue
            
        # 1. RAPIDFUZZ KE LIYE
        final_title = f"{clean_name}{season_str}{year_str}"
        try:
            display_name = to_bold(final_title)
        except:
            display_name = final_title
        
        payload_name = f"{clean_name}{season_str} {year_val}".strip().lower()
        payload_name = re.sub(r'\s+', ' ', payload_name) 
        
        hidden_key = payload_name.replace("ee", "i").replace("oo", "u").replace("aa", "a")
        
        if hidden_key not in IN_MEMORY_TITLES:
            IN_MEMORY_TITLES.append(hidden_key)
        if hidden_key not in TITLE_MAP:
            TITLE_MAP[hidden_key] = set()
            
        TITLE_MAP[hidden_key].add((display_name, payload_name))
        
        # 2. 🔥 EXPLORE MENU KE LIYE (Naya Logic) 🔥
        # Series me S01, S02 uda diya, sirf base name aur year rakha
        explore_display_name = f"{clean_name}{year_str}".strip()
        explore_search_key = explore_display_name.lower()
        
        if explore_search_key not in seen_explore_names:
            seen_explore_names.add(explore_search_key)
            GLOBAL_RECENT_LIST.append(explore_display_name)
            
    CACHE_LOADED = True
    print(f"✅ Unified Cache Loaded: {len(IN_MEMORY_TITLES)} RapidFuzz | {len(GLOBAL_RECENT_LIST)} Explore Titles")
# zishan [
from database.jsreferdb import referdb
from database.config_db import mdb
import logging
from urllib.parse import quote_plus
from Jisshu.util.file_properties import get_name, get_hash, get_media_file_size
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
# ] codes add

# === PREMIUM FILE SIZE LIMIT ===
PREMIUM_LIMIT = 1932735283 # 1.5 GB in bytes

# === CUSTOM BOLD FORMATTERS ===
def to_bold(text):
    bold_map = str.maketrans(
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.",
        "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇."
    )
    return str(text).translate(bold_map)

def get_size_compact(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units) - 1:
        i += 1
        size /= 1024.0
        
    if units[i] in ["Bytes", "KB", "MB"]:
        size_str = f"{int(size)}"
    else:
        size_str = f"{size:.1f}".rstrip('0').rstrip('.')
        
    formatted_size = f"{size_str}{units[i]}"
    return to_bold(formatted_size)

import re

def get_vip_sorted_files(files, search_query=""):
    parsed_files = []
    search_query_lower = search_query.lower().strip()
    
    for file in files:
        raw_name = str(file.file_name)
        raw_caption = str(getattr(file, 'caption', '')) if getattr(file, 'caption', None) else ""
        
        # Caption se HTML tags saaf karo
        clean_caption = re.sub(r'<[^>]+>', ' ', raw_caption)
        
        # HYBRID SCANNER
        scan_text = (raw_name + " " + clean_caption).lower()
        
        # 1. QUALITY & FORMAT CLEANUP
        base_quality = "480p"
        
        # 'ds4k' ko temporary hide kar rahe hain taki wo '4k' me count na ho
        check_text = scan_text.replace("ds4k", "")
        
        if "2160p" in check_text or "4k" in check_text: base_quality = "4K"
        elif "1080p" in scan_text: base_quality = "1080p"
        elif "720p" in scan_text: base_quality = "720p"
        
        format_tag = ""
        if "hevc" in scan_text or "x265" in scan_text or "265x" in scan_text: format_tag += " HEVC"
        if "10bit" in scan_text: format_tag += " 10Bit"
        
        quality = f"{base_quality}{format_tag}".strip()
        
        # 2. AUDIO CATCHER (SMART DICTIONARY MAPPING)
        lang_map = {
            "hindi": "Hindi", "hin": "Hindi",
            "english": "English", "eng": "English", "en": "English",
            "tamil": "Tamil", "tam": "Tamil",
            "telugu": "Telugu", "tel": "Telugu",
            "malayalam": "Malayalam", "mal": "Malayalam",
            "kannada": "Kannada", "kan": "Kannada",
            "punjabi": "Punjabi", "pun": "Punjabi",
            "bengali": "Bengali", "ben": "Bengali",
            "marathi": "Marathi", "mar": "Marathi",
            "gujarati": "Gujarati", "guj": "Gujarati",
            "odia": "Odia", "odi": "Odia",
            "urdu": "Urdu",
            "bhojpuri": "Bhojpuri", "bhoj": "Bhojpuri",
            "korean": "Korean", "kor": "Korean",
            "japanese": "Japanese", "jap": "Japanese",
            "spanish": "Spanish", "spa": "Spanish",
            "chinese": "Chinese", "chi": "Chinese"
        }
        
        found_audios = []
        words = re.findall(r'[a-zA-Z]+', scan_text)
        for word in words:
            if word in lang_map and lang_map[word] not in found_audios:
                found_audios.append(lang_map[word])
                
        # Handle default Dual/Multi cases if missing
        if not found_audios:
            if "multi" in scan_text: found_audios.append("Multi")
            elif "dual" in scan_text: found_audios.append("Dual")
        
        # 🛑 THE ULTIMATE FIX: Jhooth bolne se achha sach batao
        if len(found_audios) == 0:
            audio = "[Orig Audio]" # Fake Hindi default hata diya gaya hai!
        elif len(found_audios) == 1:
            audio = f"[{found_audios[0]}]"
        elif len(found_audios) == 2:
            audio = f"[{found_audios[0][:3]}+{found_audios[1][:3]}]"
        else:
            audio = "[Multi]"
            
       # 3. WEB SERIES SAFE EXTRACTION (RANGE CHRONO PROV)
        # 🔥 PRO-FIX 1: Replace special dashes and bullets so regex catches them perfectly
        raw_name = raw_name.replace('–', '-').replace('—', '-').replace('•', '-')
        clean_caption = clean_caption.replace('–', '-').replace('—', '-').replace('•', '-')
        
        raw_name = re.sub(r'(?i)(s\d{1,2})(e\d{1,2})', r'\1 \2', raw_name)
        clean_caption = re.sub(r'(?i)(s\d{1,2})(e\d{1,2})', r'\1 \2', clean_caption)
        
        season_match = re.search(r'(?i)\b(s\d{1,2}|season\s*\d{1,2})\b', raw_name)
        if not season_match: 
            season_match = re.search(r'(?i)\b(s\d{1,2}|season\s*\d{1,2})\b', clean_caption)
            
        s_num = 999  
        season_str = ""
        if season_match:
            extracted_s = re.sub(r'[^0-9]', '', season_match.group())
            s_num = int(extracted_s) if extracted_s else 1
            season_str = f" S{str(s_num).zfill(2)}"
            
        # Hardcore Range Match Logic
        ep_match = re.search(r'(?i)\b(e\d{1,2}\-\d{1,2}|e\d{1,2}\-e\d{1,2}|ep\s*\d{1,2}\-\d{1,2})\b', raw_name)
        if not ep_match:
            ep_match = re.search(r'(?i)\b(e\d{1,2}\-\d{1,2}|e\d{1,2}\-e\d{1,2}|ep\s*\d{1,2}\-\d{1,2})\b', clean_caption)
            
        ep_str = ""
        e_num = 999  
        has_range = False
        
        if ep_match:
            has_range = True
            e_val = ep_match.group().upper().replace('EPISODE', '').replace('EP', '')
            ep_str = f" [{e_val}]"
            num_find = re.search(r'\d+', e_val)
            e_num = int(num_find.group()) if num_find else 998 
        else:
            single_ep = re.search(r'(?i)\b(e\d{1,2}|ep\s*\d{1,2}|episode\s*\d{1,2})\b', raw_name)
            if not single_ep:
                single_ep = re.search(r'(?i)\b(e\d{1,2}|ep\s*\d{1,2}|episode\s*\d{1,2})\b', clean_caption)
            if single_ep:
                e_clean = single_ep.group().lower().replace('episode', '').replace('ep', '').replace('e', '').strip()
                ep_str = f" E{e_clean.zfill(2)}"
                num_find = re.search(r'\d+', e_clean)
                if num_find: e_num = int(num_find.group())
                
        if not ep_str and any(word in scan_text for word in ["complete", "combined", "batch", "all episodes"]):
            ep_str = ""
            
        is_combined = False
        if season_str and (not ep_str or "complete" in scan_text or "combined" in scan_text):
            is_combined = True
            e_num = -2 
            
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', raw_name)
        if not year_match:
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', clean_caption)
        year_str = f" ({year_match.group(1)})" if year_match else ""
        
       # 4. MASTER CLEANUP (MIN-INDEX SLICING)
        # ---> PERMANENT CAPTION BYPASS + HTML DECODE FIX <---
        import html
        
        # Telegram se aane wale HTML codes (jaise &#x27;) ko asli characters (') mein badlo
        raw_name = html.unescape(raw_name)
        if clean_caption:
            clean_caption = html.unescape(clean_caption)
            
        clean_name = raw_name
        
        if clean_caption:
            # Caption ki pehli line ko nikalna
            first_line = clean_caption.split('\n')[0].strip()
            
            # --- START SMART CLEANING ---
            first_line = re.sub(r'(?i)^(title|name|movie|file)\s*.*?:\s*', '', first_line).strip()
            first_line = re.sub(r'^[^\w\s\(\)\[\]]+', '', first_line).strip()
            first_line = re.sub(r'\[.*?\]', '', first_line)
            first_line = re.sub(r'(?i)\.(mkv|mp4|avi|srt|txt)$|\.[a-zA-Z0-9]{3}$', '', first_line)
            first_line = re.sub(r'\s+', ' ', first_line).strip()
            # --- END SMART CLEANING ---
            
            if len(first_line) > len(raw_name) and "t.me" not in first_line.lower() and "@" not in first_line and "join" not in first_line.lower():
                clean_name = first_line

        # 🔥 PRO-FIX 2: Advanced Front-Stripper Loop
        while True:
            prev_name = clean_name
            # Pehle aane wale tags (720p, S05, E06-E10, Comp, Combined) ko safely udao
            clean_name = re.sub(r'(?i)^\s*\[?(?:1080p|720p|480p|2160p|4k|hevc|x265|265x|10bit|s\d{1,2}|e\d{1,3}(?:\-e?\d{1,3})?|comp|complete|all episodes|combined)\]?\b\s*[-_|\s]*\s*', '', clean_name)
            if clean_name == prev_name:
                break
        
       # Start me bache hue loose brackets ko uda do
        clean_name = re.sub(r'^[^\w\s\(\)\[\]]+', '', clean_name).strip()

        # 🔥 PRO-FIX 3: MIDDLE STRIPPER (Remove Seasons, Episodes, Combined, Complete)
        clean_name = re.sub(r'(?i)\b(s\d{1,2}|season\s*\d{1,2})\b', '', clean_name)
        clean_name = re.sub(r'(?i)\b(e\d{1,3}(?:\-e?\d{1,3})?|ep\d{1,3}(?:\-ep?\d{1,3})?|episode\s*\d{1,3})\b', '', clean_name)
        clean_name = re.sub(r'(?i)\b(complete|combined|all episodes|comp|part\s*\d+)\b', '', clean_name)

        clean_name = re.sub(r'\.(mkv|mp4|avi|webm|zip|rar|Mkv)$', '', clean_name, flags=re.IGNORECASE)
        
        cut_indices = []
        if year_match:
            idx = clean_name.rfind(year_match.group(1))
            if idx > 2: cut_indices.append(idx)
            
        # 🔥 ULTIMATE END STRIPPER: Aakhir mein lage hue saare tags pakad lega
        cut_pattern = r'(?i)(1080p|720p|480p|2160p|4k|web-?dl|webrip|hdrip|camrip|dvdscr|x264|x265|hevc|esubs?|hindi|hin|tamil|telugu|malayalam|kannada|punjabi|marathi|bengali|gujarati|odia|urdu|bhojpuri|korean|japanese|chinese|spanish|english|eng|dual|multi|bluray|@\w+|www\.\S+|\[|\(|season\s*\d{1,2}\b|complete|combined|all episodes|comp)'
        match = re.search(cut_pattern, clean_name)
        if match and match.start() > 2:
            cut_indices.append(match.start())
            
        if cut_indices:
            # Jo faltoo tag sabse pehle aaya, wahi se aage ka kachra kaat do
            clean_name = clean_name[:min(cut_indices)]
                
        # Sirf Dot (.) aur Underscore (_) ko space banayenge
        clean_name = re.sub(r'[._]+', ' ', clean_name)
        
        # Hyphen (-), Colon (:), Comma (,), Apostrophe (') allow kar diya
        clean_name = re.sub(r'[^a-zA-Z0-9\s\-:\',\+&]', '', clean_name) 
        
        # Extra spaces hata kar aur aakhir me latakte hue dash/colon ko uda kar Title Case karna
        clean_name = ' '.join(clean_name.split()).strip(' -:,').title()
        
        # Python ke .title() ki wajah se "Schindler's" galati se "Schindler'S" ban jata hai, usko fix karne ke liye:
        clean_name = re.sub(r"\'S\b", "'s", clean_name)
        
        if not clean_name or clean_name.lower() in ["season", "complete", "combined"]: 
            clean_name = "Movie File" 
            
        # Increased limit drastically so real names aren't cut
        if len(clean_name) > 65:
            clean_name = clean_name[:62] + "..."
            
        # 5. PREMIUM IDENTIFICATION
        is_premium = 0
        if "1080p" in base_quality or "4K" in base_quality:
            is_premium = 1
            
        # 6. ASSEMBLY
        combined_tag = " (Complete)" if is_combined else ""
        final_title = f"{clean_name}{season_str}{ep_str}{year_str}{combined_tag}"
        
        # 7. ICON & SORTING RANK PARAMETERS
        icon = "👑" if is_premium == 1 else ("📁" if "720p" in base_quality else "📱")
        
        # --- SMART MATCH SCORE LOGIC ---
        match_score = 0
        clean_name_lower = clean_name.lower()
        if search_query_lower == clean_name_lower:
            match_score = 3  # Exact Match (Sabse Top Par)
        elif clean_name_lower.startswith(search_query_lower):
            match_score = 2  # Starts With (Sequels / Parts)
        elif search_query_lower in clean_name_lower:
            match_score = 1  # Contains (Beech me naam ho)
            
        file_year = int(year_match.group(1)) if year_match else 0
        file_size_bytes = getattr(file, "file_size", 0)

        # NAYA TIER LOGIC
        curr_tier = 1 if e_num == -2 else (2 if has_range else 3)

        parsed_files.append({
            "file": file,
            "clean_name": final_title,
            "quality": quality,
            "audio": audio,
            "icon": icon,
            "match_score": match_score, 
            "year": file_year,
            "name_for_sort": clean_name_lower,
            "is_premium": is_premium,        
            "is_series": 1 if season_str else 0, 
            "season": s_num,                
            "episode": e_num,               
            "file_size_bytes": file_size_bytes,
            "tier": curr_tier
        })
        
    # --- PERFECT AUTO-RANKING SORT ---
    parsed_files.sort(key=lambda x: (
        -x["match_score"],         # 1. Exact Match sabse upar
        x["name_for_sort"],        # 2. Ek jaise naam wali sabhi files group hongi
        x["season"],               # 3. Series priority: S01 -> S02 -> S03 (Movies hamesha S999 par set hain)
        x["tier"],                 # 4. Combined(1) -> Range(2) -> Single Eps(3)
        x["episode"],              # 5. Episode sorting: E01 -> E02 -> E03
        -x["year"],                # 6. Movies ke case me latest Year (2024 -> 2006) pehle aayega
        x["file_size_bytes"]       # 7. Size/Quality: 480p -> 720p -> 1080p
    ))

    # UI DIVIDER LOGIC 
    prev_tier = None
    prev_movie_id = None
    for item in parsed_files:
        curr_tier = item["tier"]
        curr_movie_id = f'{item["name_for_sort"]}_{item["year"]}'
        item["needs_divider"] = False
        
        if item["is_series"] == 1:
            # Web Series ke liye Divider (Jab Tier badle)
            if prev_tier is not None and prev_tier != curr_tier:
                item["needs_divider"] = True
        else:
            # Movies ke liye Smart Divider (Jab Movie Name + Year badle)
            if prev_movie_id is not None and prev_movie_id != curr_movie_id:
                item["needs_divider"] = True
                
        prev_tier = curr_tier
        prev_movie_id = curr_movie_id

    # ---> UX TEXT WALL FIX (THE FLIP STRATEGY + EXTREME BOLD) <---
    for item in parsed_files:
        # 1. Flip Logic (Sirf single episodes (Tier 3) ke liye)
        if item["is_series"] == 1 and item["tier"] == 3:
            s_tag = f" S{str(item['season']).zfill(2)}"
            e_tag = f" E{str(item['episode']).zfill(2)}"
            
            # Asli naam me se Season/Ep hata kar base name nikalo
            base_name = item['clean_name'].replace(s_tag, "").replace(e_tag, "").strip()
            
            # Episode number aage, Base name piche
            item["clean_name"] = f"{s_tag.strip()} {e_tag.strip()} ┃ {base_name}"
            
        # 2. BOLD LOGIC (Ye har file ke naam ko thick Unicode bold bana dega)
        item["clean_name"] = to_bold(item["clean_name"])

    return parsed_files
	
def get_filtered_dicts(key, sorted_dicts, ignore_key=None):
    # Ye function check karega ki memory me kitne filter active hain aur sabko ek sath apply karega
    filters = ACTIVE_FILTERS.get(key, {})
    if not filters: return sorted_dicts
    
    filtered = []
    for item in sorted_dicts:
        match = True
        if 'season' in filters and ignore_key != 'season' and item.get('season') != filters['season']:
            match = False
        if 'year' in filters and ignore_key != 'year' and item.get('year') != filters['year']:
            match = False
        if 'language' in filters and ignore_key != 'language':
            clean_audio = item["audio"].replace("[", "").replace("]", "")
            if clean_audio != filters['language']: match = False
        if 'quality' in filters and ignore_key != 'quality':
            base_q = str(item.get("quality", "720P")).upper()
            file_name = str(getattr(item["file"], "file_name", "")).upper()
            final_q = base_q
            if "HEVC" in file_name or "X265" in file_name:
                if "HEVC" not in final_q: final_q += " HEVC"
            if "10BIT" in file_name or "10-BIT" in file_name or "10 BIT" in file_name:
                if "10BIT" not in final_q: final_q += " 10BIT"
            if final_q != filters['quality']: match = False
                
        if match:
            filtered.append(item)
    return filtered

def inject_filter_buttons(btn, key, offset, req, has_series):
    # Ye function active filters par ✅ lagayega aur clear button add karega
    filters = ACTIVE_FILTERS.get(key, {})
    
    q_text = f"✅ {filters['quality']}" if 'quality' in filters else "ǫᴜᴀʟɪᴛʏ"
    l_text = f"✅ {filters['language']}" if 'language' in filters else "ʟᴀɴɢᴜᴀɢᴇ"
    
    if has_series:
        s_text = f"✅ S{filters['season']:02d}" if 'season' in filters else "ꜱᴇᴀꜱᴏɴ"
        mid_btn = InlineKeyboardButton(s_text, callback_data=f"seasons#{key}#{offset}#{req}")
    else:
        y_text = f"✅ {filters['year']}" if 'year' in filters else "ʏᴇᴀʀ"
        mid_btn = InlineKeyboardButton(y_text, callback_data=f"years#{key}#{offset}#{req}")
        
    # Purane buttons ki jagah naye dynamic buttons
    btn.insert(1, [
        InlineKeyboardButton(q_text, callback_data=f"qualities#{key}#{offset}#{req}"),
        mid_btn,
        InlineKeyboardButton(l_text, callback_data=f"languages#{key}#{offset}#{req}")
    ])
    
    # Agar filter active hai, to Clear button do
    if filters:
        btn.insert(2, [InlineKeyboardButton("🗑 ᴄʟᴇᴀʀ ᴀʟʟ ꜰɪʟᴛᴇʀs", callback_data=f"clear_filters#{key}#{req}#{offset}")])
        
    return btn

async def get_smart_search_results(search, offset=0, max_results=None):
    try:
        offset = int(offset) if offset else 0
    except:
        offset = 0
        
    limit = int(MAX_BTN) if max_results is None else int(max_results)
    
    # 💥 CACHE SYSTEM IN ACTION 💥 (Seedha Cache se fetch karo)
    sorted_dicts = await get_cached_sorted_dicts(search)
    
    if not sorted_dicts:
        return [], "", 0
        
    # 3. Sort hui files ko wapas original list me badlo
    sorted_files = [item["file"] for item in sorted_dicts]
    
    # 4. Ab manually unhe 10-10 ke panno (pages) me kaato
    paginated_files = sorted_files[offset : offset + limit]
    total = len(sorted_files)
    
    n_offset = offset + limit
    if n_offset >= total:
        n_offset = ""
        
    return paginated_files, n_offset, total

# === HYBRID DESI TYPO CACHE SYSTEM ===
DESI_TYPO_DICT = {}
TYPOS_LOADED = False

@Client.on_message(filters.command("add_typo") & filters.user(ADMINS))
async def add_typo_cmd(client, message):
    global TYPOS_LOADED, DESI_TYPO_DICT
    
    # BULK ADD LOGIC (Fastest Way)
    if message.reply_to_message and message.reply_to_message.text:
        lines = message.reply_to_message.text.split('\n')
        bulk_requests = []
        added = 0
        
        for line in lines:
            if "|" in line:
                wrong, right = line.split("|", 1)
                wrong = wrong.strip().lower()
                right = right.strip().lower()
                if wrong and right:
                    DESI_TYPO_DICT[wrong] = right
                    bulk_requests.append(UpdateOne({"wrong_name": wrong}, {"$set": {"right_name": right}}, upsert=True))
                    added += 1
                    
        if bulk_requests:
            await mydb.typos.bulk_write(bulk_requests)
            
        TYPOS_LOADED = True 
        return await message.reply_text(f"⚡ **{added} Typos Bulk Added in 1 Second!**")

    # SINGLE ADD LOGIC
    try:
        cmd_text = message.text.split(" ", 1)[1]
        wrong, right = cmd_text.split("|", 1)
        wrong = wrong.strip().lower()
        right = right.strip().lower()
    except Exception:
        return await message.reply_text("❌ **Format:** `/add_typo galat | sahi`")

    DESI_TYPO_DICT[wrong] = right
    await mydb.typos.update_one({"wrong_name": wrong}, {"$set": {"right_name": right}}, upsert=True)
    TYPOS_LOADED = True 
    await message.reply_text(f"✅ **Typo Added & Cached!**\n❌ `{wrong}` -> ✅ `{right}`")


@Client.on_message(filters.command("del_typo") & filters.user(ADMINS))
async def del_typo_cmd(client, message):
    global DESI_TYPO_DICT
    try:
        wrong = message.text.split(" ", 1)[1].strip().lower()
    except Exception:
        return await message.reply_text("❌ **Format:** `/del_typo galat_naam`")
    
    result = await mydb.typos.delete_one({"wrong_name": wrong})
    if result.deleted_count:
        if wrong in DESI_TYPO_DICT:
            del DESI_TYPO_DICT[wrong]
        await message.reply_text(f"✅ **Typo Deleted!**\n`{wrong}` ab hata diya gaya hai.")
    else:
        await message.reply_text(f"⚠️ **Not Found!**\n`{wrong}` database me hai hi nahi.")

@Client.on_message(filters.command("all_typos") & filters.user(ADMINS))
async def all_typos_cmd(client, message):
    count = await mydb.typos.count_documents({})
    if count == 0:
        return await message.reply_text("📂 **Typo Dictionary bilkul khali hai!**")
        
    msg = await message.reply_text("⏳ **List generate ho rahi hai...**")
    out = f"=== TOTAL TYPOS: {count} ===\n\n"
    async for doc in mydb.typos.find({}):
        out += f"{doc['wrong_name']} | {doc['right_name']}\n"
        
    with open("typo_list.txt", "w", encoding="utf-8") as f:
        f.write(out)
        
    await message.reply_document(document="typo_list.txt", caption=f"✅ **Total Saved Typos: {count}**")
    os.remove("typo_list.txt")
    await msg.delete()

async def advantage_spell_chok(message, searching_msg=None):
    raw_search = message.text.strip().lower()
    
    # === TIER 0: LOAD CACHE & MANUAL TYPOS ===
    await build_title_cache() 
    
    global TYPOS_LOADED, DESI_TYPO_DICT
    if not TYPOS_LOADED:
        DESI_TYPO_DICT.clear()
        async for doc in mydb.typos.find({}):
            DESI_TYPO_DICT[doc['wrong_name']] = doc['right_name']
        TYPOS_LOADED = True
        
    search = DESI_TYPO_DICT.get(raw_search, raw_search)

    # === TIER 1: DIRECT LOCAL MATCH ===
    files, offset, total_results = await get_smart_search_results(search)
    if files:
        if searching_msg:
            try: await searching_msg.delete()
            except: pass
        message.text = search
        client = getattr(message, '_client', getattr(message, 'client', None))
        return await auto_filter(client, message)

    # === TIER 2: THE API SCRUBBER (Kachra Chhantai) ===
    import re
    clean_search = re.sub(r'(?i)(1080p|720p|480p|2160p|4k|web-?dl|webrip|hdrip|camrip|dvdscr|x264|x265|hevc|10bit|hindi|hin|tamil|telugu|english|eng|dual|multi|bluray)', '', search).strip()
    clean_search = re.sub(r'\s+', ' ', clean_search).strip()
    
    if not clean_search:
        clean_search = search # Safety fallback

    # === TIER 3: RAPID-FUZZ (Desi Phonetic Check) ===
    desi_search = clean_search.replace("ee", "i").replace("oo", "u").replace("aa", "a")
    best_matches = await asyncio.to_thread(process.extract, desi_search, IN_MEMORY_TITLES, scorer=fuzz.token_sort_ratio, limit=6)
    highest_score = best_matches[0][1] if best_matches else 0

    # === THE SCORE-BASED SWITCH ===
    
    # 🟢 CASE A: HIGH MATCH (Local Database Win)
    if highest_score >= 60:  
        seen_base_names = set() # Sirf unique franchise dikhane ke liye
        buttons = []
        
        for match_str, score, _ in best_matches:
            if score >= 60:
                tuples_set = TITLE_MAP.get(match_str, set())
                for disp, payload_name in tuples_set:
                    base_name = re.sub(r'\b(19\d{2}|20\d{2})\b', '', payload_name)
                    base_name = re.sub(r'(?i)\bs\d{1,2}\b', '', base_name).strip().title()
                    
                    if base_name and base_name not in seen_base_names:
                        seen_base_names.add(base_name)
                        payload = f"spell#{base_name[:45].lower()}"
                        buttons.append([InlineKeyboardButton(f"✨ {base_name}", callback_data=payload)])
                        
                    if len(buttons) >= 4: break 
            if len(buttons) >= 4: break
            
        if buttons:
            buttons.append([InlineKeyboardButton("🌐 𝐅𝐢𝐧𝐝 𝐨𝐧 𝐓𝐌𝐃𝐁", callback_data=f"tmdb_search#{clean_search[:45]}")])
            buttons.append([InlineKeyboardButton("❌ Close", callback_data='close_data')])
            
            suggestion_text = (
                f"<b>⚠️ SPELLING MISMATCH</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🔍 <b>Search:</b> <code>{clean_search.title()}</code>\n\n"
                f"<i>Exact spelling nahi mili. Niche diye gaye options check karein.</i>\n\n"
                f"👇 <b>Agar aapki Movie/Series list mein nahi hai, toh TMDB par search karein:</b>"
            )
            # 🔥 EDIT INSTEAD OF NEW MESSAGE
            if searching_msg:
                k = await searching_msg.edit_text(text=suggestion_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)
            else:
                k = await message.reply_text(text=suggestion_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)
            TMDB_MAP[k.id] = clean_search 
            return k

    # 🔴 CASE B: LOW MATCH (TMDB Selection Menu)
    try:
        movies = await get_poster(clean_search, bulk=True)
    except Exception as e:
        print(f"TMDB Error: {e}")
        movies = None

    if movies:
        buttons = []
        user = message.from_user.id if message.from_user else 0
        
        for movie in movies[:8]:
            title = movie.get('title', 'Unknown')
            year = movie.get('year')
            year_str = str(year) if year else "N/A" 
            m_type = movie.get('media_type', 'movie')
            m_char = "t" if m_type == "tv" else "m"
            
            buttons.append([
                InlineKeyboardButton(text=f"🌐 {title} ({year_str})", callback_data=f"spol#{movie.get('id')}#{m_char}#{user}")
            ])
            
        buttons.append([InlineKeyboardButton("❌ Close", callback_data='close_data')])
        
        tmdb_fallback_text = (
            f"<b>✦ ᴛᴍᴅʙ sᴇᴀʀᴄʜ ʀᴇsᴜʟᴛs ✦</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔍 <b>Search:</b> <code>{clean_search.title()}</code>\n\n"
            f"<i>Yeh file database mein nahi mili, par TMDB par matches mil gaye hain.</i>\n\n"
            f"👇 <b>Apna exact title select karein:</b>"
        )
        
        # 🔥 EDIT INSTEAD OF NEW MESSAGE
        if searching_msg:
            k = await searching_msg.edit_text(text=tmdb_fallback_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)
        else:
            k = await message.reply_text(text=tmdb_fallback_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=enums.ParseMode.HTML)
        TMDB_MAP[k.id] = clean_search 
        return k

    # 🟡 CASE C: TOTAL TRASH SEARCH (Na Local, Na TMDB)
    google = urllib.parse.quote_plus(clean_search)
    button = [[
        InlineKeyboardButton("🔍 Check Spelling on Google", url=f"https://www.google.com/search?q={google}")
    ],[
        InlineKeyboardButton("📖 Search Guide", callback_data="search_guide"),
        InlineKeyboardButton("🚫 Close", callback_data="close_data")
    ]]
    
    not_found_text = (
        f"🛑 **SEARCH FAILED: SPELLING ERROR!**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"❌ **Aapka Input:** `{clean_search.title()}`\n\n"
        f"⚠️ **Kyon Fail Hua?**\n"
        f"Global TMDB bhi is naam ko nahi pehchaan paya. Iska seedha matlab hai ki aapki spelling puri tarah galat hai. Bot toote-foote naam aur tukke nahi samajhta.\n\n"
        f"🛠️ **Ab Karna Kya Hai?**\n"
        f"**1.** Niche 🔍 **Google** button dabaiye.\n"
        f"**2.** Wahan se Movie/Series ki **exact spelling** copy karein.\n"
        f"**3.** Wapas aakar yahan chat mein paste karein."
    )
    
    # 🔥 EDIT INSTEAD OF NEW MESSAGE
    if searching_msg:
        k = await searching_msg.edit_text(text=not_found_text, reply_markup=InlineKeyboardMarkup(button), parse_mode=enums.ParseMode.MARKDOWN)
    else:
        k = await message.reply_text(text=not_found_text, reply_markup=InlineKeyboardMarkup(button), parse_mode=enums.ParseMode.MARKDOWN)
    
    await asyncio.sleep(120)
    try:
        await k.delete()
    except:
        pass
    return

from info import ADMINS

@Client.on_message(filters.command("update_cache") & filters.user(ADMINS))
async def refresh_fuzz_cache(client, message):
    # Ye function purani RAM delete karke nayi RAM load karega bina bot restart kiye
    global CACHE_LOADED, IN_MEMORY_TITLES, TITLE_MAP
    
    m = await message.reply_text("⏳ **Refreshing Database Cache...**\nIsme 2-5 second lagenge.")
    
    # Purana kachra saaf karo
    CACHE_LOADED = False
    IN_MEMORY_TITLES.clear()
    TITLE_MAP.clear()
    
    # Naya cache build karo
    await build_title_cache()
    
    await m.edit_text(f"✅ **Cache Successfully Updated!**\n\nAb RapidFuzz nayi movies ko bhi search kar lega.\n🎬 Total Movies in Memory: `{len(IN_MEMORY_TITLES)}`")

@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_search(client, message):
    await mdb.update_top_messages(message.from_user.id, message.text)
    bot_id = client.me.id
    user_id = message.from_user.id
    
    if str(message.text).startswith('/'):
        return
        
    # --- LINK FILTER FIX FOR INDEXING ---
    # Agar message me koi link (t.me) hai, toh usko search mat karo!
    import re
    if re.findall(r'https?://\S+|www\.\S+|t\.me/\S+', message.text):
        return
    # ------------------------------------
    message.text = re.sub(r'(?i)season\s*(\d+)', lambda m: f"S{int(m.group(1)):02d}", message.text)
    is_premium = await db.has_premium_access(user_id)
    pm_search_status = await db.get_pm_search_status(bot_id)
    
    # Logic: Agar PM search ON hai, YA user Premium hai, toh search chalne do
    if pm_search_status or is_premium:
        if any(lang in message.text.lower() for lang in ['hindi', 'tamil', 'telugu', 'malayalam', 'kannada', 'english', 'gujarati']): 
            return await auto_filter(client, message)
        await auto_filter(client, message)
    else:
        # Jab PM search OFF ho aur user FREE ho, tab ye message jayega
        btn = [
            [InlineKeyboardButton("💎 GET PREMIUM NOW 💎", callback_data="seeplans")],
            [InlineKeyboardButton("💬 Join Official Group", url='https://t.me/+XQa4P8UuLf43NDBl')]
        ]
        
        caption = f"""
<b>🔒 𝐁𝐎𝐓 𝐒𝐄𝐀𝐑𝐂𝐇 𝐈𝐒 𝐋𝐎𝐂𝐊𝐄𝐃 🔒</b>

<b>Direct Bot Search ab sirf Premium Members ke liye available hai.</b>
🆓 <b>Free users hamare Official Group mein search kar sakte hain.</b>

⭐ <b>Premium upgrade karke Direct Bot Search unlock karein.</b>
👇 <b>Tap GET PREMIUM NOW to upgrade.</b>"""
        
        await message.reply_photo(
            photo="https://i.ibb.co/HmdxgtS/x.jpg",  # Yahan apni image link daal de
            caption=caption,
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )
        
    
@Client.on_message(filters.group & filters.text & filters.incoming)
async def group_search(client, message):
    PREMIUM_GROUP_ID = -1003920104895  
    if message.chat.id == PREMIUM_GROUP_ID:
        return
    await mdb.update_top_messages(message.from_user.id, message.text)
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id
    settings = await get_settings(chat_id)
 
    if message.chat.id == SUPPORT_GROUP :
                if message.text.startswith("/"):
                    return
                files, n_offset, total = await get_smart_search_results(message.text, offset=0)
                if total != 0:
                    link = await db.get_set_grp_links(index=1)
                    msg = await message.reply_text(script.SUPPORT_GRP_MOVIE_TEXT.format(message.from_user.mention(), total), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ 😉' , url='https://t.me/JisshuMovieZone')]]))
                    await asyncio.sleep(300)
                    return await msg.delete()
                else: return     
    if settings["auto_filter"]:
        if not user_id:
            return
        
        if 'hindi' in message.text.lower() or 'tamil' in message.text.lower() or 'telugu' in message.text.lower() or 'malayalam' in message.text.lower() or 'kannada' in message.text.lower() or 'english' in message.text.lower() or 'gujarati' in message.text.lower(): 
            return await auto_filter(client, message)

        elif message.text.startswith("/"):
            return
        
        elif re.findall(r'https?://\S+|www\.\S+|t\.me/\S+', message.text):
            if await is_check_admin(client, message.chat.id, message.from_user.id):
                return
            await message.delete()
            return await message.reply("<b>⚠️ SYSTEM ALERT:</b>\nLinks are not allowed in this group.")

        elif '@admin' in message.text.lower() or '@admins' in message.text.lower():
            if await is_check_admin(client, message.chat.id, message.from_user.id):
                return
            admins = []
            async for member in client.get_chat_members(chat_id=message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                if not member.user.is_bot:
                    admins.append(member.user.id)
                    if member.status == enums.ChatMemberStatus.OWNER:
                        if message.reply_to_message:
                            try:
                                sent_msg = await message.reply_to_message.forward(member.user.id)
                                await sent_msg.reply_text(f"#Attention\n★ User: {message.from_user.mention}\n★ Group: {message.chat.title}\n\n★ <a href={message.reply_to_message.link}>Go to message</a>", disable_web_page_preview=True)
                            except:
                                pass
                        else:
                            try:
                                sent_msg = await message.forward(member.user.id)
                                await sent_msg.reply_text(f"#Attention\n★ User: {message.from_user.mention}\n★ Group: {message.chat.title}\n\n★ <a href={message.link}>Go to message</a>", disable_web_page_preview=True)
                            except:
                                pass
            hidden_mentions = (f'[\u2064](tg://user?id={user_id})' for user_id in admins)
            await message.reply_text('<code>Report sent</code>' + ''.join(hidden_mentions))
            return               
        else:
            try: 
                await auto_filter(client, message)
            except Exception as e:
                traceback.print_exc()
                print('found err in grp search  :',e)

    else:
        k=await message.reply_text('<b>⚠️ ᴀᴜᴛᴏ ꜰɪʟᴛᴇʀ ᴍᴏᴅᴇ ɪꜱ ᴏғғ...</b>')
        await asyncio.sleep(10)
        await k.delete()

from pyrogram.types import InputMediaPhoto

	
@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return
    files, n_offset, total = await get_smart_search_results(search, offset=offset)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0
    if not files:
        return
    temp.FILES_ID[key] = files
    batch_ids = files
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = batch_ids
    batch_link = f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}"
    ads, ads_name, _ = await mdb.get_advirtisment()
    ads_text = ""
    if ads is not None and ads_name is not None:
        ads_url = f"https://t.me/{temp.U_NAME}?start=ads"
        ads_text = f"<a href={ads_url}>{ads_name}</a>"
    js_ads = f"\n━━━━━━━━━━━━━━━━━━\n <b>{ads_text}</b> \n━━━━━━━━━━━━━━━━━━" if ads_text else ""
    settings = await get_settings(query.message.chat.id)
    reqnxt  = query.from_user.id if query.from_user else 0
    temp.CHAT[query.from_user.id] = query.message.chat.id

    # 🔥 SMART BYPASS LOGIC FOR PREMIUM TITLES 🔥
    is_premium = await db.has_premium_access(reqnxt) if reqnxt else False
    for f in files:
        try:
            is_prem_title = await db.get_premium_info(f.file_name)
            if is_prem_title:
                is_premium = True
                break
        except:
            pass

    links = ""
    if settings["link"]:
        btn = []
        search_term = search if 'search' in locals() else BUTTONS.get(key, "")
        sorted_files = get_vip_sorted_files(files, search_term)
        
        for item in sorted_files:
            file = item["file"]
            file_size = get_size_compact(file.file_size)
            quality_str = to_bold(str(item["quality"]).upper())
            audio_str = to_bold(item["audio"])
            
            display_title = f'{item["icon"]} {item["clean_name"]}'
            sub_line = f"↳ <b>[{file_size}] • [{quality_str}] • {audio_str}</b>"
            
            divider = "\n▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n" if item.get("needs_divider") else "\n\n"
            
            if not is_premium and item.get("is_premium") == 1:
                links += f"""{divider}<b><a href="https://t.me/{temp.U_NAME}?start=reqprem">{display_title}</a></b>\n{sub_line}"""
            else:
                links += f"""{divider}<b><a href="https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}">{display_title}</a></b>\n{sub_line}"""
    else:
        btn = []
        search_term = search if 'search' in locals() else BUTTONS.get(key, "")
        sorted_files = get_vip_sorted_files(files, search_term)
        for item in sorted_files:
            file = item["file"]
            file_size = get_size_compact(file.file_size)
            quality_str = to_bold(str(item["quality"]).upper())
            audio_str = to_bold(item["audio"])
            display_text = f'[{file_size}] {item["icon"]} {item["clean_name"]} [{quality_str}] {audio_str}'
            
            if not is_premium and item.get("is_premium") == 1:
                btn.append([InlineKeyboardButton(text=f"{display_text}", callback_data="reqprem")])
            else:
                btn.append([InlineKeyboardButton(text=display_text, callback_data=f'cfiles#{reqnxt}#{file.file_id}')])
                
    btn.insert(0,[
	InlineKeyboardButton("📥 𝗦𝗲𝗻𝗱 𝗔𝗹𝗹 𝗙𝗶𝗹𝗲𝘀 📥", callback_data=batch_link),
        ])
    has_series = any(item.get("is_series", 0) == 1 for item in sorted_files)
    btn = inject_filter_buttons(btn, key, offset, req, has_series)    

    if 0 < offset <= int(MAX_BTN):
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - int(MAX_BTN)
    if n_offset == 0:

        btn.append(
            [InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"ᴘᴀɢᴇ {math.ceil(int(offset) / int(MAX_BTN)) + 1} / {math.ceil(total / int(MAX_BTN))}", callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(int(offset) / int(MAX_BTN)) + 1} / {math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"{math.ceil(int(offset) / int(MAX_BTN)) + 1} / {math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
                InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    if settings["link"]:
        await query.message.edit_text(cap + links + js_ads, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
        return        
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()
    
@Client.on_callback_query(filters.regex(r"^seasons#"))
async def seasons_cb_handler(client: Client, query: CallbackQuery):
    _, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
        
    search = BUTTONS.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        
    sorted_dicts = await get_cached_sorted_dicts(search)
    filtered_dicts = get_filtered_dicts(key, sorted_dicts, ignore_key='season')
    
    found_seasons = set()
    for item in filtered_dicts:
        if item["is_series"] == 1 and item["season"] != 999:
            found_seasons.add(item["season"])
            
    sorted_seasons = sorted(list(found_seasons))

    btn = []
    for s in sorted_seasons:
        season_str = f"S{str(s).zfill(2)}"
        btn.append(
            InlineKeyboardButton(season_str, callback_data=f"season_search#{s}#{key}#0#{offset}#{req}")
        )

    buttons = [btn[i:i+2] for i in range(0, len(btn), 2)]
    buttons.append([InlineKeyboardButton("⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    
    await query.message.edit_text("<b>📂 Select Season To Filter:</b>", reply_markup=InlineKeyboardMarkup(buttons))
	
@Client.on_callback_query(filters.regex(r"^season_search#"))
async def season_search(client: Client, query: CallbackQuery):
    _, s_num, key, offset, orginal_offset, req = query.data.split("#")
    
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)	
        
    s_num = int(s_num)
    seas = f"S{str(s_num).zfill(2)}"
    offset = int(offset)
    
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True) 
        
    search = search.replace("_", " ")
    
    sorted_dicts = await get_cached_sorted_dicts(search)
    
    if key not in ACTIVE_FILTERS: ACTIVE_FILTERS[key] = {}
    ACTIVE_FILTERS[key]['season'] = s_num
    filtered_dicts = get_filtered_dicts(key, sorted_dicts)
    
    total = len(filtered_dicts)
    if total == 0:
        return await query.answer(f"sᴏʀʀʏ {seas} ɴᴏᴛ ғᴏᴜɴᴅ ғᴏʀ {search}", show_alert=1)
        
    paginated_dicts = filtered_dicts[offset : offset + int(MAX_BTN)]
    files = [item["file"] for item in paginated_dicts]
    
    n_offset = offset + int(MAX_BTN)
    if n_offset >= total:
        n_offset = ""

    batch_ids = files
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = batch_ids
    batch_link = f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}"
    reqnxt = query.from_user.id if query.from_user else 0
    settings = await get_settings(query.message.chat.id)
    temp.CHAT[query.from_user.id] = query.message.chat.id
    ads, ads_name, _ = await mdb.get_advirtisment()
    ads_text = ""
    if ads is not None and ads_name is not None:
        ads_url = f"https://t.me/{temp.U_NAME}?start=ads"
        ads_text = f"<a href={ads_url}>{ads_name}</a>"
    js_ads = f"\n━━━━━━━━━━━━━━━━━━\n <b>{ads_text}</b> \n━━━━━━━━━━━━━━━━━━" if ads_text else ""
  
    # 🔥 SMART BYPASS LOGIC FOR PREMIUM TITLES 🔥
    is_premium = await db.has_premium_access(reqnxt) if reqnxt else False
    for f in files:
        try:
            is_prem_title = await db.get_premium_info(f.file_name)
            if is_prem_title:
                is_premium = True
                break
        except:
            pass

    links = ""
    if settings["link"]:
        btn = []
        search_term = search if 'search' in locals() else BUTTONS.get(key, "")
        sorted_files = get_vip_sorted_files(files, search_term)
        
        for item in sorted_files:
            file = item["file"]
            file_size = get_size_compact(file.file_size)
            quality_str = to_bold(str(item["quality"]).upper())
            audio_str = to_bold(item["audio"])
            
            display_title = f'{item["icon"]} {item["clean_name"]}'
            sub_line = f"↳ [{file_size}] • [{quality_str}] • {audio_str}"
            
            divider = "\n▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n" if item.get("needs_divider") else "\n\n"
            
            if not is_premium and item.get("is_premium") == 1:
                links += f"""{divider}<b><a href="https://t.me/{temp.U_NAME}?start=reqprem">{display_title}</a></b>\n{sub_line}"""
            else:
                links += f"""{divider}<b><a href="https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}">{display_title}</a></b>\n{sub_line}"""
    else:
        btn = []
        search_term = search if 'search' in locals() else BUTTONS.get(key, "")
        sorted_files = get_vip_sorted_files(files, search_term)
        for item in sorted_files:
            file = item["file"]
            file_size = get_size_compact(file.file_size)
            quality_str = to_bold(str(item["quality"]).upper())
            audio_str = to_bold(item["audio"])
            display_text = f'[{file_size}] {item["icon"]} {item["clean_name"]} {quality_str} {audio_str}'
            
            if not is_premium and item.get("is_premium") == 1:
                btn.append([InlineKeyboardButton(text=f"{display_text}", callback_data="reqprem")])
            else:
                btn.append([InlineKeyboardButton(text=display_text, callback_data=f'cfiles#{reqnxt}#{file.file_id}')])
   
    btn.insert(0,[
	InlineKeyboardButton("📥 𝗦𝗲𝗻𝗱 𝗔𝗹𝗹 𝗙𝗶𝗹𝗲𝘀 📥", callback_data=batch_link),
        ])
    has_series = any(item.get("is_series", 0) == 1 for item in sorted_files)
    btn = inject_filter_buttons(btn, key, offset, req, has_series)    
    
    if offset == 0 and n_offset == "":
        pass 
    elif n_offset == "":
        btn.append(
            [InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"season_search#{s_num}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages")])
    elif offset == 0:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}",callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"season_search#{s_num}#{key}#{n_offset}#{orginal_offset}#{req}")])
    else:
        btn.append(
            [InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"season_search#{s_num}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"season_search#{s_num}#{key}#{n_offset}#{orginal_offset}#{req}")])

    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{orginal_offset}")])
    await query.message.edit_text(cap + links + js_ads, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
    return

@Client.on_callback_query(filters.regex(r"^tmdb_search#"))
async def tmdb_search_callback(client, query):
    # Callback limit (64-byte) se bachne ke liye data split
    _, search_query = query.data.split("#", 1)
    
    await query.answer("Fetching from TMDB Database...", show_alert=False)
    
    try:
        movies = await get_poster(search_query, bulk=True)
    except Exception as e:
        print(f"TMDB Callback Error: {e}")
        movies = None
        
    # 🛠️ POSTER BUG FIX: Agar pic (media) hai, toh edit_text caption badal dega. 
    # Isliye purana photo delete karke naya saaf text message bhejenge.
    try:
        await query.message.delete()
    except:
        pass
        
    if not movies:
        google_query = search_query.replace(" ", "+")
        
        tmdb_fail_text = (
            f"❌ **NO RESULTS ON TMDB**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔍 **Query:** `{search_query.title()}`\n\n"
            f"TMDB database mein is naam se koi official title nahi mila. Niche button par click karke exact spelling Google se verify karein."
        )
        
        fail_buttons = [
            [InlineKeyboardButton("🔍 Check Spelling on Google", url=f"https://www.google.com/search?q={google_query}")],
            [InlineKeyboardButton("❌ Close", callback_data='close_data')]
        ]
        
        k = await client.send_message(
            chat_id=query.message.chat.id,
            text=tmdb_fail_text,
            reply_markup=InlineKeyboardMarkup(fail_buttons),
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return
        
    buttons = []
    user = query.from_user.id
    
    # 💥 THE FIX: Limit increased to 8
    for movie in movies[:8]:
        title = movie.get('title', 'Unknown')
        year = movie.get('year')
        year_str = str(year) if year else "N/A" 
        m_type = movie.get('media_type', 'movie')
        m_char = "t" if m_type == "tv" else "m"
        
        buttons.append([
            InlineKeyboardButton(text=f"🌐 {title} ({year_str})", callback_data=f"spol#{movie.get('id')}#{m_char}#{user}")
        ])
        
    buttons.append([InlineKeyboardButton("❌ Close", callback_data='close_data')])
    
    # 🛠️ PREMIUM HTML UI TEXT
    tmdb_success_text = (
        f"<b>✦ ᴛᴍᴅʙ sᴇᴀʀᴄʜ ʀᴇsᴜʟᴛs ✦</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔍 <b>Query:</b> <code>{search_query.title()}</code>\n\n"
        f"👇 <b>Niche list se apna exact title select karein:</b>"
    )
    
    k = await client.send_message(
        chat_id=query.message.chat.id,
        text=tmdb_success_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.HTML
    )
    TMDB_MAP[k.id] = search_query

@Client.on_callback_query(filters.regex(r"^years#"))
async def years_cb_handler(client: Client, query: CallbackQuery):
    _, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
        
    search = BUTTONS.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        
    sorted_dicts = await get_cached_sorted_dicts(search)
    filtered_dicts = get_filtered_dicts(key, sorted_dicts, ignore_key='year')
    
    found_years = set()
    for item in filtered_dicts:
        if item["year"] != 0:
            found_years.add(item["year"])
            
    sorted_years = sorted(list(found_years), reverse=True)

    btn = []
    for y in sorted_years:
        btn.append(
            InlineKeyboardButton(str(y), callback_data=f"years_search#{y}#{key}#0#{offset}#{req}")
        )

    buttons = [btn[i:i+3] for i in range(0, len(btn), 3)]
    buttons.append([InlineKeyboardButton("⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    
    await query.message.edit_text("<b>📂 Select Year To Filter:</b>", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^years_search#"))
async def year_search(client: Client, query: CallbackQuery):
    _, year_val, key, offset, orginal_offset, req = query.data.split("#")
    
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)	
        
    year_val = int(year_val)
    offset = int(offset)
    
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True) 
        
    search = search.replace("_", " ")
    
    sorted_dicts = await get_cached_sorted_dicts(search)
    
    if key not in ACTIVE_FILTERS: ACTIVE_FILTERS[key] = {}
    ACTIVE_FILTERS[key]['year'] = year_val
    filtered_dicts = get_filtered_dicts(key, sorted_dicts)
    
    total = len(filtered_dicts)
    if total == 0:
        return await query.answer(f"sᴏʀʀʏ {year_val} ɴᴏᴛ ғᴏᴜɴᴅ ғᴏʀ {search}", show_alert=1)
        
    paginated_dicts = filtered_dicts[offset : offset + int(MAX_BTN)]
    files = [item["file"] for item in paginated_dicts]
    
    n_offset = offset + int(MAX_BTN)
    if n_offset >= total:
        n_offset = ""

    batch_ids = files
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = batch_ids
    batch_link = f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}"

    reqnxt = query.from_user.id if query.from_user else 0
    settings = await get_settings(query.message.chat.id)
    temp.CHAT[query.from_user.id] = query.message.chat.id
    ads, ads_name, _ = await mdb.get_advirtisment()
    ads_text = ""
    if ads is not None and ads_name is not None:
        ads_url = f"https://t.me/{temp.U_NAME}?start=ads"
        ads_text = f"<a href={ads_url}>{ads_name}</a>"
    js_ads = f"\n━━━━━━━━━━━━━━━━━━\n <b>{ads_text}</b> \n━━━━━━━━━━━━━━━━━━" if ads_text else ""
    
    # 🔥 SMART BYPASS LOGIC FOR PREMIUM TITLES 🔥
    is_premium = await db.has_premium_access(reqnxt) if reqnxt else False
    for f in files:
        try:
            is_prem_title = await db.get_premium_info(f.file_name)
            if is_prem_title:
                is_premium = True
                break
        except:
            pass

    links = ""
    if settings["link"]:
        btn = []
        search_term = search if 'search' in locals() else BUTTONS.get(key, "")
        sorted_files = get_vip_sorted_files(files, search_term)
        
        for item in sorted_files:
            file = item["file"]
            file_size = get_size_compact(file.file_size)
            quality_str = to_bold(str(item["quality"]).upper())
            audio_str = to_bold(item["audio"])
            
            display_title = f'{item["icon"]} {item["clean_name"]}'
            sub_line = f"↳ <b>[{file_size}] • [{quality_str}] • {audio_str}</b>"
            
            divider = "\n▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n" if item.get("needs_divider") else "\n\n"
            
            if not is_premium and item.get("is_premium") == 1:
                links += f"""{divider}<b><a href="https://t.me/{temp.U_NAME}?start=reqprem">{display_title}</a></b>\n{sub_line}"""
            else:
                links += f"""{divider}<b><a href="https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}">{display_title}</a></b>\n{sub_line}"""
    else:
        btn = []
        search_term = search if 'search' in locals() else BUTTONS.get(key, "")
        sorted_files = get_vip_sorted_files(files, search_term)
        for item in sorted_files:
            file = item["file"]
            file_size = get_size_compact(file.file_size)
            quality_str = to_bold(str(item["quality"]).upper())
            audio_str = to_bold(item["audio"])
            display_text = f'[{file_size}] {item["icon"]} {item["clean_name"]} [{quality_str}] {audio_str}'
            
            if not is_premium and item.get("is_premium") == 1:
                btn.append([InlineKeyboardButton(text=f"{display_text}", callback_data="reqprem")])
            else:
                btn.append([InlineKeyboardButton(text=display_text, callback_data=f'cfiles#{reqnxt}#{file.file_id}')])
        
   
    btn.insert(0,[
	InlineKeyboardButton("📥 𝗦𝗲𝗻𝗱 𝗔𝗹𝗹 𝗙𝗶𝗹𝗲𝘀 📥", callback_data=batch_link),
        ])
    has_series = any(item.get("is_series", 0) == 1 for item in sorted_files)
    btn = inject_filter_buttons(btn, key, offset, req, has_series)    
    
    if offset == 0 and n_offset == "":
        pass 
    elif n_offset == "":
        btn.append(
            [InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"years_search#{year_val}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages")])
    elif offset == 0:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}",callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"years_search#{year_val}#{key}#{n_offset}#{orginal_offset}#{req}")])
    else:
        btn.append(
            [InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"years_search#{year_val}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"years_search#{year_val}#{key}#{n_offset}#{orginal_offset}#{req}")])

    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{orginal_offset}")])
    await query.message.edit_text(cap + links + js_ads, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
    return

@Client.on_callback_query(filters.regex(r"^clear_filters#"))
async def clear_filters_handler(client, query):
    _, key, req, offset = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
        
    # Memory se saare filter uda do
    if key in ACTIVE_FILTERS:
        ACTIVE_FILTERS[key] = {}
        
    await query.answer("🗑 All filters cleared!", show_alert=False)
    
    # Wapas base search wale function me bhej do (Taaki refresh ho jaye)
    query.data = f"next_{req}_{key}_{offset}"
    await next_page(client, query)

@Client.on_callback_query(filters.regex(r"^ghost_req#"))
async def ghost_request_handler(bot, query):
    data = query.data.split('#')
    if len(data) == 3:
        _, tmdb_id, m_char = data
    else:
        _, tmdb_id = data
        m_char = "m"
        
    m_type = "tv" if m_char == "t" else "movie"
    user_id = query.from_user.id
    
    try:
        REQ_CHNL = int(REQUEST_CHANNEL)
    except Exception:
        return await query.answer("info.py me REQUEST_CHANNEL ki ID galat hai.", show_alert=True)

    # 🔥 1. UI-LEVEL SPAM BLOCKER: Turant button gayab kar do taaki dobara click na ho sake!
    try:
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏳ Processing Request...", callback_data="ignore")]]))
    except:
        pass

    # 🔥 2. DATABASE-LEVEL SPAM BLOCKER: Race condition & Type safe check
    try:
        tmdb_int = int(tmdb_id)
    except:
        tmdb_int = tmdb_id
        
    existing_req = await db.req.find_one({
        "user_id": user_id, 
        "tmdb_id": {"$in": [str(tmdb_id), tmdb_int]}
    })
    
    if existing_req:
        # Agar already request lag chuki hai, toh wapas 'Close' button de do
        try:
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_data")]]))
        except: pass
        return await query.answer("⚠️ SPAM ALERT: Aap pehle hi iski request daal chuke hain! Kripya upload hone ka wait karein.", show_alert=True)
        
    await query.answer("Sending Request...", show_alert=False)
    movie = await get_poster(tmdb_id, id=True, type=m_type)
    
    if not movie:
        try:
            await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_data")]]))
        except: pass
        return await query.answer("Error processing request!", show_alert=True)
        
    movie_name = movie.get('title')
    year = movie.get('year') or "N/A"
    
    admin_text = (
        f"🚨 **NEW UPLOAD REQUEST** 🚨\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎬 **Title:** `{movie_name} ({year})`\n"
        f"📺 **Type:** `{'TV Series' if m_type == 'tv' else 'Movie'}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **User:** {query.from_user.mention}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"🔗 **TMDB ID:** `{tmdb_id}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
    )
    
    # PRO BATCH-PROCESSING ADMIN GRID
    admin_btn = [
        [InlineKeyboardButton("📥 Add to Queue (Leeching)", callback_data=f"req_queued#{user_id}#{tmdb_id}#{m_char}")],
        [InlineKeyboardButton("✅ Uploaded (Direct)", callback_data=f"notify_user#{user_id}#{tmdb_id}#{m_char}"),
         InlineKeyboardButton("⏳ Not Released", callback_data=f"req_notrel#{user_id}#{tmdb_id}")],
        [InlineKeyboardButton("🚫 Not Available", callback_data=f"req_notavail#{user_id}#{tmdb_id}"),
         InlineKeyboardButton("🗑 Silent Delete", callback_data="delete_admin_msg")]
    ]
    
    try:
        # 🔥 3. Save to database explicitly as String BEFORE sending the network request
        await db.save_movie_request(user_id, movie_name, str(tmdb_id))
        
        try:
            await bot.send_photo(
                chat_id=REQ_CHNL,
                photo=movie.get('poster') or "https://i.ibb.co/HpRDS9X5/x.jpg",
                caption=admin_text,
                reply_markup=InlineKeyboardMarkup(admin_btn),
                parse_mode=enums.ParseMode.MARKDOWN
            )
        except Exception as photo_err:
            print(f"Photo Reject: {photo_err}")
            await bot.send_message(
                chat_id=REQ_CHNL,
                text=admin_text,
                reply_markup=InlineKeyboardMarkup(admin_btn),
                parse_mode=enums.ParseMode.MARKDOWN
            )
            
        success_text = (
            f"✅ **REQUEST SUBMITTED!**\n\n"
            f"🎬 `{movie_name}`\n\n"
            f"Aapki request hamari admin team ko bhej di gayi hai. "
            f"Jaise hi yeh file upload hogi, aapko isi bot par ek notification aa jayega. Please wait karein!"
        )
        await query.message.edit_caption(
            caption=success_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_data")]]),
            parse_mode=enums.ParseMode.MARKDOWN
        )
    except Exception as e:
        print(f"Ghost Request Critical Error: {e}")
        await query.answer("Error sending request! Terminal logs check kar.", show_alert=True)
 
@Client.on_callback_query(filters.regex(r"^fuz#"))
async def fuzzy_search_callback(client, query):
    _, search_query = query.data.split("#", 1)
    
    try:
        await query.answer("Fetching Files...", show_alert=False)
    except Exception:
        pass
    
    # SAFE METHOD: Spoll tuple ka use kiya hai taaki read-only crash na ho
    files, offset, total_results = await get_smart_search_results(search_query)
    
    if files:
        spoll_data = (search_query, files, offset, total_results)
        # Ye naya result bhej dega (naya message banke aayega)
        await auto_filter(client, query, spoll=spoll_data)
        # 🔥 UX FIX: Yahan pehle await query.message.delete() tha, jisko hata diya gaya hai.
        # Ab Welcome screen waisi hi bani rahegi!
    else:
        await query.answer("No files found!", show_alert=True)
# 🔄 NAYA FUNCTION: Back To Menu ke liye
@Client.on_callback_query(filters.regex(r"^fuzback#"))
async def fuzback_callback(client, query):
    _, key = query.data.split("#", 1)
    search = BUTTONS.get(key)
    original_search = DISAMBIGUATION_MAP.get(search)
    
    if not original_search:
        return await query.answer("Session expired! Please search manually again.", show_alert=True)
        
    await query.answer("Returning to Menu...", show_alert=False)
    try:
        await query.message.delete()
    except:
        pass
        
    # User ka original message uthao aur purana search daal kar dubara auto_filter chala do
    user_msg = query.message.reply_to_message if query.message.reply_to_message else query.message
    user_msg.text = original_search
    await auto_filter(client, user_msg)

@Client.on_callback_query(filters.regex(r"^qualities#"))
async def quality_cb_handler(client: Client, query: CallbackQuery):
    _, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
        
    search = BUTTONS.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        
    sorted_dicts = await get_cached_sorted_dicts(search)
    filtered_dicts = get_filtered_dicts(key, sorted_dicts, ignore_key='quality')
    
    found_qualities = set()
    for item in filtered_dicts:
        base_q = str(item.get("quality", "720P")).upper()
        file_name = str(getattr(item["file"], "file_name", "")).upper()
        
        final_q = base_q
        if "HEVC" in file_name or "X265" in file_name:
            if "HEVC" not in final_q: final_q += " HEVC"
        if "10BIT" in file_name or "10-BIT" in file_name or "10 BIT" in file_name:
            if "10BIT" not in final_q: final_q += " 10BIT"
            
        found_qualities.add(final_q)
            
    def qual_sort_key(q):
        if "4K" in q or "2160P" in q: return 4
        if "1080P" in q: return 3
        if "720P" in q: return 2
        if "480P" in q: return 1
        return 0
        
    sorted_qualities = sorted(list(found_qualities), key=qual_sort_key, reverse=True)

    btn = []
    for q in sorted_qualities:
        display_text = to_bold(q)
        # MASTER FIX: "quality_search#" ko compress karke "qa#" kar diya (To bypass 64-byte limit)
        btn.append(
            InlineKeyboardButton(display_text, callback_data=f"qa#{q}#{key}#0#{offset}#{req}")
        )

    buttons = [btn[i:i+2] for i in range(0, len(btn), 2)]
    buttons.append([InlineKeyboardButton("⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    
    await query.message.edit_text("<b>📂 Select Quality To Filter:</b>", reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex(r"^qa#"))
async def quality_search(client: Client, query: CallbackQuery):
    _, qul, key, offset, orginal_offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)	
        
    offset = int(offset)
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True) 
        
    search = search.replace("_", " ")
    
    sorted_dicts = await get_cached_sorted_dicts(search)
    
    if key not in ACTIVE_FILTERS: ACTIVE_FILTERS[key] = {}
    ACTIVE_FILTERS[key]['quality'] = qul
    filtered_dicts = get_filtered_dicts(key, sorted_dicts)
    
    total = len(filtered_dicts)
    if total == 0:
        return await query.answer(f"sᴏʀʀʏ {qul} ɴᴏᴛ ғᴏᴜɴᴅ ꜰᴏʀ {search}", show_alert=1)
        
    paginated_dicts = filtered_dicts[offset : offset + int(MAX_BTN)]
    files = [item["file"] for item in paginated_dicts]
    
    n_offset = offset + int(MAX_BTN)
    if n_offset >= total:
        n_offset = ""
        
    batch_ids = files
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = batch_ids
    batch_link = f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}"

    reqnxt = query.from_user.id if query.from_user else 0
    settings = await get_settings(query.message.chat.id)
    temp.CHAT[query.from_user.id] = query.message.chat.id
    ads, ads_name, _ = await mdb.get_advirtisment()
    ads_text = ""
    if ads is not None and ads_name is not None:
        ads_url = f"https://t.me/{temp.U_NAME}?start=ads"
        ads_text = f"<a href={ads_url}>{ads_name}</a>"
    js_ads = f"\n━━━━━━━━━━━━━━━━━━\n <b>{ads_text}</b> \n━━━━━━━━━━━━━━━━━━" if ads_text else ""
    
    # 🔥 SMART BYPASS LOGIC FOR PREMIUM TITLES 🔥
    is_premium = await db.has_premium_access(reqnxt) if reqnxt else False
    for f in files:
        try:
            is_prem_title = await db.get_premium_info(f.file_name)
            if is_prem_title:
                is_premium = True
                break
        except:
            pass

    links = ""
    if settings["link"]:
        btn = []
        search_term = search if 'search' in locals() else BUTTONS.get(key, "")
        sorted_files = get_vip_sorted_files(files, search_term)
        
        for item in sorted_files:
            file = item["file"]
            file_size = get_size_compact(file.file_size)
            quality_str = to_bold(str(item["quality"]).upper())
            audio_str = to_bold(item["audio"])
            
            display_title = f'{item["icon"]} {item["clean_name"]}'
            sub_line = f"↳ <b>[{file_size}] • [{quality_str}] • {audio_str}</b>"
            
            divider = "\n▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n" if item.get("needs_divider") else "\n\n"
            
            if not is_premium and item.get("is_premium") == 1:
                links += f"""{divider}<b><a href="https://t.me/{temp.U_NAME}?start=reqprem">{display_title}</a></b>\n{sub_line}"""
            else:
                links += f"""{divider}<b><a href="https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}">{display_title}</a></b>\n{sub_line}"""
    else:
        btn = []
        search_term = search if 'search' in locals() else BUTTONS.get(key, "")
        sorted_files = get_vip_sorted_files(files, search_term)
        for item in sorted_files:
            file = item["file"]
            file_size = get_size_compact(file.file_size)
            quality_str = to_bold(str(item["quality"]).upper())
            audio_str = to_bold(item["audio"])
            display_text = f'[{file_size}] {item["icon"]} {item["clean_name"]} [{quality_str}] {audio_str}'
            
            if not is_premium and item.get("is_premium") == 1:
                btn.append([InlineKeyboardButton(text=f"{display_text}", callback_data="reqprem")])
            else:
                btn.append([InlineKeyboardButton(text=display_text, callback_data=f'cfiles#{reqnxt}#{file.file_id}')])
        
    btn.insert(0,[
    InlineKeyboardButton("📥 𝗦𝗲𝗻𝗱 𝗔𝗹𝗹 𝗙𝗶𝗹𝗲𝘀 📥", callback_data=batch_link),
        ])
    has_series = any(item.get("is_series", 0) == 1 for item in sorted_files)
    btn = inject_filter_buttons(btn, key, offset, req, has_series)    
    
    if offset == 0 and n_offset == "":
        pass 
    elif n_offset == "":
        btn.append(
            [InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"qa#{qul}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages")])
    elif offset == 0:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}",callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"qa#{qul}#{key}#{n_offset}#{orginal_offset}#{req}")])
    else:
        btn.append(
            [InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"qa#{qul}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"qa#{qul}#{key}#{n_offset}#{orginal_offset}#{req}")])

    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{orginal_offset}")])
    await query.message.edit_text(cap + links + js_ads, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
    return

@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):
    _, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
        
    search = BUTTONS.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        
    sorted_dicts = await get_cached_sorted_dicts(search)
    filtered_dicts = get_filtered_dicts(key, sorted_dicts, ignore_key='language')
    
    found_audios = set()
    for item in filtered_dicts:
        if item["audio"]:
            clean_audio = item["audio"].replace("[", "").replace("]", "")
            found_audios.add(clean_audio)
            
    sorted_audios = sorted(list(found_audios))

    btn = []
    for a in sorted_audios:
        btn.append(
            InlineKeyboardButton(a, callback_data=f"lang_search#{a}#{key}#0#{offset}#{req}")
        )

    buttons = [btn[i:i+2] for i in range(0, len(btn), 2)]
    buttons.append([InlineKeyboardButton("⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{offset}")])
    
    await query.message.edit_text("<b>📂 Select Language To Filter:</b>", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r"^lang_search#"))
async def lang_search(client: Client, query: CallbackQuery):
    _, lang, key, offset, orginal_offset, req = query.data.split("#")
    
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)	
        
    offset = int(offset)
    search = BUTTONS.get(key)
    cap = CAP.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True) 
        
    search = search.replace("_", " ")
    
    sorted_dicts = await get_cached_sorted_dicts(search)
    
    if key not in ACTIVE_FILTERS: ACTIVE_FILTERS[key] = {}
    ACTIVE_FILTERS[key]['language'] = lang
    filtered_dicts = get_filtered_dicts(key, sorted_dicts)
            
    total = len(filtered_dicts)
    if total == 0:
        return await query.answer(f"sᴏʀʀʏ {lang} ɴᴏᴛ ғᴏᴜɴᴅ ꜰᴏʀ {search}", show_alert=1)
        
    paginated_dicts = filtered_dicts[offset : offset + int(MAX_BTN)]
    files = [item["file"] for item in paginated_dicts]
    
    n_offset = offset + int(MAX_BTN)
    if n_offset >= total:
        n_offset = ""

    batch_ids = files
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = batch_ids
    batch_link = f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}"

    reqnxt = query.from_user.id if query.from_user else 0
    settings = await get_settings(query.message.chat.id)
    group_id = query.message.chat.id
    temp.CHAT[query.from_user.id] = query.message.chat.id
    ads, ads_name, _ = await mdb.get_advirtisment()
    ads_text = ""
    if ads is not None and ads_name is not None:
        ads_url = f"https://t.me/{temp.U_NAME}?start=ads"
        ads_text = f"<a href={ads_url}>{ads_name}</a>"

    js_ads = f"\n━━━━━━━━━━━━━━━━━━\n <b>{ads_text}</b> \n━━━━━━━━━━━━━━━━━━" if ads_text else ""
    
    # 🔥 SMART BYPASS LOGIC FOR PREMIUM TITLES 🔥
    is_premium = await db.has_premium_access(reqnxt) if reqnxt else False
    for f in files:
        try:
            is_prem_title = await db.get_premium_info(f.file_name)
            if is_prem_title:
                is_premium = True
                break
        except:
            pass

    links = ""
    if settings["link"]:
        btn = []
        search_term = search if 'search' in locals() else BUTTONS.get(key, "")
        sorted_files = get_vip_sorted_files(files, search_term)
        
        for item in sorted_files:
            file = item["file"]
            file_size = get_size_compact(file.file_size)
            quality_str = to_bold(str(item["quality"]).upper())
            audio_str = to_bold(item["audio"])
            
            display_title = f'{item["icon"]} {item["clean_name"]}'
            sub_line = f"↳ <b>[{file_size}] • [{quality_str}] • {audio_str}</b>"
            
            divider = "\n▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n" if item.get("needs_divider") else "\n\n"
            
            if not is_premium and item.get("is_premium") == 1:
                links += f"""{divider}<b><a href="https://t.me/{temp.U_NAME}?start=reqprem">{display_title}</a></b>\n{sub_line}"""
            else:
                links += f"""{divider}<b><a href="https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file.file_id}">{display_title}</a></b>\n{sub_line}"""
    else:
        btn = []
        search_term = search if 'search' in locals() else BUTTONS.get(key, "")
        sorted_files = get_vip_sorted_files(files, search_term)
        for item in sorted_files:
            file = item["file"]
            file_size = get_size_compact(file.file_size)
            quality_str = to_bold(str(item["quality"]).upper())
            audio_str = to_bold(item["audio"])
            display_text = f'[{file_size}] {item["icon"]} {item["clean_name"]} [{quality_str}] {audio_str}'
            
            if not is_premium and item.get("is_premium") == 1:
                btn.append([InlineKeyboardButton(text=f"{display_text}", callback_data="reqprem")])
            else:
                btn.append([InlineKeyboardButton(text=display_text, callback_data=f'cfiles#{reqnxt}#{file.file_id}')])
        

    btn.insert(0,[
	InlineKeyboardButton("📥 𝗦𝗲𝗻𝗱 𝗔𝗹𝗹 𝗙𝗶𝗹𝗲𝘀 📥", callback_data=batch_link),
        ])
    has_series = any(item.get("is_series", 0) == 1 for item in sorted_files)
    btn = inject_filter_buttons(btn, key, offset, req, has_series)    
    if offset == 0 and n_offset == "":
        pass 
    elif n_offset == "":
        btn.append(
            [InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"lang_search#{lang}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages")])
    elif offset == 0:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}",callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"lang_search#{lang}#{key}#{n_offset}#{orginal_offset}#{req}")])
    else:
        btn.append(
            [InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"lang_search#{lang}#{key}#{offset- int(MAX_BTN)}#{orginal_offset}#{req}"),
             InlineKeyboardButton(f"{math.ceil(offset / int(MAX_BTN)) + 1}/{math.ceil(total / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"lang_search#{lang}#{key}#{n_offset}#{orginal_offset}#{req}")])

    btn.append([InlineKeyboardButton(text="⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{orginal_offset}")])
    await query.message.edit_text(cap + links + js_ads, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
    return
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))

from pyrogram.types import InputMediaPhoto

@Client.on_callback_query(filters.regex(r"^spol#"))
async def advantage_spoll_choker(bot, query):
    data = query.data.split('#')
    if len(data) == 4:
        _, tmdb_id, m_char, user = data
    else:
        _, tmdb_id, user = data
        m_char = "m"
        
    m_type = "tv" if m_char == "t" else "movie"
    
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT, show_alert=True)
        
    await query.answer("Fetching Data...", show_alert=False)
    movie = await get_poster(tmdb_id, id=True, type=m_type)
    
    if not movie:
        return await query.answer("Error fetching movie details!", show_alert=True)
        
    title = movie.get('title')
    movie_year = movie.get('year')
    # Year ko title ke saath jodo taaki exact search ho (e.g., "Sinister 2012")
    search = f"{title} {str(movie_year)[:4]}" if movie_year else title
    search = search.strip()
    
    files, offset, total_results = await get_smart_search_results(search)
    
    if files:
        spoll_data = (search, files, offset, total_results)
        await auto_filter(bot, query, spoll=spoll_data)
        try:
            await query.message.delete()
        except:
            pass
    else:
        genres = movie.get('genres', 'N/A')
        if isinstance(genres, list):
            genres = ", ".join(genres)
        rating = movie.get('rating') or "N/A"
        year = movie.get('year') or "N/A"
        
        ghost_text = (
            f"🎬 **{movie.get('title')}** ({year})\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🌟 **Rating:** {rating} / 10\n"
            f"🎭 **Genres:** {genres}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ **STATUS: NOT AVAILABLE**\n\n"
            f"👉 Yeh file abhi hamare server par nahi hai. Niche 'Request Upload' par click karein aur hamari team ise jald hi add kar degi."
        )
        
        # 🔙 THE TMDB BACK BUTTON LOGIC (100% Working RAM Map Method)
        original_search = TMDB_MAP.get(query.message.id, "")
            
        # Ab ye deep-link user ko direct Bot ke inbox me bhejega
        btn = [[
            InlineKeyboardButton("📤 REQUEST UPLOAD", url=f"https://telegram.me/{temp.U_NAME}?start=ghostreq_{tmdb_id}_{m_char}")
        ]]
        
        # Agar original search mil gaya, toh TMDB Menu par wapas jane ka button add kar do
        if original_search:
            btn.append([InlineKeyboardButton("🔙 Back to TMDB List", callback_data=f"tmdb_search#{original_search[:45]}")])
            
        btn.append([
            InlineKeyboardButton("❌ Close", callback_data="close_data")
        ])
        
        try:
            await query.message.delete()
        except:
            pass
            
        poster_url = movie.get('poster') or "https://i.ibb.co/HpRDS9X5/x.jpg"
        # 🔥 FIX: Capture the sent message into a variable
        ghost_msg = await bot.send_photo(
            chat_id=query.message.chat.id,
            photo=poster_url,
            caption=ghost_text,
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.MARKDOWN
        )
        
        await asyncio.sleep(90)
        try:
            await ghost_msg.delete()
        except:
            pass

# 🔄 NAYA FUNCTION: Did You Mean (Spell) Redirect ke liye
@Client.on_callback_query(filters.regex(r"^spell#"))
async def spell_checker_callback(client, query):
    _, search_query = query.data.split("#", 1)
    
    await query.answer("Correcting spelling and searching...", show_alert=False)
    try:
        await query.message.delete()
    except:
        pass
        
    # 💥 THE MAGIC: Fake a new user message to force the Disambiguation Menu
    user_msg = query.message.reply_to_message if query.message.reply_to_message else query.message
    user_msg.text = search_query
    
    # Bina spoll ke auto_filter call karenge taaki exact/multiple match check ho
    await auto_filter(client, user_msg)

# 🔄 NAYA FUNCTION: Pagination ke liye
@Client.on_callback_query(filters.regex(r"^fuzpage#"))
async def fuzpage_callback(client, query):
    _, search_base, page = query.data.split("#")
    page = int(page)
    
    # 💥 THE BUG FIX: Seedha explicit key se uthao, loop mat lagao
    search = DISAMBIGUATION_MAP.get(search_base)
            
    if not search:
        return await query.answer("Session expired! Please search manually again.", show_alert=True)
            
    await query.answer("Turning Page...", show_alert=False)
    
    # Data wapas re-fetch karo (Logic wahi purana)
    sorted_all_files = await get_cached_sorted_dicts(search)
    
    unique_titles = {}
    highest_match_score = 0
    
    for item in sorted_all_files:
        if item['match_score'] > highest_match_score:
            highest_match_score = item['match_score']
        
        name_title = item['name_for_sort'].title()
        year_val = item['year']
        is_series = item['is_series']
        
        max_disp_len = 32
        if len(name_title) > max_disp_len:
            short_title = name_title[:max_disp_len].strip() + ".."
        else:
            short_title = name_title
        
        if is_series == 1:
            key_id = f"{item['name_for_sort']}_series"
            disp = f"📺 {short_title} (Series)"
            payload_search = item['name_for_sort'][:45].strip()
        else:
            year_str = str(year_val) if year_val else ""
            key_id = f"{item['name_for_sort']}_{year_str}"
            disp = f"🎬 {short_title} ({year_str})" if year_str else f"🎬 {short_title}"
            
            base_name = item['name_for_sort']
            if year_str:
                max_name_len = 45 - len(year_str) - 1 
                if len(base_name) > max_name_len:
                    base_name = base_name[:max_name_len].strip()
                payload_search = f"{base_name} {year_str}"
            else:
                payload_search = base_name[:45].strip()
            
        if key_id not in unique_titles:
            unique_titles[key_id] = (disp, payload_search)

    force_menu = (highest_match_score == 1)
    all_items = list(unique_titles.items())
    
    items_per_page = 8
    total_pages = math.ceil(len(all_items) / items_per_page)
    start = page * items_per_page
    end = start + items_per_page
    paginated_items = all_items[start:end]
    
    DISAMBIGUATION_MAP[search_base] = search # Memory ko refresh karo taaki aage bhi kaam kare

    buttons = []
    for key_id, (disp, payload_search) in paginated_items:
        DISAMBIGUATION_MAP[payload_search] = search
        buttons.append([InlineKeyboardButton(disp, callback_data=f"fuz#{payload_search}")])
    
    # 💥 SMART NAVIGATION ROW 💥
    if total_pages > 1:
        nav_row = []
        if page > 0: 
            nav_row.append(InlineKeyboardButton("⪻ Back", callback_data=f"fuzpage#{search_base}#{page-1}"))
        
        nav_row.append(InlineKeyboardButton(f"📄 {page+1} / {total_pages}", callback_data="pages"))
        
        if page + 1 < total_pages: 
            nav_row.append(InlineKeyboardButton("Next ⪼", callback_data=f"fuzpage#{search_base}#{page+1}"))
            
        buttons.append(nav_row)
    
    if force_menu:
        buttons.append([InlineKeyboardButton("🌐 Search in TMDB", callback_data=f"tmdb_search#{search[:45]}")])
    
    buttons.append([InlineKeyboardButton("❌ Close", callback_data='close_data')])
    
    if force_menu:
        disambiguation_text = (
            f"<b>⚠️ EXACT MATCH NOT FOUND</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔍 <b>Query:</b> <code>{search.title()}</code>\n\n"
            f"I found <b>{len(all_items)}</b> partial matches for your search.\n\n"
            f"👇 <b>Action:</b> Pick your exact title or search in TMDB:"
        )
    else:
        disambiguation_text = (
            f"<b>⚠️ MULTIPLE MATCHES FOUND</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔍 <b>Query:</b> <code>{search.title()}</code>\n\n"
            f"I found <b>{len(all_items)}</b> files related to your search.\n\n"
            f"👇 <b>Action:</b> Pick your exact title:"
        )
    
    try:
        await query.message.edit_text(
            text=disambiguation_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML
        )
    except pyrogram.errors.exceptions.bad_request_400.MessageNotModified:
        pass

@Client.on_callback_query(filters.regex(r"^cfiles"))
async def pmfile_cb(client, query):
    try:
        _, userid, fileid = query.data.split("#")
        
        if int(userid) != 0 and query.from_user.id != int(userid):
            await query.answer("⚠️ Request Your Own!!", show_alert=True)
            return

        bot_uname = temp.U_NAME if temp.U_NAME else "movie_storage2_0_bot"
        file_link = f"https://telegram.me/{bot_uname}?start=file_{query.message.chat.id}_{fileid}"
        
        btn = [[InlineKeyboardButton("📥 ɢᴇᴛ ꜰɪʟᴇ ɴᴏᴡ 📥", url=file_link)]]
        await query.message.reply_text(
            f"<b>Hey {query.from_user.mention}, aapki file link ready hai! Niche click karein 👇</b>", 
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer()
        
    except Exception as e:
        print(f"CFILES ERROR: {e}")
        await query.answer("⚠️ Server Error: Bot failed to generate link.", show_alert=True)

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        try:
            user = query.message.reply_to_message.from_user.id
        except:
            user = query.from_user.id
        if int(user) != 0 and query.from_user.id != int(user):
            return await query.answer(script.ALRT_TXT, show_alert=True)
        await query.answer("Closed ")
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass
            
    elif query.data == "reqprem":
        btn = [
            [InlineKeyboardButton("💎 Gᴇᴛ Pʀᴇᴍɪᴜᴍ Nᴏᴡ 💎", callback_data="seeplans")],
            [InlineKeyboardButton("🚫 Cʟᴏsᴇ 🚫", callback_data="close_data")]
        ]
        
        caption = f"""
<b>Free users ke liye sirf 480p • 720p Quality ka access hai.</b>
<b>So ye 1080p ki file sirf Premium Members ke liye available hai 🔐</b>

📂 𝐏𝐫𝐞𝐦𝐢𝐮𝐦 𝐀𝐜𝐜𝐞𝐬𝐬 𝐊𝐞 𝐒𝐚𝐚𝐭𝐡 𝐌𝐢𝐥𝐞𝐠𝐚:
⚡ <i>Ultra Fast Direct Download Links</i>
🎬 <i>480p • 720p • 1080p • 4K Quality</i>
🔊 <i>Better Audio & Clean Prints</i>
🔥 <i>Early Access To Latest Uploads</i>

Agar baar baar low quality prints se pareshaan ho, toh Premium main upgrade karna better option hai 💎

<b>1000+ users already Premium use kar rahe hain for smooth & instant access 🚀</b>

👇 <i>Ek baar Premium access try karke dekho… difference khud feel ho jayega 👀</i>"""

        await query.answer("👑 Premium Required for Heavy Files!", show_alert=True)
        
        await client.send_photo(
            chat_id=query.message.chat.id,
            photo="https://i.ibb.co/QFwnjH5q/x.jpg",
            caption=caption,
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )
        return
            
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type
        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()
        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)    

    elif query.data.startswith("checksub"):
        ident, file_id , grp_id = query.data.split("#")
        if grp_id != 'None' or grp_id != '':
            chat_id = grp_id
        else:
            chat_id = query.message.chat.id
        if AUTH_CHANNEL and not await is_req_subscribed(client, query):
            await query.answer("Nice try! 😉 Lekin file tabhi milegi jab aap sach mein channel join karoge.\n\nJaldi join karo aur wapas aao!", show_alert=True)
            return         
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('ɴᴏ sᴜᴄʜ ꜰɪʟᴇ ᴇxɪsᴛs 🚫')
        files = files_[0]
        btn = [[
            InlineKeyboardButton('🎗️ ɢᴇᴛ ʏᴏᴜʀ ғɪʟᴇ 🎗️', url=f'https://t.me/{temp.U_NAME}?start=file_{chat_id}_{file_id}')
        ]]
        reply_markup = InlineKeyboardMarkup(btn)
        
        success_text = (
            f"🎉 <b>Thanks for joining our channel!</b>\n\n"
            f"📁 <b>File Name:</b> <code>{files.file_name[:20]}...</code>\n\n"
            f"👇 <i>Niche diye gaye button par click karke apni file access karein.</i>\n\n"
            f"🛡️ <b>Maintained by:</b> @moviestorage_official"
        )
        return await query.message.edit(text=success_text, reply_markup=reply_markup)
		
    elif query.data == "give_trial":
        user_id = query.from_user.id
        has_free_trial = await db.check_trial_status(user_id)
        if has_free_trial:
            await query.answer(" ʏᴏᴜ'ᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ ʏᴏᴜʀ ꜰʀᴇᴇ ᴛʀɪᴀʟ ᴏɴᴄᴇ !\n\n📌 ᴄʜᴇᴄᴋᴏᴜᴛ ᴏᴜʀ ᴘʟᴀɴꜱ ʙʏ : /plan", show_alert=True)
            return
        else:            
            await db.give_free_trial(user_id)
            
            trial_text = (
                "🎉 <b>Congratulations!</b> 🎉\n\n"
                "Aapka <b>5-Minute Free Premium Trial</b> abhi se start ho chuka hai! ⏱️\n\n"
                "Ab agle 5 minute tak aap bina kisi rukawat ke high-quality files download kar sakte hain aur premium ka maza le sakte hain.\n\n"
                "⚠️ <b>TRIAL LIMITATIONS:</b>\n"
                "❌ <i>18+ Content Channel ka access nahi milega.</i>\n"
                "❌ <i>Premium Request Group ka access nahi milega.</i>\n"
                "<i>(Ye dono exclusive features sirf Paid Premium members ke liye hain.)</i>\n\n"
                "⏳ <i>5 minute baad normal restrictions wapas lag jayengi.</i>\n\n"
                "Agar aapko Premium ka smooth experience pasand aaye aur FULL Premium Access chahiye, toh niche button dabakar permanently upgrade kar lein! 💎"
            )
            
            trial_image = "https://i.ibb.co/ksyXBff8/x.jpg" 
            
            btn = [
                [InlineKeyboardButton("💸 ᴄʜᴇᴄᴋᴏᴜᴛ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ 💸", callback_data='seeplans')],
                [InlineKeyboardButton("👤 ᴍʏ ᴀᴄᴄᴏᴜɴᴛ", callback_data='check_myplan')]
            ]
            
            try:
                await query.message.edit_media(
                    media=InputMediaPhoto(media=trial_image, caption=trial_text, parse_mode=enums.ParseMode.HTML),
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            except Exception:
                await client.send_photo(
                    chat_id=query.message.chat.id,
                    photo=trial_image,
                    caption=trial_text,
                    reply_markup=InlineKeyboardMarkup(btn),
                    parse_mode=enums.ParseMode.HTML
                )
                await query.message.delete()

            await client.send_message(LOG_CHANNEL, text=f"#FREE_TRAIL_CLAIMED\n\n👤 ᴜꜱᴇʀ ɴᴀᴍᴇ - {query.from_user.mention}\n⚡ ᴜꜱᴇʀ ɪᴅ - {user_id}", disable_web_page_preview=True)
            return   
	
    elif query.data.startswith("stream"):
        user_id = query.from_user.id
        file_id = query.data.split('#', 1)[1]
        log_msg = await client.send_cached_media(
        chat_id=LOG_CHANNEL,
        file_id=file_id
        )
        fileName = quote_plus(get_name(log_msg))
        online = f"{URL}watch/{log_msg.id}/{fileName}?hash={get_hash(log_msg)}"
        download = f"{URL}{log_msg.id}/{fileName}?hash={get_hash(log_msg)}"
        btn = [[
            InlineKeyboardButton("Movie Storage OfficiaL", url=f'https://t.me/moviestorage_official'),
            InlineKeyboardButton("Movie Storage OfficiaL", url=f'https://t.me/moviestorage_official')
        ],[
            InlineKeyboardButton('❌ ᴄʟᴏsᴇ ❌', callback_data='close_data')
	]]
        await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(btn)
	)
        username = query.from_user.username
        await log_msg.reply_text(
            text=f"#LinkGenrated\n\nIᴅ : <code>{user_id}</code>\nUꜱᴇʀɴᴀᴍᴇ : {username}\n\nNᴀᴍᴇ : {fileName}",
            quote=True,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Movie Storage OfficiaL", url=f'https://t.me/moviestorage_official'),
                    InlineKeyboardButton('Movie Storage OfficiaL', url=f'https://t.me/moviestorage_official')
                ]
            ])
	)
	
    elif query.data == "buttons":
        await query.answer("ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 😊", show_alert=True)

    elif query.data == "pages":
        await query.answer("📌 Current Page")

    elif query.data.startswith("lang_art"):
        _, lang = query.data.split("#")
        await query.answer(f"ʏᴏᴜ sᴇʟᴇᴄᴛᴇᴅ {lang.title()} ʟᴀɴɢᴜᴀɢᴇ ⚡️", show_alert=True)
  
    elif query.data == "start":
        user_id = query.from_user.id
        if await db.has_premium_access(user_id):
            user_status = "👑 Pʀᴇᴍɪᴜᴍ Mᴇᴍʙᴇʀ"
        else:
            user_status = "Fʀᴇᴇ Usᴇʀ"

        import datetime, pytz
        ist = pytz.timezone('Asia/Kolkata')
        hour = datetime.datetime.now(ist).hour
        if 5 <= hour < 12: greeting = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ ☀️"
        elif 12 <= hour < 17: greeting = "ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ 🌤️"
        elif 17 <= hour < 21: greeting = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 🌙"
        else: greeting = "ɢᴏᴏᴅ ɴɪɢʜᴛ 😴"

        buttons = [
                        [InlineKeyboardButton('🎬 Explore Movies & Web Series', callback_data='exp_main')],
                        [InlineKeyboardButton('🔎 Sᴇᴀʀᴄʜ Mᴏᴠɪᴇs', url="https://t.me/+jUo32x8VbPdlNTE1"), InlineKeyboardButton('📖 Search Guide', callback_data='search_guide')],
                        [InlineKeyboardButton('👑 Get Premium', callback_data='seeplans'), InlineKeyboardButton('👤 My Account', callback_data='check_myplan')],
                        [InlineKeyboardButton('🎁 Refer & Earn', callback_data="reffff"), InlineKeyboardButton('⚙️ Bot Settings', callback_data='features')],
                        [InlineKeyboardButton('📢 Updates Channel', url='https://t.me/+1P-7PXGIyDg4MmE1'), InlineKeyboardButton('📢 Backup Channel', url='https://t.me/moviestorage_official')]
                    ] 
        reply_markup = InlineKeyboardMarkup(buttons)
        try:
            await query.message.edit_media(
                media=InputMediaPhoto(media=random.choice(START_IMG), caption=script.START_TXT.format(greeting=greeting, mention=query.from_user.mention, status=user_status), parse_mode=enums.ParseMode.HTML),
                reply_markup=reply_markup
            )
        except Exception:
            await query.message.reply_photo(
                photo=random.choice(START_IMG),
                caption=script.START_TXT.format(greeting=greeting, mention=query.from_user.mention, status=user_status),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
            await query.message.delete()
    
    elif query.data == "free":
        buttons = [[
            InlineKeyboardButton('☆📸 𝙎𝙚𝙣𝙙 𝙨𝙘𝙧𝙚𝙚creenshot 📸☆', url=f'https://t.me/stbhai_admin')
        ],[
            InlineKeyboardButton('💎 𝗖𝘂𝘀𝘁𝗼𝗺 𝗣𝗹𝗮𝗻 💎', callback_data='other')
        ],[
            InlineKeyboardButton('• 𝗕𝗮𝗰𝗸 •', callback_data='broze'),
            InlineKeyboardButton('• 𝗖𝗹𝗼𝘀𝗲 •', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)             
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PAYPICS))
        )
        await query.message.edit_text(
            text=script.FREE_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )   
    
    elif query.data == "broze":
       buttons = [[
            InlineKeyboardButton('🍁 𝗖𝗹𝗶𝗰𝗸 𝗔𝗹𝗹 𝗣𝗹𝗮𝗻𝘀 & 𝗣𝗿𝗶𝗰𝗲𝘀 🍁', callback_data='free')
        ], [
            InlineKeyboardButton('• 𝗖𝗹𝗼𝘀𝗲 •', callback_data='close_data')
       ]]
       reply_markup = InlineKeyboardMarkup(buttons)
  
       await query.message.edit_media(
         media=InputMediaPhoto(
            media=SUBSCRIPTION, 
            caption=script.PREPLANSS_TXT.format(query.from_user.mention()),
            parse_mode=enums.ParseMode.HTML
         ),
         reply_markup=reply_markup
       )
        
    elif query.data == "other":
        buttons = [[
            InlineKeyboardButton('☎️ 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘄𝗻𝗲𝗿 𝗧𝗼 𝗞𝗻𝗼𝘄 𝗠𝗼𝗿𝗲', user_id = ADMINS[0])
        ],[
            InlineKeyboardButton('• 𝗕𝗮𝗰𝗸 •', callback_data='free')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PAYPICS))
        )
        await query.message.edit_text(
            text=script.OTHER_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
	)

    elif query.data == "ref_point":
        await query.answer(f'You Have: {referdb.get_refer_points(query.from_user.id)} Refferal points.', show_alert=True)

    elif query.data == "verifyon":
        await query.answer(f'Only the bot admin can ᴏɴ ✓ or ᴏғғ ✗ this feature.', show_alert=True)
    
    elif query.data == "features":
        buttons = [[
              InlineKeyboardButton('Aᴅᴍɪɴ Cᴏᴍᴍᴀɴᴅs', callback_data='admincmd'),
              InlineKeyboardButton('Iᴍᴀɢᴇ Tᴏ Lɪɴᴋ', callback_data='telegraph'),
              ], [
              InlineKeyboardButton('F-Sᴜʙ', callback_data='fsub'),
              InlineKeyboardButton('Gʀᴏᴜᴘ Sᴇᴛᴜᴘ', callback_data='earn')
              ], [
              InlineKeyboardButton('⋞ Back To Home', callback_data='start')
              ]]
    
        reply_markup = InlineKeyboardMarkup(buttons)
    
        await query.message.edit_media(
            media=InputMediaPhoto(
            media=random.choice(START_IMG),
            caption=script.HELP_TXT,
            parse_mode=enums.ParseMode.HTML 
            ),
            reply_markup=reply_markup
	)
        
    elif query.data == "admincmd":
      if query.from_user.id not in ADMINS:
        return await query.answer('ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ꜰᴏʀ ʏᴏᴜ ʙʀᴏ!', show_alert=True)
    
      buttons = [[
	      InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='features'),
	      InlineKeyboardButton('ɴᴇxᴛ ⪼', callback_data='admincmd2'),
      ]]
      reply_markup = InlineKeyboardMarkup(buttons)
    
      await client.edit_message_media(
          chat_id=query.message.chat.id,
          message_id=query.message.id,
          media=InputMediaAnimation(
            media="https://graph.org/file/e8fca20a60d756a5023cb-61c0d5d0917be87e18.gif",
            caption=script.ADMIN_CMD_TXT,
            parse_mode=enums.ParseMode.HTML
          ),
          reply_markup=reply_markup
          )

    elif query.data == "admincmd2":
       buttons = [[
	      InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='admincmd')]]
       reply_markup = InlineKeyboardMarkup(buttons)
    
       await client.edit_message_media(
          chat_id=query.message.chat.id,
          message_id=query.message.id,
          media=InputMediaAnimation(
            media="https://graph.org/file/e8fca20a60d756a5023cb-61c0d5d0917be87e18.gif",
            caption=script.ADMIN_CMD_TXT2,
            parse_mode=enums.ParseMode.HTML
          ),
          reply_markup=reply_markup
      )
	    
    elif query.data == "fsub":
        buttons = [[
            InlineKeyboardButton('⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs ⇆', url=f'http://t.me/{temp.U_NAME}?startgroup=start')],
            [InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='features')]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.FSUB_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == 'about':
        await query.message.edit_text(
            script.ABOUT_TEXT.format(query.from_user.mention(),temp.B_LINK),
            reply_markup = InlineKeyboardMarkup(
                [[
			InlineKeyboardButton('‼️ ᴅɪꜱᴄʟᴀɪᴍᴇʀ ‼️', callback_data='disclaimer')
		],[
			InlineKeyboardButton('Sᴏᴜʀᴄᴇ ᴄᴏᴅᴇ', callback_data='Source')
                ],[
                        InlineKeyboardButton('My Developers 😎',callback_data='mydevelopers')
		],[
			InlineKeyboardButton('⋞ ʜᴏᴍᴇ', callback_data='start')]]
                ),
            disable_web_page_preview = True
	)
    elif query.data == "mydevelopers":
        await query.answer("Meet the minds behind this bot:\n\n👨‍💻 STBhai\n\n❤️ A big thank you for making this bot awesome!", show_alert=True)
 
    elif query.data == "Source":
        buttons = [[
            InlineKeyboardButton('Repo', url='https://t.me/movie_storage2_0_bot')
        ],[
            InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='about'),
            InlineKeyboardButton('• ᴄʟᴏsᴇ •', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
	)
	
    elif query.data == "disclaimer":
            btn = [[
                    InlineKeyboardButton("📲 ᴄᴏɴᴛᴀᴄᴛ ᴛᴏ ᴏᴡɴᴇʀ ", user_id = ADMINS[0])
               ],[
                    InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="about")
                  ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.DISCLAIMER_TXT),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML 
	    )
    elif query.data == "earn":
       buttons = [[
	      InlineKeyboardButton('⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs ⇆', url=f'http://t.me/{temp.U_NAME}?startgroup=start')
       ],[
              InlineKeyboardButton('⋞ ʜᴏᴍᴇ', callback_data='features'),
              InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ', url=f'https://t.me/+4uFxyl0TAL0xMTg0'),
       ]]
       reply_markup = InlineKeyboardMarkup(buttons)
       await client.edit_message_media(
          chat_id=query.message.chat.id,
          message_id=query.message.id,
          media=InputMediaAnimation(
            media="https://graph.org/file/fcbf708a303f38327effe-308b22fbe6b239ee2b.gif",
            caption=script.GROUP_TEXT.format(temp.B_LINK),
            parse_mode=enums.ParseMode.HTML
        ),
        reply_markup=reply_markup
    )
   
    elif query.data == "telegraph":
        buttons = [[
            InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='features')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)  
        await query.message.edit_text(
            text=script.TELE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "font":
        buttons = [[
            InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='features')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons) 
        await query.message.edit_text(
            text=script.FONT_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
	)
  

    elif query.data == "all_files_delete":
        files = await Media.count_documents()
        await query.answer('Deleting...')
        await Media.collection.drop()
        await query.message.edit_text(f"Successfully deleted {files} files")
        
    elif query.data.startswith("killfilesak"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>ꜰᴇᴛᴄʜɪɴɢ ꜰɪʟᴇs ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword} ᴏɴ ᴅʙ...\n\nᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
        files, total = await get_bad_files(keyword)
        await query.message.edit_text(f"<b>ꜰᴏᴜɴᴅ {total} ꜰɪʟᴇs ꜰᴏʀ ʏᴏᴜʀ ǫᴜᴇʀʏ {keyword}!!</b>")
        deleted = 0
        async with lock:
            try:
                for file in files:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Media.collection.delete_one({
                        '_id': file_ids,
                    })
                    if result.deleted_count:
                        print(f'Successfully deleted {file_name} from database.')
                    deleted += 1
                    if deleted % 20 == 0:
                        await query.message.edit_text(f"<b>Process started for deleting files from DB. Successfully deleted {str(deleted)} files from DB for your query {keyword} !\n\nPlease wait...</b>")
            except Exception as e:
                print(e)
                await query.message.edit_text(f'Error: {e}')
            else:
                await query.message.edit_text(f"<b>Process Completed for file deletion !\n\nSuccessfully deleted {str(deleted)} files from database for your query {keyword}.</b>")
          
    elif query.data.startswith("reset_grp_data"):
        grp_id = query.message.chat.id
        btn = [[
            InlineKeyboardButton('☕️ ᴄʟᴏsᴇ ☕️', callback_data='close_data')
        ]]           
        reply_markup=InlineKeyboardMarkup(btn)
        await save_group_settings(grp_id, 'shortner', SHORTENER_WEBSITE)
        await save_group_settings(grp_id, 'api', SHORTENER_API)
        await save_group_settings(grp_id, 'shortner_two', SHORTENER_WEBSITE2)
        await save_group_settings(grp_id, 'api_two', SHORTENER_API2)
        await save_group_settings(grp_id, 'shortner_three', SHORTENER_WEBSITE3)
        await save_group_settings(grp_id, 'api_three', SHORTENER_API3)
        await save_group_settings(grp_id, 'verify_time', TWO_VERIFY_GAP)
        await save_group_settings(grp_id, 'third_verify_time', THREE_VERIFY_GAP)
        await save_group_settings(grp_id, 'tutorial', TUTORIAL)
        await save_group_settings(grp_id, 'tutorial_2', TUTORIAL_2)
        await save_group_settings(grp_id, 'tutorial_3', TUTORIAL_3)
        await save_group_settings(grp_id, 'template', IMDB_TEMPLATE)
        await save_group_settings(grp_id, 'caption', FILE_CAPTION)
        await save_group_settings(grp_id, 'log', LOG_VR_CHANNEL)
        await query.answer('ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ʀᴇꜱᴇᴛ...')
        await query.message.edit_text("<b>ꜱᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ʀᴇꜱᴇᴛ ɢʀᴏᴜᴘ ꜱᴇᴛᴛɪɴɢꜱ...\n\nɴᴏᴡ ꜱᴇɴᴅ /details ᴀɢᴀɪɴ</b>", reply_markup=reply_markup)

    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            await query.answer(script.ALRT_TXT, show_alert=True)
            return
        if status == "True":
            await save_group_settings(int(grp_id), set_type, False)
            await query.answer("ᴏғғ ❌")
        else:
            await save_group_settings(int(grp_id), set_type, True)
            await query.answer("ᴏɴ ✅")
        settings = await get_settings(int(grp_id))      
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
            reply_markup = InlineKeyboardMarkup(buttons)
            d = await query.message.edit_reply_markup(reply_markup)
            await asyncio.sleep(300)
            await d.delete()
        else:
            await query.message.edit_text("<b>ꜱᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ</b>")
            
    elif query.data == "reqmovie":
        if not REQUEST_CHANNEL:
            return await query.answer("❌ Request Channel is missing in info.py!", show_alert=True)
            
        userid = query.from_user.id
        
        try:
            msg_id = query.message.reply_to_message.id
        except:
            msg_id = query.message.id

        try:
            msg_text = query.message.text
            search_query = msg_text.split("movie ")[1].split(" hamare")[0].strip()
        except:
            try:
                search_query = query.message.reply_to_message.text
            except:
                search_query = "Unknown"

        btn = [[
            InlineKeyboardButton("⚙️ ᴏᴘᴛɪᴏɴs ⚙️", callback_data=f"show_options#{userid}#{msg_id}")
        ]]
        
        request_text = f"<b>🆕 ɴᴇᴡ ᴍᴏᴠɪᴇ ʀᴇǫᴜᴇsᴛ</b>\n\n<b>👤 ᴜsᴇʀ:</b> {query.from_user.mention}\n<b>🆔 ɪᴅ:</b> <code>{userid}</code>\n<b>🔍 ǫǫᴇʀʏ:</b> <code>{search_query}</code>"
        
        try:
            await client.send_message(chat_id=REQUEST_CHANNEL, text=request_text, reply_markup=InlineKeyboardMarkup(btn))
            
            await query.answer("✅ Request Sent!", show_alert=False)
            
            if search_query != "Unknown":
                header_text = f"For <code>{search_query}</code> Has Been Forwarded To Admins!"
            else:
                header_text = "Has Been Forwarded To Admins!"
            
            success_text = (
                f"<b>✅ Your Request {header_text} ⏳</b>\n\n"
                f"<blockquote>⚠️ <b>ZAROORI SOOCHNA:</b> Ek hi movie ki baar-baar request na karein. (Please don't spam!)</blockquote>"
            )
            
            await query.message.edit_text(
                text=success_text,
                reply_markup=None
            )
            
        except Exception as e:
            await query.answer("❌ Error: Request Channel settings check karein!", show_alert=True)
            print(e)
            
    elif query.data.startswith("show_options"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("✅️ ᴀᴄᴄᴇᴘᴛ ᴛʜɪꜱ ʀᴇǫᴜᴇꜱᴛ ✅️", callback_data=f"accept#{user_id}#{msg_id}")
        ],[
            InlineKeyboardButton("🚫 ʀᴇᴊᴇᴄᴛ ᴛʜɪꜱ ʀᴇǫᴜᴇꜱᴛ 🚫", callback_data=f"reject#{user_id}#{msg_id}")
        ]]
        try:
            st = await client.get_chat_member(chnl_id, userid)
            if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
                await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            elif st.status == enums.ChatMemberStatus.MEMBER:
                await query.answer(script.ALRT_TXT, show_alert=True)
        except pyrogram.errors.exceptions.bad_request_400.UserNotParticipant:
            await query.answer("⚠️ Bhai, pehle is channel ko join toh kar lo!", show_alert=True)

    elif query.data.startswith("reject"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("✗ ʀᴇᴊᴇᴄᴛᴇᴅ ✗", callback_data=f"rj_alert#{user_id}")
        ]]
        btn = [[
            InlineKeyboardButton("♻️ ᴠɪᴇᴡ sᴛᴀᴛᴜs ♻️", url=f"{query.message.link}")
        ]]
        st = await client.get_chat_member(chnl_id, userid)
        if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
            user = await client.get_users(user_id)
            request = query.message.text
            await query.answer("Message requester ko bhej diya gaya hai.")
            await query.message.edit_text(f"<s>{request}</s>")
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            try:
                await client.send_message(chat_id=user_id, text="<b>Bhai, sorry par aapki request reject kar di gayi hai. 😶</b>", reply_markup=InlineKeyboardMarkup(btn))
            except UserIsBlocked:
                await client.send_message(SUPPORT_GROUP, text=f"<b>💥 ʜᴇʟʟᴏ {user.mention},\n\nBhai, sorry par aapki request reject kar di gayi hai. 😶</b>", reply_markup=InlineKeyboardMarkup(btn), reply_to_message_id=int(msg_id))
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("accept"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("😊 ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ 😊", callback_data=f"already_available#{user_id}#{msg_id}")
        ],[
            InlineKeyboardButton("‼️ ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ ‼️", callback_data=f"not_available#{user_id}#{msg_id}")
        ],[
            InlineKeyboardButton("🥵 ᴛᴇʟʟ ᴍᴇ ʏᴇᴀʀ/ʟᴀɴɢᴜᴀɢᴇ 🥵", callback_data=f"year#{user_id}#{msg_id}")
        ],[
            InlineKeyboardButton("🙃 ᴜᴘʟᴏᴀᴅ ɪɴ 1 ʜᴏᴜʀ 🙃", callback_data=f"upload_in#{user_id}#{msg_id}")
        ],[
            InlineKeyboardButton("⚡ ᴜᴘʟᴏᴀᴅᴇᴅ ⚡", callback_data=f"uploaded#{user_id}#{msg_id}")
        ]]
        try:
            st = await client.get_chat_member(chnl_id, userid)
            if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
                await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            elif st.status == enums.ChatMemberStatus.MEMBER:
                await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        except pyrogram.errors.exceptions.bad_request_400.UserNotParticipant:
            await query.answer("⚠️ Bhai, pehle is channel ko join toh kar lo!", show_alert=True)

    elif query.data.startswith("not_available"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("🚫 ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ 🚫", callback_data=f"na_alert#{user_id}")
        ]]
        btn = [[
            InlineKeyboardButton("♻️ ᴠɪᴇᴡ sᴛᴀᴛᴜs ♻️", url=f"{query.message.link}")
        ]]
        st = await client.get_chat_member(chnl_id, userid)
        if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
            user = await client.get_users(user_id)
            request = query.message.text
            await query.answer("Message requester ko bhej diya gaya hai.")
            await query.message.edit_text(f"<s>{request}</s>")
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            try:
                await client.send_message(chat_id=user_id, text="<b>Sorry bhai, aapne jo maanga wo abhi available nahi hai. 😢</b>", reply_markup=InlineKeyboardMarkup(btn))
            except UserIsBlocked:
                await client.send_message(SUPPORT_GROUP, text=f"<b>💥 ʜᴇʟʟᴏ {user.mention},\n\nSorry bhai, aapne jo maanga wo abhi available nahi hai. 😢</b>", reply_markup=InlineKeyboardMarkup(btn), reply_to_message_id=int(msg_id))
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    # 1. MANUALLY NOTIFY USER & DELETE
    elif query.data.startswith("notify_user"):
        _, target_user_id, tmdb_id, m_char = query.data.split("#")
        target_user_id = int(target_user_id)
        m_type = "tv" if m_char == "t" else "movie"
        chnl_id = query.message.chat.id
        userid = query.from_user.id
                 
        # Check if clicker is Admin
        st = await client.get_chat_member(chnl_id, userid)
        if st.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            await query.answer("Fetching Movie details & Notifying user...", show_alert=False)
                         
            try:
                # TMDB se fresh details fetch karo
                movie = await get_poster(tmdb_id, id=True, type=m_type)
                
                # Title aur Year alag-alag nikal kar jod do
                base_title = movie.get('title') if movie else "Requested Movie"
                year = movie.get('year') if movie else ""
                
                if year and year != "N/A":
                    movie_name = f"{base_title} ({year})"
                    # URL ke liye safe format: bracket hata kar year jod diya
                    search_movie = f"{base_title}-{year}".replace(" ", "-")
                else:
                    movie_name = base_title
                    search_movie = base_title.replace(" ", "-")
                    
                poster_url = movie.get('poster') if movie else "https://i.ibb.co/HpRDS9X5/x.jpg"
                                 
                # Tera final Pro-Minimal caption
                notify_text = (
                    f"✅ **'{movie_name}' is Uploaded!**\n\n"
                    f"➖➖➖➖➖➖➖➖➖➖\n"
                    f"🎬 Aapki requested file upload kar di gayi hai.\n"
                    f"👇 Download karne ke liye niche click karein."
                )
                notify_btn = [[
                    InlineKeyboardButton('🔍 Get File', url=f'https://telegram.me/{temp.U_NAME}?start=getfile-{search_movie}')
                ]]
                                 
                # User ko seedha PM bhejo
                await client.send_photo(
                    chat_id=target_user_id,
                    photo=poster_url,
                    caption=notify_text,
                    reply_markup=InlineKeyboardMarkup(notify_btn)
                )
                                 
                # Database se request uda do taaki loop me wapas na aaye
                await db.delete_movie_request(target_user_id, tmdb_id)
                                 
                # Admin channel se request message uda do
                await query.message.delete()
                             
            except Exception as e:
                print(f"Manual Notify Error: {e}")
                await query.answer(f"Failed to notify user! Bot blocked or error: {e}", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    # ==========================================
    # 🚨 ADMIN ACTION: ADD TO QUEUE (Batching)
    # ==========================================
    elif query.data.startswith("req_queued"):
        _, target_user_id, tmdb_id, m_char = query.data.split("#")
        target_user_id = int(target_user_id)
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        
        st = await client.get_chat_member(chnl_id, userid)
        if st.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            try:
                # DATABASE ME STATUS 'QUEUED' AUR MESSAGE ID SAVE KAR DIYA (With m_char)
                await db.update_request_status(target_user_id, tmdb_id, "queued", msg_id=query.message.id, chat_id=query.message.chat.id, m_char=m_char)

                # User ko update do
                msg = (
                    f"🟢 **REQUEST ACCEPTED**\n\n"
                    f"Aapki request accept kar li gayi hai aur file **Queue (Uploading) mein lag gayi hai**.\n"
                    f"Jaise hi upload complete hoga, aapko yahi par link mil jayega. Pls thoda wait karein! ⏳"
                )
                await client.send_message(chat_id=target_user_id, text=msg)
                
                # Admin Channel Update
                admin_text = query.message.text.markdown if query.message.text else "Movie Request"
                queued_text = f"⏳ **[STATUS: IN QUEUE]** ⏳\n➖➖➖➖➖➖➖➖➖\n{admin_text}"
                
                # Ab Queue me hai toh sirf manual option bachega
                new_admin_btn = [
                    [InlineKeyboardButton("✅ Mark as Uploaded (Manual)", callback_data=f"notify_user#{target_user_id}#{tmdb_id}#{m_char}")],
                    [InlineKeyboardButton("🗑 Cancel & Delete Request", callback_data="delete_admin_msg")]
                ]
                await query.message.edit_text(text=queued_text, reply_markup=InlineKeyboardMarkup(new_admin_btn), parse_mode=enums.ParseMode.MARKDOWN)
                await query.answer("Added to Queue! User notified.", show_alert=False)
            except Exception as e:
                await query.answer(f"Error: {e}", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    # ==========================================
    # 🚨 ADMIN ACTION: NOT RELEASED YET (UPDATED)
    # ==========================================
    elif query.data.startswith("req_notrel"):
        _, target_user_id, tmdb_id = query.data.split("#")
        target_user_id = int(target_user_id)
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        
        # Admin check
        st = await client.get_chat_member(chnl_id, userid)
        if st.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            try:
                # TMDB se movie ka naam fetch karo
                movie = await get_poster(tmdb_id, id=True)
                movie_name = movie.get('title') if movie else "Aapki Requested Movie"
                
                msg = (
                    f"⚠️ **REQUEST UPDATE**\n\n"
					f"🎬 **{movie_name}**\n\n"
                    f"Yeh movie abhi officially OTT ya Internet par release nahi hui hai.\n\n"
                    f"Jaise hi release hogi, ise upload kar diya jayega."
                )
                await client.send_message(chat_id=target_user_id, text=msg)
                await db.delete_movie_request(target_user_id, tmdb_id)
                await query.message.delete()
                await query.answer("User Notified: Not Released!", show_alert=False)
            except Exception as e:
                pass
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    # ==========================================
    # 🚨 ADMIN ACTION: NOT AVAILABLE (UPDATED)
    # ==========================================
    elif query.data.startswith("req_notavail"):
        _, target_user_id, tmdb_id = query.data.split("#")
        target_user_id = int(target_user_id)
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        
        st = await client.get_chat_member(chnl_id, userid)
        if st.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            try:
                # TMDB se movie ka naam fetch karo
                movie = await get_poster(tmdb_id, id=True)
                movie_name = movie.get('title') if movie else "Aapki Requested Movie"
                
                msg = (
                    f"🚫 **REQUEST UNAVAILABLE**\n\n"
                    f"Aapki requested file **'{movie_name}'** abhi internet par available nahi hai.\n\n"
                    f"Jaise hi yeh available hogi, ise database mein add kar diya jayega."
                )
                await client.send_message(chat_id=target_user_id, text=msg)
                await db.delete_movie_request(target_user_id, tmdb_id)
                await query.message.delete()
                await query.answer("User Notified: Not Available!", show_alert=False)
            except Exception as e:
                pass
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)
	
	# 2. ONLY DELETE REQUEST (Bina User ko notify kiye)
    elif query.data == "delete_admin_msg":
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        
        st = await client.get_chat_member(chnl_id, userid)
        if st.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            await query.answer("Request Message Deleted!", show_alert=False)
            try:
                await query.message.delete()
            except:
                pass
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)
			
    elif query.data.startswith("already_available"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("🫤 ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ 🫤", callback_data=f"aa_alert#{user_id}")
        ]]
        btn = [[
            InlineKeyboardButton("♻️ ᴠɪᴇᴡ sᴛᴀᴛᴜs ♻️", url=f"{query.message.link}")
        ]]
        st = await client.get_chat_member(chnl_id, userid)
        if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
            user = await client.get_users(user_id)
            request = query.message.text
            await query.answer("Message requester ko bhej diya gaya hai.")
            await query.message.edit_text(f"<s>{request}</s>")
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            try:
                await client.send_message(chat_id=user_id, text="<b>Bhai, ye movie pehle se hi bot mein uploaded hai. Ek baar theek se search kar lo. 😋</b>", reply_markup=InlineKeyboardMarkup(btn))
            except UserIsBlocked:
                await client.send_message(SUPPORT_GROUP, text=f"<b>💥 ʜᴇʟʟᴏ {user.mention},\n\nBhai, ye movie pehle se hi bot mein uploaded hai. Ek baar theek se search kar lo. 😋</b>", reply_markup=InlineKeyboardMarkup(btn), reply_to_message_id=int(msg_id))
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("upload_in"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("😌 ᴜᴘʟᴏᴀᴅ ɪ 1 ʜᴏᴜʀ 😌", callback_data=f"upload_alert#{user_id}")
        ]]
        btn = [[
            InlineKeyboardButton("♻️ ᴠɪᴇᴡ sᴛᴀᴛᴜs ♻️", url=f"{query.message.link}")
        ]]
        st = await client.get_chat_member(chnl_id, userid)
        if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
            user = await client.get_users(user_id)
            request = query.message.text
            await query.answer("Message requester ko bhej diya gaya hai.")
            await query.message.edit_text(f"<s>{request}</s>")
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            try:
                await client.send_message(chat_id=user_id, text="<b>Aapki request agle 1 ghante mein upload ho jayegi. Thoda wait karo! ⏳</b>", reply_markup=InlineKeyboardMarkup(btn))
            except UserIsBlocked:
                await client.send_message(SUPPORT_GROUP, text=f"<b>💥 ʜᴇʟʟᴏ {user.mention},\n\nAapki request agle 1 ghante mein upload ho jayegi. Thoda wait karo! ⏳</b>", reply_markup=InlineKeyboardMarkup(btn), reply_to_message_id=int(msg_id))
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("year"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("⚠️ ᴛᴇʟʟ ᴍᴇ ʏᴇᴀʀꜱ & ʟᴀɴɢᴜᴀɢᴇ ⚠️", callback_data=f"yrs_alert#{user_id}")
        ]]
        btn = [[
            InlineKeyboardButton("♻️ ᴠɪᴇᴡ sᴛᴀᴛᴜs ♻️", url=f"{query.message.link}")
        ]]
        st = await client.get_chat_member(chnl_id, userid)
        if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
            user = await client.get_users(user_id)
            request = query.message.text
            await query.answer("Message requester ko bhej diya gaya hai.")
            await query.message.edit_text(f"<s>{request}</s>")
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            try:
                await client.send_message(chat_id=user_id, text="<b>Bhai, bina Year aur Language bataye main kaise dhoondhu? Sahi details ke sath dubara request daalo. 😬</b>", reply_markup=InlineKeyboardMarkup(btn))
            except UserIsBlocked:
                await client.send_message(SUPPORT_GROUP, text=f"<b>💥 ʜᴇʟʟᴏ {user.mention},\n\nBhai, bina Year aur Language bataye main kaise dhoondhu? Sahi details ke sath dubara request daalo. 😬</b>", reply_markup=InlineKeyboardMarkup(btn), reply_to_message_id=int(msg_id))
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("rj_alert"):
        ident, user_id = query.data.split("#")
        userid = query.from_user.id
        if str(userid) in user_id:
            await query.answer("Sorry bhai, aapki request reject ho gayi hai.", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("na_alert"):
        ident, user_id = query.data.split("#")
        userid = query.from_user.id
        if str(userid) in user_id:
            await query.answer("Sorry, ye request abhi available nahi hai.", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("ul_alert"):
        ident, user_id = query.data.split("#")
        userid = query.from_user.id
        if str(userid) in user_id:
            await query.answer("Lo bhai, aapki request upload kar di gayi hai!", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("aa_alert"):
        ident, user_id = query.data.split("#")
        userid = query.from_user.id
        if str(userid) in user_id:
            await query.answer("Bhai, ye movie pehle se hi bot mein available hai.", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("upload_alert"):
        ident, user_id = query.data.split("#")
        userid = query.from_user.id
        if str(userid) in user_id:
            await query.answer("Aapki request agle 1 ghante mein upload ho jayegi! ⏳", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("yrs_alert"):
        ident, user_id = query.data.split("#")
        userid = query.from_user.id
        if str(userid) in user_id:
            await query.answer("Sahi Year aur Language ke sath dubara request daalo bhai. 😬", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("batchfiles"):
        ident, group_id, message_id, user = query.data.split("#")
        group_id = int(group_id)
        message_id = int(message_id)
        user = int(user)
        if user != query.from_user.id:
            await query.answer(script.ALRT_TXT, show_alert=True)
            return
            
        is_premium = await db.has_premium_access(user)
        if not is_premium:
            alert_text = "🚫 BATCH DOWNLOAD LOCKED 🚫\n\nEk sath sabhi files nikalna Premium feature hai.\n\nFree users ko 1-1 karke karna hoga. Time bachane ke liye Premium lijiye! ⚡"
            await query.answer(alert_text, show_alert=True)
            return

        link = f"https://telegram.me/{temp.U_NAME}?start=allfiles_{group_id}-{message_id}"
        await query.answer(url=link)
        return
	    

async def auto_filter(client, msg, spoll=False , pm_mode = False):
    if not spoll:
        message = msg
        search = message.text
        chat_id = message.chat.id
        req = message.from_user.id if message.from_user else 0
        settings = await get_settings(chat_id , pm_mode=pm_mode)
        
        # 🔥 PRO-FIX 1: FLOODWAIT KILLER. Removed useless "Searching" message in groups.
        # Sirf private chat me loading dikhayega, group me spam (aur 20 sec ki rukawat) band!
        searching_msg = None
        if message.chat.type == enums.ChatType.PRIVATE:
            try:
                search_ui = f"🔍 <i>Searching For:</i>\n\n🍿 <b>{search}</b> 🍿"
                searching_msg = await msg.reply_text(search_ui, parse_mode=enums.ParseMode.HTML)
            except pyrogram.errors.exceptions.flood_420.FloodWait:
                pass # Agar FloodWait aaye toh loading msg skip karo
        
        # Paginated files (UI list ke liye)
        files, offset, total_results = await get_smart_search_results(search)
        
        if not files:
            # 🔥 DON'T DELETE: Pass the message to edit it
            return await advantage_spell_chok(msg, searching_msg)
            
        # 💥 THE PRO DISAMBIGUATION ENGINE V2.3 (Strict Match Fix) 💥
        has_exact_year = bool(re.search(r'\b(19\d{2}|20\d{2})\b', search))
        
        all_raw_files, _, _ = await get_search_results(search, max_results=300, offset=0)
        sorted_all_files = get_vip_sorted_files(all_raw_files, search)
        
        unique_titles = {}
        highest_match_score = 0
        
        for item in sorted_all_files:
            if item['match_score'] > highest_match_score:
                highest_match_score = item['match_score']
                
            name_title = item['name_for_sort'].title()
            year_val = item['year']
            is_series = item['is_series']
            
            # --- UI VISUAL TRUNCATION ---
            max_disp_len = 32
            if len(name_title) > max_disp_len:
                short_title = name_title[:max_disp_len].strip() + ".."
            else:
                short_title = name_title
            
            if is_series == 1:
                key_id = f"{item['name_for_sort']}_series"
                disp = f"📺 {short_title} (Series)"
                payload_search = item['name_for_sort'][:45].strip()
            else:
                year_str = str(year_val) if year_val else ""
                key_id = f"{item['name_for_sort']}_{year_str}"
                disp = f"🎬 {short_title} ({year_str})" if year_str else f"🎬 {short_title}"
                
                base_name = item['name_for_sort']
                if year_str:
                    max_name_len = 45 - len(year_str) - 1 
                    if len(base_name) > max_name_len:
                        base_name = base_name[:max_name_len].strip()
                    payload_search = f"{base_name} {year_str}"
                else:
                    payload_search = base_name[:45].strip()
                
            if key_id not in unique_titles:
                unique_titles[key_id] = (disp, payload_search)
                
        # 💥 TRIGGER LOGIC FIX: Force menu if only partial match is found (Score 1)
        force_menu = (highest_match_score == 1)
        
        # Trigger menu ONLY if multiple parts found OR we are forcing it due to poor match
        if (len(unique_titles) > 1 and not has_exact_year) or force_menu:
            # 💥 SMART PAGINATION & DYNAMIC COUNT LOGIC 💥
            page = 0
            items_per_page = 8
            all_items = list(unique_titles.items())
            total_pages = math.ceil(len(all_items) / items_per_page)
            paginated_items = all_items[page * items_per_page : (page + 1) * items_per_page]
            
            if len(DISAMBIGUATION_MAP) > 500: DISAMBIGUATION_MAP.clear()
            
            # 💥 THE BUG FIX: Case-sensitivity & Explicit Mapping 💥
            search_base = search[:20]
            DISAMBIGUATION_MAP[search_base] = search
            
            buttons = []
            for key_id, (disp, payload_search) in paginated_items:
                DISAMBIGUATION_MAP[payload_search] = search
                buttons.append([InlineKeyboardButton(disp, callback_data=f"fuz#{payload_search}")])
            
            # 💥 SMART NAVIGATION ROW 💥
            if total_pages > 1:
                nav_row = []
                nav_row.append(InlineKeyboardButton(f"📄 1 / {total_pages}", callback_data="pages"))
                nav_row.append(InlineKeyboardButton("Next ⪼", callback_data=f"fuzpage#{search[:20]}#1"))
                buttons.append(nav_row)
            
            # Agar match exact nahi hai, toh TMDB ka button lazmi do
            if force_menu:
                buttons.append([InlineKeyboardButton("🌐 Search in TMDB", callback_data=f"tmdb_search#{search[:45]}")])
                            
            buttons.append([InlineKeyboardButton("❌ Close", callback_data='close_data')])
            
            # 🔥 DYNAMIC ALERT TEXT (Removed await searching_msg.delete()) 🔥
            if force_menu:
                disambiguation_text = (
                    f"<b>⚠️ EXACT MATCH NOT FOUND</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🔍 <b>Query:</b> <code>{search.title()}</code>\n\n"
                    f"I found <b>{len(all_items)}</b> partial matches for your search.\n\n"
                    f"👇 <b>Action:</b> Pick your exact title or search in TMDB:"
                )
            else:
                disambiguation_text = (
                    f"<b>⚠️ MULTIPLE MATCHES FOUND</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🔍 <b>Query:</b> <code>{search.title()}</code>\n\n"
                    f"I found <b>{len(all_items)}</b> files related to your search.\n\n"
                    f"👇 <b>Action:</b> Pick your exact title:"
                )
                        
            # 🔥 PRO-FIX 1: Handle NoneType error for Group Chats
            if searching_msg:
                # Private chat mein message edit hoga
                k = await searching_msg.edit_text(
                    text=disambiguation_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                # Group chat mein naya message jayega
                k = await message.reply_text(
                    text=disambiguation_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=enums.ParseMode.HTML
                )
            
            #   ANTI-CLUTTER AUTO-DESTRUCT (120 seconds)
            await asyncio.sleep(120)
            try:
                await k.delete()
            except:
                pass
            return
            
        # Agar seedha result mil gaya bina menu ke, tab message delete mat karo, 
        # wo aage chalkar final poster send hone se pehle delete hoga.
        
    else:
        # THE FIX: Agar Telegram reply_to_message bhool gaya...
        settings = await get_settings(msg.message.chat.id , pm_mode=pm_mode)
        message = msg.message.reply_to_message if msg.message.reply_to_message else msg.message
        search, files, offset, total_results = spoll
        req = msg.from_user.id
		# SHOW PLEASE WAIT IMMEDIATELY
        if spoll:
            # 🛑 100% BULLETPROOF FIX: Sirf temporary search menus ko delete karenge
            msg_content = str(msg.message.text or msg.message.caption or "")
            is_temp = any(word in msg_content for word in ["MATCHES FOUND", "MATCH NOT FOUND", "ᴛᴍᴅʙ", "SPELLING"])
            
            if is_temp:
                try:
                    await msg.message.edit(f"<b><code>{search}</code> ɪs ꜰᴏᴜɴᴅ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ꜰᴏʀ ꜰɪʟᴇs 📫</b>")
                except:
                    pass
        
    key = f"{message.chat.id}-{message.id}"
    BUTTONS[key] = search
    ACTIVE_FILTERS[key] = {} # Naye search par memory saaf
    batch_ids = files
    temp.FILES_ID[key] = batch_ids
    batch_link = f"batchfiles#{message.chat.id}#{message.id}#{message.from_user.id}"
    temp.CHAT[message.from_user.id] = message.chat.id
    settings = await get_settings(message.chat.id , pm_mode=pm_mode)
    del_msg = f"\n\n<b>⚠️ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴀꜰᴛᴇʀ <code>{get_readable_time(DELETE_TIME)}</code> ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs</b>" if settings["auto_delete"] else ''
    
    # ==========================================
    # 🚀 SMART SERIES INTERCEPTOR (100% BUG FREE & MOVIE SAFE)
    # ==========================================
    try:
        message = msg.message if hasattr(msg, "data") else msg
        user_id = message.from_user.id if message.from_user else None
    except:
        message = msg
        user_id = 0

    if not re.search(r'(?i)(?:s|season)\s*\d+', search):
        def get_fname(f):
            return f.get("file_name", "") if isinstance(f, dict) else getattr(f, "file_name", "")
            
        is_series = any(re.search(r'(?i)(?:s|season)\s*0*\d+', get_fname(f)) for f in files[:5]) if files else False
        
        if is_series:
            try:
                from database.ia_filterdb import get_search_results as get_seasons
                # 🔥 FIX 2: 'filter=True' nikal diya jo database search ko error dekar rok raha tha!
                fetch_res = await get_seasons(search, offset=0, max_results=150)
                all_files_for_seasons = fetch_res[0] if isinstance(fetch_res, tuple) else fetch_res
            except Exception as e:
                all_files_for_seasons = files
            
            season_buttons = await generate_season_buttons(search, all_files_for_seasons)
            
            if season_buttons:
                text = f"📺 **{search.title()}** ek Series lag rahi hai.\n👇 Kripya apna Season select karein:"
                original_query = DISAMBIGUATION_MAP.get(search, search)
                season_buttons.append([InlineKeyboardButton("🔙 Back To Quary", callback_data=f"spell#{original_query[:45]}")])
                
                # 🔥 PRO-FIX 2: Safe fallback without Console Spam
                try:
                    if 'searching_msg' in locals() and searching_msg and not spoll:
                        await searching_msg.edit_text(text, reply_markup=InlineKeyboardMarkup(season_buttons))
                    elif hasattr(msg, "data"):
                        await msg.message.edit_text(text, reply_markup=InlineKeyboardMarkup(season_buttons))
                    else:
                        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(season_buttons))
                except pyrogram.errors.exceptions.bad_request_400.MessageIdInvalid:
                    # Message delete ho chuka hai, seedha naya message bhej do
                    try:
                        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(season_buttons))
                    except:
                        pass
                except pyrogram.errors.exceptions.bad_request_400.MessageNotModified:
                    pass # Same button dubara click hone par spam roko
                except Exception:
                    # Koi bhi aur error ho toh terminal spam kiye bina fallback chalao
                    try:
                        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(season_buttons))
                    except:
                        pass
                    # 🔥 FALLBACK: Agar edit fail ho (Message delete ho gaya ho), toh instantly NAYA message bhej do
                    try:
                        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(season_buttons))
                    except:
                        pass
                
                return # Series ke liye execution yahan ruko
    is_premium = await db.has_premium_access(req) if req else False

    # 🌟 PREMIUM TITLE SETUP (Priority 1) 🌟
    is_prem_title = False
    custom_caption = None
    custom_poster = None

    # 🔥 THE ULTIMATE FIX: commands.py ki tarah exactly file_name se check karenge!
    for f in files:
        try:
            prem_data = await db.get_premium_info(f.file_name)
            if prem_data:
                is_premium = True  # 1080p Lock Bypass for inline list
                is_prem_title = True
                if isinstance(prem_data, dict):
                    custom_caption = prem_data.get("custom_text", "").replace("\\n", "\n")
                    custom_poster = prem_data.get("image_url", "").strip()
                break # Ek bhi file match hui toh bypass activate!
        except Exception as e:
            print(f"Premium Fetch Error: {e}")
    links = ""
    if settings["link"]:
        btn = []
        
        search_term = search if 'search' in locals() else ""
        sorted_files = get_vip_sorted_files(files, search_term)
        current_start = 1 if 'offset' not in locals() or offset == "" else int(offset) + 1
        pm_prefix = "pm_mode_" if pm_mode else ""
        chat_id_to_use = ADMINS[0] if pm_mode else message.chat.id
        
        for file_num, item in enumerate(sorted_files, start=current_start):
            file = item["file"]
            file_size = get_size_compact(file.file_size)
            quality_str = to_bold(str(item["quality"]).upper())
            audio_str = to_bold(item["audio"])
            
            display_title = f'{item["icon"]} {item["clean_name"]}'
            sub_line = f"↳ [{file_size}] • [{quality_str}] • {audio_str}"
            
            divider = "\n▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n" if item.get("needs_divider") else "\n\n"
            
            if not is_premium and item.get("is_premium") == 1:
                links += f"""{divider}<b><a href="https://t.me/{temp.U_NAME}?start=reqprem">{display_title}</a></b>\n{sub_line}"""
            else:
                # 🔥 THE FATAL BUG FIX: 'query' exist nahi karta normal search me. 'message' use karna hai.
                links += f"""{divider}<b><a href="https://t.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}">{display_title}</a></b>\n{sub_line}"""
    else:
        btn = []
        search_term = search if 'search' in locals() else ""
        sorted_files = get_vip_sorted_files(files, search_term)
        pm_prefix = "pm_mode_" if pm_mode else ""
        chat_id_to_use = ADMINS[0] if pm_mode else message.chat.id
        
        for item in sorted_files:
            file = item["file"]
            file_size = get_size_compact(file.file_size)
            quality_str = to_bold(str(item["quality"]).upper())
            audio_str = to_bold(item["audio"])
            display_text = f'[{file_size}] {item["icon"]} {item["clean_name"]} [{quality_str}] {audio_str}'
            
            if not is_premium and item.get("is_premium") == 1:
                btn.append([InlineKeyboardButton(text=f"{display_text}", callback_data="reqprem")])
            else:
                btn.append([InlineKeyboardButton(text=display_text, url=f'https://telegram.dog/{temp.U_NAME}?start={pm_prefix}file_{chat_id_to_use}_{file.file_id}')])

    if offset != "":
        if total_results >= MAX_BTN:
            btn.insert(0,[
                InlineKeyboardButton("📥 𝗦𝗲𝗻𝗱 𝗔𝗹𝗹 𝗙𝗶𝗹𝗲𝘀 📥", callback_data=batch_link),
            ])
            
            has_series = any(item.get("is_series", 0) == 1 for item in sorted_files)
            mid_btn = InlineKeyboardButton("ꜱᴇᴀꜱᴏɴ", callback_data=f"seasons#{key}#{offset}#{req}") if has_series else InlineKeyboardButton("ʏᴇᴀʀ", callback_data=f"years#{key}#{offset}#{req}")
            
            btn.insert(1, [
                InlineKeyboardButton("ǫᴜᴀʟɪᴛʏ", callback_data=f"qualities#{key}#{offset}#{req}"),
                mid_btn,
                InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#{offset}#{req}")
            ])
        else:
            btn.insert(0,[
                InlineKeyboardButton("📥 𝗦𝗲𝗻𝗱 𝗔𝗹𝗹 𝗙𝗶𝗹𝗲𝘀 📥", callback_data=batch_link),
                InlineKeyboardButton("ʟᴀɴɢᴜᴀɢᴇ", callback_data=f"languages#{key}#{offset}#{req}")
            ])
    else:
        btn.insert(0,[
            InlineKeyboardButton("📥 𝗦𝗲𝗻𝗱 𝗔𝗹𝗹 𝗙𝗶𝗹𝗲𝘀 📥", callback_data=batch_link),
            ])
                             
    
    if offset != "":
        BUTTONS[key] = search
        # 🧠 THE FIX: 'req' (User ID) ko dobara overwrite mat karo, 
        # warna Next button par bot ki khud ki ID chhap jayegi.
        btn.append(
            [InlineKeyboardButton(text=f"1/{math.ceil(int(total_results) / int(MAX_BTN))}", callback_data="pages"),
             InlineKeyboardButton(text="ɴᴇxᴛ ⪼", callback_data=f"next_{req}_{key}_{offset}")]
        )
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        try:
            offset = int(offset) 
        except:
            offset = int(MAX_BTN)
        
    # 🔙 BACK TO MENU BUTTON
    if search in DISAMBIGUATION_MAP:
        btn.append([InlineKeyboardButton("🔙 Back To Menu", callback_data=f"fuzback#{key}")])

    # 🔥 FIX 2: "BACK TO ALL SEASONS" BUTTON 🔥
    s_match = re.search(r'(?i)\s*(?:s|season)\s*0*(\d+)', search)
    if s_match:
        base_name = search[:s_match.start()].strip()
        if base_name:
            # Yahan humne 'spell#' ko hata kar 'fuz#' laga diya hai. 
            # fuz# callback Disambiguation Menu (Multiple matches) ko automatically bypass karke 
            # seedha Season Interceptor ko hit karta hai (spoll=True pass karke).
            btn.append([InlineKeyboardButton("🔙 Back to All Seasons", callback_data=f"fuz#{base_name[:45]}")])
    try:
        imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    except Exception as tmdb_error:
        print(f"⚠️ TMDB Timeout/Error Ignored Safely: {tmdb_error}")
        imdb = None
        
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b>📂 ʜᴇʀᴇ ɪ ꜰᴏᴜɴᴅ ꜰᴏʀ ʏᴏᴜʀ sᴇᴀʀᴄʜ {search}</b>"

    ads, ads_name, _ = await mdb.get_advirtisment()
    ads_text = ""
    if ads is not None and ads_name is not None:
        ads_url = f"https://t.me/{temp.U_NAME}?start=ads"
        ads_text = f"<a href={ads_url}>{ads_name}</a>"

    js_ads = f"\n━━━━━━━━━━━━━━━━━━\n <b>{ads_text}</b> \n━━━━━━━━━━━━━━━━━━" if ads_text else ""
    CAP[key] = cap
    
    # 🔥 SAFE DELETE LOGIC (Wait message ko files aane ke theek pehle udaega) 🔥
    if spoll and hasattr(msg, "message"):
        try:
            await msg.message.delete()
        except:
            pass
    elif 'searching_msg' in locals():
        try:
            await searching_msg.delete()
        except:
            pass

    if imdb and imdb.get('poster'):
        try:
            if settings['auto_delete']:
                k = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024] + links + del_msg, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
                await asyncio.sleep(DELETE_TIME)
                await k.delete()
            else:
                await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024] + links + js_ads, reply_markup=InlineKeyboardMarkup(btn))                    
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            try: # 🔥 PRO-FIX: Second attempt ko try-except mein wrap kiya taaki dead URL par bot crash na ho
                if settings["auto_delete"]:
                    k = await message.reply_photo(photo=poster, caption=cap[:1024] + links + js_ads, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
                    await asyncio.sleep(DELETE_TIME)
                    await k.delete()
                else:
                    await message.reply_photo(photo=poster, caption=cap[:1024] + links + js_ads, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))
            except Exception:
                # Agar fallback image bhi load na ho, toh chup-chaap text message bhej do
                if settings["auto_delete"]:
                    k = await message.reply_text(cap + links + js_ads, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
                    await asyncio.sleep(DELETE_TIME)
                    await k.delete()
                else:
                    await message.reply_text(cap + links + js_ads, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
        except Exception as e:
            print(e)
            if settings["auto_delete"]:
                try:
                    k = await message.reply_text(cap + links + js_ads, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
                except Exception as e:
                    print("error", e)
                await asyncio.sleep(DELETE_TIME)
                await k.delete()
            else:
                await message.reply_text(cap + links + js_ads, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
    else:
        k = await message.reply_text(text=cap + links + js_ads, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(btn), parse_mode=enums.ParseMode.HTML, reply_to_message_id=message.id)
        if settings['auto_delete']:
            await asyncio.sleep(DELETE_TIME)
            await k.delete()
from info import ADMINS

@Client.on_message(filters.command("update_cache") & filters.user(ADMINS))
async def refresh_fuzz_cache(client, message):
    # Ye function purani RAM delete karke nayi RAM load karega bina bot restart kiye
    global CACHE_LOADED, IN_MEMORY_TITLES, TITLE_MAP
    
    m = await message.reply_text("⏳ **Refreshing Database Cache...**\nIsme 2-5 second lagenge.")
    
    # Purana kachra saaf karo
    CACHE_LOADED = False
    IN_MEMORY_TITLES.clear()
    TITLE_MAP.clear()
    
    # Naya cache build karo
    await build_title_cache()
    
    await m.edit_text(f"✅ **Cache Successfully Updated!**\n\nAb RapidFuzz nayi movies ko bhi search kar lega.\n🎬 Total Movies in Memory: `{len(IN_MEMORY_TITLES)}`")
