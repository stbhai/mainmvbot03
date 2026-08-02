import logging
import urllib.parse
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from database.jsreferdb import referdb
from database.users_chats_db import db
from datetime import datetime, timedelta
from pyrogram import StopPropagation
from plugins.pm_filter import to_bold

def get_ui_progress_bar(current, target):
    if current >= target: return "🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩", 100
    ratio = current / target
    filled = int(ratio * 10)
    return "🟩" * filled + "⬜" * (10 - filled), int(ratio * 100)

async def render_refer_ui(client, query_or_message, force_new=False):
    user_id = query_or_message.from_user.id
    data = referdb.get_refer_data(user_id)
    
    invites = data.get('total_invites', 0)
    claimed = data.get('claimed_milestones', [])
    inf_claims = data.get('infinite_claims', 0)
    
    if invites < 1: next_target = 1
    elif invites < 3: next_target = 3
    elif invites < 7: next_target = 7
    elif invites < 15: next_target = 15
    else: next_target = 15 + ((inf_claims + 1) * 5)

    p_bar, percent = get_ui_progress_bar(invites if invites < 15 else (invites - 15) - (inf_claims * 5), next_target if invites < 15 else 5)
    
    # 🔥 UX FIX: Link ko caption ke niche lane ke liye url parameter hata kar text ke bottom me inject kiya
    bot_link = f"https://t.me/{client.me.username}?start=reff_{user_id}"
    raw_text = (
        f"🍿 **Hey! Agar tum Movies & Web Series dekhte ho, to ye Telegram Bot zaroor try karna.**\n\n"
        f"Thousands of Movies & Web Series available hain with fast direct downloads.\n\n"
        f"🎁 New users ko FREE VIP Trial bhi milta hai.\n\n"
        f"🔗 **Click here to join:**👇\n {bot_link}"
    )
    encoded_text = urllib.parse.quote(raw_text)
    invite_url = f"https://telegram.me/share/url?text={encoded_text}"

    # ⚡ FAST LINK GENERATOR (Zero lag) - FIXED INDENTATION & MOVED OUT OF IF/ELSE
    bot_username = client.me.username if client.me else (await client.get_me()).username
    refer_link = f"https://t.me/{bot_username}?start=reff_{user_id}"

    if invites < 15:
        text = (
            f"🎁 **𝗥𝗘𝗙𝗘𝗥 & 𝗘𝗔𝗥𝗡 𝗣𝗥𝗘𝗠𝗜𝗨𝗠** 🎁\n━━━━━━━━━━━━━━━━━━━━\n"
            f"👋 Hello {query_or_message.from_user.first_name},\n"
            f"<b>Invite your friends and unlock Premium for FREE,</b> Jitne zyada friends join karenge, utne bade Rewards unlock honge.\n\n"
            f"📊 **𝗬𝗢𝗨𝗥 𝗟𝗜𝗩𝗘 𝗦𝗧𝗔𝗧𝗦:**\n"
            f"├ 📈 Total Invites: **{str(invites).zfill(2)} Users**\n"
            f"└ 🎁 Rewards Claimed: **{len(claimed)} / 4 Completed**\n\n"
            f"🚀 **𝗡𝗘𝗫𝗧 𝗠𝗜𝗟𝗘𝗦𝗧𝗢𝗡𝗘 𝗣𝗥𝗢𝗚𝗥𝗘𝗦𝗦:**\n"
            f"┃{p_bar}┃ **{percent}%**\n"
            f"🔥 Only **{next_target - invites} successful invites** aur chahiye next Premium Reward unlock karne ke liye!\n\n"
            f"🎁 **𝗥𝗘𝗪𝗔𝗥𝗗 𝗟𝗘𝗩𝗘𝗟𝗦:**\n"
            f"{'✅' if 'm1' in claimed else '🔓' if invites >= 1 else '🔒'} 01 Invite  ➔ 12 Hours Premium\n"
            f"{'✅' if 'm2' in claimed else '🔓' if invites >= 3 else '🔒'} 03 Invites ➔ 03 Days Premium\n"
            f"{'✅' if 'm3' in claimed else '🔓' if invites >= 7 else '🔒'} 07 Invites ➔ 10 Days Premium\n"
            f"{'✅' if 'm4' in claimed else '🔓' if invites >= 15 else '🔒'} 15 Invites ➔ 01 Month Premium\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 𝗬𝗼𝘂𝗿 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗟𝗶𝗻𝗸: 👇\n"
            f"`{refer_link}`"
        )
    else:
        text = (
            f"🔄 **𝗜𝗡𝗙𝗜𝗡𝗜𝗧𝗘 𝗟𝗢𝗢𝗣 𝗠𝗢𝗗𝗘: 𝗔𝗖𝗧𝗜𝗩𝗘** 🔄\n━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 Absolute Legend! Aapne saare main milestones successfully clear kar liye hain.\n\n"
            f"🚀 The grind doesn't stop! Ab har **5 NAYE INVITES** par aapko flat **7 Days Premium** milta rahega, without any limits!\n\n"
            f"📊 **𝗬𝗢𝗨𝗥 𝗟𝗜𝗩𝗘 𝗦𝗧𝗔𝗧𝗦:**\n"
            f"├ 📈 Total Invites: **{invites} Users**\n"
            f"└ 🔄 Infinite Loop Claims: **{inf_claims} Times Rewarded**\n\n"
            f"🎯 **𝗖𝗨𝗥𝗥𝗘𝗡𝗧 𝗟𝗢𝗢𝗣 𝗣𝗥𝗢𝗚𝗥𝗘𝗦𝗦:**\n"
            f"┃{p_bar}┃ **{percent}%**\n"
            f"🔥 Flat 7 Days Premium ke liye bas **{next_target - invites} naye invites** aur chahiye!\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 𝗬𝗼𝘂𝗿 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗟𝗶𝗻𝗸: 👇\n"
            f"`{refer_link}`"
        )

    can_claim = False
    claim_payload = "none"
    
    if invites >= 1 and 'm1' not in claimed: can_claim, claim_payload = True, "claim_m1_12h"
    elif invites >= 3 and 'm2' not in claimed: can_claim, claim_payload = True, "claim_m2_3d"
    elif invites >= 7 and 'm3' not in claimed: can_claim, claim_payload = True, "claim_m3_10d"
    elif invites >= 15 and 'm4' not in claimed: can_claim, claim_payload = True, "claim_m4_30d"
    elif invites >= 15 and (invites - 15) >= ((inf_claims + 1) * 5): can_claim, claim_payload = True, "claim_inf_7d"

    btn = []
    if can_claim:
        btn.append([InlineKeyboardButton("🎁 Cʟᴀɪᴍ Yᴏᴜʀ Rᴇᴡᴀʀᴅ", callback_data=claim_payload)])
        
    btn.append([InlineKeyboardButton('📨 Sʜᴀʀᴇ Yᴏᴜʀ Rᴇғᴇʀ Lɪɴᴋ', url=invite_url)])
    # 🔥 ADDED TOP 10 BUTTON HERE
    btn.append([InlineKeyboardButton('🏆 Top 10 Inviters', callback_data='top_referrers')])
    btn.append([InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='start'), InlineKeyboardButton('❌ Close', callback_data='close_data')])

    if hasattr(query_or_message, "data") and not force_new:
        try:
            # 🔥 FIX: Ab ye caption ke sath sath Main Refer wali photo ko bhi wapas set karega!
            await client.edit_message_media(
                chat_id=query_or_message.message.chat.id,
                message_id=query_or_message.message.id,
                media=InputMediaPhoto(media="https://i.ibb.co/4wBDD9PC/x.jpg", caption=text),
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except Exception:
            pass
    elif hasattr(query_or_message, "data") and force_new:
        # Callback se aaya hai par FRESH message chahiye
        await query_or_message.message.reply_photo(photo="https://i.ibb.co/4wBDD9PC/x.jpg", caption=text, reply_markup=InlineKeyboardMarkup(btn))
    else:
        # Seedha /refer command se aaya hai
        await query_or_message.reply_photo(photo="https://i.ibb.co/4wBDD9PC/x.jpg", caption=text, reply_markup=InlineKeyboardMarkup(btn))

@Client.on_message(filters.command("refer") & filters.private, group=-3)
@Client.on_callback_query(filters.regex(r"^reffff"), group=-3)
async def refer_panel_handler(client, message_or_query):
    force_new_msg = False
    
    if hasattr(message_or_query, "data"):
        await message_or_query.answer()
        # Message ka text/caption check karega
        msg_content = str(message_or_query.message.caption or message_or_query.message.text or "")
        
        # 🔥 SMART BYPASS: Agar Top 10 se 'Back' dabaya hai (Leaderboard text hai) toh Edit karega.
        # Lekin agar VIP Trial ya kisi aur menu se dabaya hai, toh 100% NEW MESSAGE bhejega!
        if "𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗" not in msg_content:
            force_new_msg = True
            
    # Ab ye function ko batayega ki naya message bhejna hai ya nahi
    await render_refer_ui(client, message_or_query, force_new=force_new_msg)
    raise StopPropagation

# 🔥 TOP 10 REFERRERS HANDLER (MONTHLY & ALL-TIME TOGGLE)
@Client.on_callback_query(filters.regex(r"^top_referrers"), group=-3)
async def top_referrers_panel(client, query):
    # Ignore double clicks on active tab instantly
    if query.data == "ignore":
        return await query.answer("Ye tab already active hai!", show_alert=False)

    # 1. 🔥 SABSE PEHLE USER ID DEFINE KARNA HAI (Isi wajah se tera code fail tha)
    user_id = query.from_user.id
    period = "alltime" if "alltime" in query.data else "monthly"
    
    # 2. Database Fetch
    top_users = referdb.get_top_referrers(period=period)
    
    # 3. 🔥 DYNAMIC IMAGE ROUTING
    if period == "alltime":
        board_image = "https://i.ibb.co/ymgdMzbx/x.jpg" # 👈 Yahan All-Time wali image aayegi
        user_data = referdb.get_refer_data(user_id)
        my_invites = user_data.get('total_invites', 0)
        board_title = "𝗧𝗢𝗣 𝟭𝟬 𝗔𝗟𝗟-𝗧𝗜𝗠𝗘 𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗"
        sub_text = "Ye hamare All-Time Top 10 members hain jinhone sabse zyada referrals kiye hain."
    else:
        board_image = "https://i.ibb.co/gFPQ8Jmp/x.jpg" # 👈 Yahan Monthly wali image aayegi
        my_invites = referdb.get_user_monthly_invites(user_id)
        board_title = "𝗧𝗢𝗣 𝟭𝟬 𝗠𝗢𝗡𝗧𝗛𝗟𝗬 𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗"
        sub_text = "Is mahine ke Top 10 referrers. Har mahine ki 1 tareekh ko ye list reset hoti hai!"

    if not top_users:
        list_text = f"⚠️ *Abhi tak is period mein koi referral nahi hua hai!*\n"
    else:
        list_text = ""
        
    is_in_top_10 = False
    user_rank_in_top_10 = 0

    # 🚀 PRECISION UI BUILDER LOOP
    for i, u in enumerate(top_users, 1):
        try:
            user_info = await client.get_users(u['user_id'])
            full_name = user_info.first_name or "User"
        except:
            full_name = f"User {str(u['user_id'])[:4]}"
            
        first_name = full_name.split()[0].strip()
        if len(first_name) > 10:
            first_name = first_name[:8] + ".."
            
        u_invites = u.get("total_invites", 0)
        
        if i == 1: prefix = "🥇 01"
        elif i == 2: prefix = "🥈 02"
        elif i == 3: prefix = "🥉 03"
        else: prefix = f"🏅 {i:02d}."
            
        base_line = f"{prefix} {first_name} — {u_invites} Invites"
        
        if u['user_id'] == user_id:
            is_in_top_10 = True
            user_rank_in_top_10 = i
            from plugins.pm_filter import to_bold # Local import
            unicode_line = to_bold(base_line)
            list_text += f"{unicode_line} 🔥\n"
        else:
            list_text += f"**{base_line}**\n"

    # 🧠 SMART DYNAMIC CAPTION ENGINE (4-Tier Edition)
    if my_invites == 0:
        rank_text = "❌ **Your Rank:** `N/A (No Rank)`"
        bottom_msg = "🚀 **Abhi tak aapne apna referral journey start nahi kiya hai. Apna invite link doston ke saath share karein, pehla Premium reward unlock karein aur Leaderboard par apni jagah banayein!**"
    elif is_in_top_10 and user_rank_in_top_10 == 1:
        rank_text = f"👑 **Your Rank:** `#{user_rank_in_top_10:02d}`"
        bottom_msg = "🏆 **Congratulations! Aap Leaderboard ke Rank #1 par hain. Invite share karte rahiye aur apni 1st position banaye rakhiye!**"
    elif is_in_top_10:
        rank_text = f"⭐ **Your Rank:** `#{user_rank_in_top_10:02d}` (In Top 10)"
        bottom_msg = "🏆 **Amazing progress! Aap already Top 10 mein ho. Bas kuch aur successful invites aur aap Leaderboard mein aur upar pahunch sakte hain!**"
    else:
        actual_rank = referdb.get_user_rank(my_invites, period=period)
        rank_text = f"📈 **Your Rank:** `#{actual_rank:02d}`"
        bottom_msg = "🚀 **Top 10 mein jagah banane ke liye sirf kuch aur successful invites chahiye. Apna invite link share karo aur Leaderboard par apni position secure karo!**"
        
    # 🎨 FINAL RENDER ASSEMBLY
    text = (
        f"{board_title}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{sub_text}\n\n"
        f"{list_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **𝗬𝗢𝗨𝗥 𝗟𝗜𝗩𝗘 𝗥𝗔𝗡𝗞:**\n"
        f"{rank_text}\n"
        f"👥 **Total Invites:** `{my_invites:02d} Users`\n\n"
        f"{bottom_msg}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    # 🔥 DYNAMIC UI BUTTONS SETUP
    btn = []
    if period == "monthly":
        btn.append([
            InlineKeyboardButton("🟢 Monthly", callback_data="ignore"),
            InlineKeyboardButton("🏆 All Time", callback_data="top_referrers_alltime")
        ])
    else:
        btn.append([
            InlineKeyboardButton("🗓️ Monthly", callback_data="top_referrers_monthly"),
            InlineKeyboardButton("🟢 All Time", callback_data="ignore")
        ])
        
    btn.append([InlineKeyboardButton('🔙 Back to Refer Zone', callback_data='reffff')])
    
    # 🖼️ MEDIA AND CAPTION SWAP ENGINE (Zero lag, zero message drops)
    await client.edit_message_media(
        chat_id=query.message.chat.id,
        message_id=query.message.id,
        media=InputMediaPhoto(media=board_image, caption=text),
        reply_markup=InlineKeyboardMarkup(btn)
    )
    raise StopPropagation

@Client.on_callback_query(filters.regex(r"^claim_"), group=-3)
async def claim_reward_processor(client, query):
    try:
        user_id = query.from_user.id
        action = query.data
        
        hours_to_add = 0
        milestone_tag = ""
        
        if action == "claim_m1_12h": hours_to_add, milestone_tag = 12, "m1"
        elif action == "claim_m2_3d": hours_to_add, milestone_tag = 72, "m2"
        elif action == "claim_m3_10d": hours_to_add, milestone_tag = 240, "m3"
        elif action == "claim_m4_30d": hours_to_add, milestone_tag = 720, "m4"
        elif action == "claim_inf_7d": hours_to_add, milestone_tag = 168, "inf"
        else: 
            await query.answer("⚠️ Invalid Action", show_alert=True)
            raise StopPropagation

        user_doc = await db.get_user(user_id)
        current_expiry = user_doc.get("expiry_time") if user_doc else None
        
        if isinstance(current_expiry, str):
            try:
                current_expiry = datetime.fromisoformat(current_expiry)
            except ValueError:
                current_expiry = None

        if current_expiry:
            if hasattr(current_expiry, "tzinfo") and current_expiry.tzinfo is not None:
                current_expiry = current_expiry.replace(tzinfo=None)
            
            if current_expiry > datetime.now():
                new_expiry = current_expiry + timedelta(hours=hours_to_add)
            else:
                new_expiry = datetime.now() + timedelta(hours=hours_to_add)
        else:
            new_expiry = datetime.now() + timedelta(hours=hours_to_add)
            
        # 🔥 SALE UPDATE: Milestone claimer gets 'referral' tag
        await db.update_user({
            "id": user_id, 
            "expiry_time": new_expiry, 
            "premium_type": "referral",
            "notified_3d": False,
            "notified_2d": False,
            "notified_1d": False
        })
        
        if milestone_tag == "inf":
            referdb.log_infinite_claim(user_id)
        else:
            referdb.log_claimed_milestone(user_id, milestone_tag)
            
        await query.answer(f"🎉 BOOM! You claimed {hours_to_add} Hours of Premium!", show_alert=True)
        
        await render_refer_ui(client, query)
        raise StopPropagation
        
    except Exception as e:
        logging.error(f"Error in claim_reward_processor: {e}")
        await query.answer("❌ Error claiming reward! Background logs check karo.", show_alert=True)
        raise StopPropagation
