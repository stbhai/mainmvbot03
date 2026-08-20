import re
from os import environ,getenv
from Script import script

id_pattern = re.compile(r'^.\d+$')
def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default
#---------------------------------------------------------------
#---------------------------------------------------------------         ,
SESSION = environ.get('SESSION', 'Media_search')
API_ID = int(environ.get('API_ID', '28271319'))
API_HASH = environ.get('API_HASH', '84d8b635a127218158581c0fd8225770')
BOT_TOKEN = environ.get('BOT_TOKEN', '8503895423:AAFZjVcXOIRltPJcy3_zaH6H0TVajWecUmg')
TMDB_API_KEY = environ.get('TMDB_API_KEY', 'b708ac88d945bc71091f85b2996982ee')
#---------------------------------------------------------------
#---------------------------------------------------------------
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '6557692712 5595790317 7509833302').split()]
USERNAME = environ.get('USERNAME', "stbhai_admin") # ADMIN USERNAME
LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1003916731885'))
MOVIE_GROUP_LINK = environ.get('MOVIE_GROUP_LINK', 'https://t.me/+pEUmki3XiYI1OWI1')
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ.get('CHANNELS', '-1003396198673 -1003469841274 -1002096567005 -1003983178241').split()]
#---------------------------------------------------------------
#---------------------------------------------------------------
DATABASE_URI = environ.get('DATABASE_URI', "mongodb+srv://theamanchaudhary:updatesbyaman@cluster0.p45995l.mongodb.net/?appName=Cluster0")
DATABASE_NAME = environ.get('DATABASE_NAME', "stdb")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'stg')
#---------------------------------------------------------------
#---------------------------------------------------------------
#----------- There will be channel id add in all these ---------
LOG_API_CHANNEL = int(environ.get('LOG_API_CHANNEL', '-1003768537428'))  # set shortner log channel
DELETE_CHANNELS = int(environ.get('DELETE_CHANNELS','-1003987967031')) # The movie you upload in it will be deleted from the bot.
LOG_VR_CHANNEL = int(environ.get('LOG_VR_CHANNEL', '-1003916731885'))
PREMIUM_LOG_CHANNEL = int(environ.get('PREMIUM_LOG_CHANNEL', '-1004321043780')) # Apne naye sales log channel ki ID daalo
PRN_ID = int(environ.get('PRN_ID', '-1003736390839')) # VIP Adult Channel ID
VIP_GROUP_ID = int(environ.get('VIP_GROUP_ID', '-1003920104895'))
NEW_PREMIUM_CHANNEL = int(environ.get('NEW_PREMIUM_CHANNEL', '-1004325068056'))
auth_channel = environ.get('AUTH_CHANNEL', '-1001620891165')
SUPPORT_GROUP = int(environ.get('SUPPORT_GROUP', '-1002245202705'))
request_channel = environ.get('REQUEST_CHANNEL', '-1003978935963') # If anyone sends a request message to your bot, you will get it in this channel.
MOVIE_UPDATE_CHANNEL = int(environ.get('MOVIE_UPDATE_CHANNEL', '-1003672727463')) # 
SUPPORT_CHAT = environ.get('SUPPORT_CHAT', 'https://t.me/stbhai_admin') #Support group link ( make sure bot is admin )
#---------------------------------------------------------------
#---------------------------------------------------------------
IS_VERIFY = False
#---------------------------------------------------------------
TUTORIAL = environ.get("TUTORIAL", "https://t.me/howtodownload_moviestorage/3")
TUTORIAL_2 = environ.get("TUTORIAL_2", "https://t.me/howtodownload_moviestorage/3")
TUTORIAL_3 = environ.get("TUTORIAL_3", "https://t.me/howtodownload_moviestorage/3")
VERIFYED_IMG = environ.get("VERIFYED_IMG", "https://i.ibb.co/qMh6Pf2V/x.jpg")
VERIFY_IMG = environ.get("VERIFY_IMG", "https://i.ibb.co/zTLRR7hr/x.jpg")
SHORTENER_API = environ.get("SHORTENER_API", "00d270e1cd595ef1bf331e398858ed8dfcbf6e18")
SHORTENER_WEBSITE = environ.get("SHORTENER_WEBSITE", 'adrinolinks.in')
SHORTENER_API2 = environ.get("SHORTENER_API2", "ecd3796d2270b7b8c458112b69e095641c6398e0")
SHORTENER_WEBSITE2 = environ.get("SHORTENER_WEBSITE2", 'gplinks.in')
SHORTENER_API3 = environ.get("SHORTENER_API3", "00d270e1cd595ef1bf331e398858ed8dfcbf6e18")
SHORTENER_WEBSITE3 = environ.get("SHORTENER_WEBSITE3", 'adrinolinks.in')
TWO_VERIFY_GAP = int(environ.get('TWO_VERIFY_GAP', "900"))
THREE_VERIFY_GAP = int(environ.get('THREE_VERIFY_GAP', "79200"))
#---------------------------------------------------------------
#---------------------------------------------------------------
LANGUAGES = ["hindi", "english", "telugu", "tamil", "kannada", "malayalam", "bengali", "marathi", "gujarati", "punjabi"]
QUALITIES = ["hdrip", "web-dl", "480p", "720p", "1080p", "1440p"]
YEARS = [f'{i}' for i in range(2025, 2002,-1 )]
SEASONS = [f'season {i}'for i in range (1 , 10)]
REF_PREMIUM = 30
PREMIUM_POINT = 1500
#---------------------------------------------------------------
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else None
REQUEST_CHANNEL = int(request_channel) if request_channel and id_pattern.search(request_channel) else None
#---------------------------------------------------------------
#---------------------------------------------------------------
#---------------------------------------------------------------
START_IMG = (environ.get('START_IMG', 'https://i.ibb.co/2YPtt7ZV/x.jpg')).split()
FORCESUB_IMG = environ.get('FORCESUB_IMG', 'https://i.ibb.co/MkNNn954/x.jpg')
REFER_PICS = (environ.get("REFER_PICS", "https://i.ibb.co/8gZGWnWK/x.jpg")).split() 
PAYPICS = (environ.get('PAYPICS', 'https://i.ibb.co/CpZdBkX3/x.jpg')).split()
SUBSCRIPTION = (environ.get('SUBSCRIPTION', 'https://i.ibb.co/GfC0C3CR/x.jpg'))
REACTIONS = ["👀", "😱", "🔥", "😍", "🎉", "🥰", "😇", "⚡"]
#---------------------------------------------------------------
#---------------------------------------------------------------
#---------------------------------------------------------------
FILE_AUTO_DEL_TIMER = int(environ.get('FILE_AUTO_DEL_TIMER', '600'))
AUTO_FILTER = is_enabled('AUTO_FILTER', True)
IS_PM_SEARCH = is_enabled('IS_PM_SEARCH', False)
IS_SEND_MOVIE_UPDATE = is_enabled('IS_SEND_MOVIE_UPDATE', True) # Don't Change It ( If You Want To Turn It On Then Turn It On By Commands) We Suggest You To Make It Turn Off If You Are Indexing Files First Time.
PORT = environ.get('PORT', '5050')
MAX_BTN = int(environ.get('MAX_BTN', '8'))
AUTO_DELETE = is_enabled('AUTO_DELETE', True)
DELETE_TIME = int(environ.get('DELETE_TIME', 600))
IMDB = is_enabled('IMDB', False)
FILE_CAPTION = environ.get('FILE_CAPTION', f'{script.FILE_CAPTION}')
IMDB_TEMPLATE = getenv("IMDB_TEMPLATE", "🧿 ᴛɪᴛʟᴇ : {title} \n🌟 ʀᴀᴛɪɴɢ : {rating} \n🎭 ɢᴇɴʀᴇ : {genres} \n📆 ʀᴇʟᴇᴀsᴇ : {year}\n")
LONG_IMDB_DESCRIPTION = is_enabled('LONG_IMDB_DESCRIPTION', False)
PROTECT_CONTENT = is_enabled('PROTECT_CONTENT', False)
SPELL_CHECK = is_enabled('SPELL_CHECK', True)
LINK_MODE = is_enabled('LINK_MODE', True)

#---------------------------------------------------------------
#---------------------------------------------------------------
#---------------------------------------------------------------
STREAM_MODE = bool(environ.get('STREAM_MODE', False)) # Set True or Flase
# Online Stream and Download

MULTI_CLIENT = False
SLEEP_THRESHOLD = int(environ.get('SLEEP_THRESHOLD', '60'))
PING_INTERVAL = int(environ.get("PING_INTERVAL", "1200"))  # 20 minutes
if 'DYNO' in environ:
    ON_HEROKU = True
else:
    ON_HEROKU = False
URL = environ.get("FQDN", "")

#---------------------------------------------------------------
#---------------------------------------------------------------
SETTINGS = {
            'spell_check': SPELL_CHECK,
            'auto_filter': AUTO_FILTER,
            'file_secure': PROTECT_CONTENT,
            'auto_delete': AUTO_DELETE,
            'template': IMDB_TEMPLATE,
            'caption': FILE_CAPTION,
            'tutorial': TUTORIAL,
            'tutorial_2': TUTORIAL_2,
            'tutorial_3': TUTORIAL_3,
            'shortner': SHORTENER_WEBSITE,
            'api': SHORTENER_API,
            'shortner_two': SHORTENER_WEBSITE2,
            'api_two': SHORTENER_API2,
            'log': LOG_VR_CHANNEL,
            'imdb': IMDB,
            'link': LINK_MODE, 
            'is_verify': IS_VERIFY, 
            'verify_time': TWO_VERIFY_GAP,
            'shortner_three': SHORTENER_WEBSITE3,
            'api_three': SHORTENER_API3,
            'third_verify_time': THREE_VERIFY_GAP
}

admin_cmds = [
    "/add_premium", "/premium_users", "/remove_premium", "/add_redeem",
    "/refresh", "/set_muc", "/pm_search_on", "/pm_search_off",
    "/set_ads", "/del_ads", "/setlist", "/clearlist",
    "/verify_id", "/index", "/send", "/leave",
    "/ban", "/unban", "/broadcast", "/grp_broadcast",
    "/delreq", "/channel", "/del_file", "/delete",
    "/deletefiles", "/deleteall", 
    "All These Commands Can Be Used Only By Admins.", 
    "⚡ powered by @movie_storage2_0_bot"
]

cmds = [
    {"start": "Start The Bot"},
    {"most": "Get Most Searches Button List"},
    {"trend": "Get Top Trending Button List"},
    {"mostlist": "Show Most Searches List"},
    {"trendlist": "𝖦𝖾𝗍 𝖳𝗈𝗉 𝖳𝗋𝖾𝗇𝖽𝗂𝗇𝗀 𝖡𝗎𝗍𝗍𝗈𝗇 𝖫𝗂𝗌t"},
    {"plan": "Check Available Premium Membership Plans"},
    {"myplan": "Check Your Currunt Plan"},
    {"refer": "To Refer Your Friend And Get Premium"},
    {"stats": "Check My Database"},
    {"id": "Get Telegram Id"},
    {"font": "To Generate Cool Fonts"},
    {"details": "Check Group Details"},
    {"settings": "Change Bot Setting"},
    {"grp_cmds": "Check Group Commands"},
    {"admin_cmds": "Bot Admin Commands"}
]
