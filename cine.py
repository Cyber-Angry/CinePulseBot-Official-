import os
import logging
from datetime import datetime

# ✅ Only This Logging Config Should Exist
logging.basicConfig(
    level=logging.DEBUG,  # Or use INFO if you want only important messages
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cinepulse.log"),   # Save to file
        logging.StreamHandler()                 # Show in terminal
    ]
)

logging.info("🎬 CinePulseBot is running...")

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

from user_logger import log_user, is_banned, handle_bot_block, BOT_OWNER_ID
from security import is_user_allowed
from howtouse import send_how_to_use
from request import handle_request
from search import search_movie
from logger import get_click_logs, get_search_logs, log_search
from logger import clear_click_logs, clear_search_logs
from telegram.ext import CommandHandler
from security import admin_only  # only if you're using admin filter
from blocked import is_user_blocked, is_banned
from functools import wraps

def block_check(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if is_banned(user_id) or is_user_blocked(user_id):
            return  # Blocked user: no response
        return await func(update, context, *args, **kwargs)
    return wrapper

import latest, series, anime, kdrama, south, hollywood, bollywood, marvel, eighteenplus, multipart
import eighteenplus as eighteen  # ✅ This line is required to fix the KeyError
from admin import admin_panel, handle_admin_callback, handle_admin_id


# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Force Join Channels
FORCE_JOIN_CHANNELS = ["@cinepulsebot_official", "@modflux_99"]

# 🔘 Build Reply Keyboard (with Admin button conditionally)
def build_menu_keyboard(user_id):
    keyboard = [
        ["𝐋𝐚𝐭𝐞𝐬𝐭 𝐑𝐞𝐥𝐞𝐚𝐬𝐞𝐬 ✨🎞️"],
        ["𝐀𝐧𝐢𝐦𝐞 💀🔥", "𝐖𝐞𝐛𝐬𝐞𝐫𝐢𝐞𝐬 🎭📺"],
        ["𝐊-𝐃𝐫𝐚𝐦𝐚𝐬 💕✨", "𝐒𝐨𝐮𝐭𝐡 𝐌𝐨𝐯𝐢𝐞𝐬 💣🔥"],
        ["𝐇𝐨𝐥𝐥𝐲𝐰𝐨𝐨𝐝 🎬🌍", "𝐁𝐨𝐥𝐥𝐲𝐰𝐨𝐨𝐝 🌟🎥"],
        ["𝐌𝐚𝐫𝐯𝐞𝐥 + 𝐃𝐂 🦸‍♂️⚡", "𝟏𝟖+ 𝐂𝐨𝐧𝐭𝐞𝐧𝐭 🔞🔥"],
        ["𝗠𝘂𝗹𝘁𝗶-𝗣𝗮𝗿𝘁 𝗠𝗼𝘃𝗶𝗲𝘀 🎬"],
        ["𝐒𝐞𝐚𝐫𝐜𝐡 🔍🧠"],
        ["𝐇𝐨𝐰 𝐭𝐨 𝐔𝐬𝐞 📘💡", "𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐚 𝐂𝐨𝐧𝐭𝐞𝐧𝐭 📝💌"]
    ]
    if str(user_id) == BOT_OWNER_ID:  # ← Yeh line ab sahi hai
        keyboard.append(["👑 Admin Panel", "📊 View Logs"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ✅ Force Join Checker
async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    not_joined = []

    for ch in FORCE_JOIN_CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                not_joined.append(ch)
        except Exception as e:
            logging.warning(f"Join check failed for {ch}: {e}")
            not_joined.append(ch)

    if not_joined:
        text = """
🔒 𝐀𝐜𝐜𝐞𝐬𝐬 𝐋𝐨𝐜𝐤𝐞𝐝!
📢 𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐭𝐡𝐞 𝐫𝐞𝐪𝐮𝐢𝐫𝐞𝐝 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬 𝐟𝐢𝐫𝐬𝐭: 👇

🔹 𝐂𝐢𝐧𝐞𝐏𝐮𝐥𝐬𝐞𝐁𝐨𝐭 𝐎𝐟𝐟𝐢𝐜𝐢𝐚𝐥 ✨🍿
🔹 𝐌𝐨𝐝𝐅𝐥𝐮𝐱 ⚡💠

✅ 𝐓𝐡𝐞𝐧 𝐜𝐥𝐢𝐜𝐤 “𝐈’𝐯𝐞 𝐉𝐨𝐢𝐧𝐞𝐝” 𝐭𝐨 𝐮𝐧𝐥𝐨𝐜𝐤 𝐟𝐮𝐥𝐥 𝐟𝐞𝐚𝐭𝐮𝐫𝐞𝐬.
"""
        buttons = [
            [InlineKeyboardButton("📢✨ 𝐂𝐢𝐧𝐞𝐏𝐮𝐥𝐬𝐞𝐁𝐨𝐭 𝐎𝐟𝐟𝐢𝐜𝐢𝐚𝐥", url="https://t.me/cinepulsebot_official")],
            [InlineKeyboardButton("⚡💠 𝐌𝐨𝐝𝐅𝐥𝐮𝐱", url="https://t.me/modflux_99")],
            [InlineKeyboardButton("✅ I’ve Joined", callback_data="check_joined")]
        ]

        try:
            if update.message:
                await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
            elif update.callback_query:
                await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        except Exception as e:
            logging.error(f"Force join error: {e}")
            handle_bot_block(user_id)

        return False
    return True

# ✅ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Block + Ban Check
    if is_banned(user_id) or is_user_blocked(user_id):
        return

    if not await check_force_join(update, context):
        return

    if not is_user_allowed(update):
        return

    log_user(user_id)

    await context.bot.send_message(
        chat_id=user_id,
        text=(
            "🎬 <b>Welcome to CinePulseBot!</b> 🍿\n"
            "📺 Movies | Series | Anime | K-Dramas\n"
            "📥 HD Download (480p | 720p | 2K/4K)\n\n"
            "❓ Movie not found?\n"
            "😌 Relax & request here — <a href='https://t.me/cinepulsefam'>@cinepulsefam</a> 💌\n\n"
            "🛠 Admin: @Maiivishalhoon"
        ),
        reply_markup=build_menu_keyboard(user_id),
        parse_mode="HTML"
    )

# ✅ I've Joined Button
async def joined_check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    not_joined = []
    for ch in FORCE_JOIN_CHANNELS:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)

    if not_joined:
        text = """
❌ 𝐘𝐨𝐮'𝐫𝐞 𝐬𝐭𝐢𝐥𝐥 𝐧𝐨𝐭 𝐣𝐨𝐢𝐧𝐞𝐝 𝐚𝐥𝐥 𝐫𝐞𝐪𝐮𝐢𝐫𝐞𝐝 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬. 👇

🔹 𝐂𝐢𝐧𝐞𝐏𝐮𝐥𝐬𝐞𝐁𝐨𝐭 𝐎𝐟𝐟𝐢𝐜𝐢𝐚𝐥 📢✨
🔹 𝐌𝐨𝐝𝐅𝐥𝐮𝐱 ⚡💠

📌 𝐏𝐥𝐞𝐚𝐬𝐞 𝐣𝐨𝐢𝐧 𝐚𝐧𝐝 𝐜𝐥𝐢𝐜𝐤 𝐚𝐠𝐚𝐢𝐧.
"""
        buttons = [
            [InlineKeyboardButton("📢✨ 𝐂𝐢𝐧𝐞𝐏𝐮𝐥𝐬𝐞𝐁𝐨𝐭 𝐎𝐟𝐟𝐢𝐜𝐢𝐚𝐥", url="https://t.me/cinepulsebot_official")],
            [InlineKeyboardButton("⚡💠 𝐌𝐨𝐝𝐅𝐥𝐮𝐱", url="https://t.me/modflux_99")],
            [InlineKeyboardButton("✅ I’ve Joined", callback_data="check_joined")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await query.edit_message_text("✅ Access Granted!")
        await start(update, context)

# ✅ Handle All Messages
@block_check
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Block + Ban Check
    if is_banned(user_id) or is_user_blocked(user_id):
        return

    if not await check_force_join(update, context):
        return

    if not is_user_allowed(update):
        return

    log_user(user_id)  # ✅ Ye line incomplete thi, maine fix kar diya

    text = update.message.text

    # Main Categories
    if text == "𝐋𝐚𝐭𝐞𝐬𝐭 𝐑𝐞𝐥𝐞𝐚𝐬𝐞𝐬 ✨🎞️":
        context.user_data["latest_page"] = 1
        await latest.show_latest(update, context, 1)

    elif text == "𝐀𝐧𝐢𝐦𝐞 💀🔥":
        context.user_data["anime_page"] = 1
        await anime.show_anime(update, context, 1)

    elif text == "𝐖𝐞𝐛𝐬𝐞𝐫𝐢𝐞𝐬 🎭📺":
        context.user_data["series_page"] = 1
        await series.show_series(update, context, 1)

    elif text == "𝐊-𝐃𝐫𝐚𝐦𝐚𝐬 💕✨":
        context.user_data["kdrama_page"] = 1
        await kdrama.show_kdrama(update, context, 1)

    elif text == "𝐒𝐨𝐮𝐭𝐡 𝐌𝐨𝐯𝐢𝐞𝐬 💣🔥":
        context.user_data["south_page"] = 1
        await south.show_south(update, context, 1)

    elif text == "𝐇𝐨𝐥𝐥𝐲𝐰𝐨𝐨𝐝 🎬🌍":
        context.user_data["hollywood_page"] = 1
        await hollywood.show_hollywood(update, context, 1)

    elif text == "𝐁𝐨𝐥𝐥𝐲𝐰𝐨𝐨𝐝 🌟🎥":
        context.user_data["bollywood_page"] = 1
        await bollywood.show_bollywood(update, context, 1)

    elif text == "𝐌𝐚𝐫𝐯𝐞𝐥 + 𝐃𝐂 🦸‍♂️⚡":
        context.user_data["marvel_page"] = 1
        await marvel.show_marvel(update, context, 1)

    elif text == "𝟏𝟖+ 𝐂𝐨𝐧𝐭𝐞𝐧𝐭 🔞🔥":
        context.user_data["eighteen_page"] = 1
        await eighteenplus.show_eighteen(update, context, 1)

    elif text == "𝗠𝘂𝗹𝘁𝗶-𝗣𝗮𝗿𝘁 𝗠𝗼𝘃𝗶𝗲𝘀 🎬":
        context.user_data["multipart_page"] = 1
        await multipart.show_multiparts(update, context, 1)

    elif text == "𝐇𝐨𝐰 𝐭𝐨 𝐔𝐬𝐞 📘💡":
        await send_how_to_use(update, context)

    elif text == "𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐚 𝐂𝐨𝐧𝐭𝐞𝐧𝐭 📝💌":
        await handle_request(update, context)

    elif text == "𝐒𝐞𝐚𝐫𝐜𝐡 🔍🧠":
        await update.message.reply_text("🔍 Please type the name of the movie or series to search.")

    elif text == "🏠 Main Menu":
        context.user_data.clear()
        await update.message.reply_text("🏠 Back to main menu", reply_markup=build_menu_keyboard(user_id))

    elif text == "👑 Admin Panel" and str(user_id) == BOT_OWNER_ID:
        await admin_panel(update, context)

    else:
        # Fallback: Pagination buttons or Search
        for section in [
            "anime", "series", "latest", "kdrama", "south",
            "hollywood", "bollywood", "marvel", "eighteen", "multipart"
        ]:
            if context.user_data.get(f"{section}_page"):
                handler = getattr(globals()[section], f"handle_{section}_buttons")
                await handler(update, context)
                return

        # If not in known section, perform search
        await handle_search(update, context)

# ✅ Search Text Handler
@block_check
async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        query = update.message.text.strip()
        username = update.effective_user.username or f"user_{user_id}"
        log_search(query, user_id, username)

        result = search_movie(query)

        if not result:
            await update.message.reply_text(
                f"⚠️ No result returned for: <code>{query}</code>", parse_mode="HTML"
            )
            return

        title, poster, caption = result
        if poster:
            await update.message.reply_photo(photo=poster, caption=caption, parse_mode="HTML")
        else:
            await update.message.reply_text(caption, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        logging.error(f"Search error: {e}")
        handle_bot_block(user_id)

async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != BOT_OWNER_ID:
        return

    click_logs = get_click_logs()
    search_logs = get_search_logs()

    combined = "🖱️ <b>Recent Click Logs</b>:\n" + "\n".join(click_logs[-30:]) or "No clicks logged yet."
    combined += "\n\n🔍 <b>Recent Search Logs</b>:\n" + "\n".join(search_logs[-30:]) or "No searches logged yet."

    try:
        # Also send file
        with open("all_logs.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(click_logs + [""] + search_logs))

        await update.message.reply_document(
            document=open("all_logs.txt", "rb"),
            filename="cinepulse_logs.txt",
            caption="📁 Full Logs Attached (Clicks + Searches)"
        )

        await update.message.reply_text(combined, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error sending logs: {e}")
        await update.message.reply_text("❌ Error loading logs.")

@admin_only
async def clear_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /clearlogs command received!")  # ← Add this line
    clear_click_logs()
    clear_search_logs()
    await update.message.reply_text("✅ Click and Search logs cleared!")

# ✅ Run Bot
if __name__ == "__main__":
    print("🚀 Bot is starting...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(joined_check_callback, pattern="check_joined"))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^(show_|toggle:)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.User(BOT_OWNER_ID), handle_admin_id))
    app.add_handler(MessageHandler(filters.Regex("^📊 View Logs$"), view_logs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    app.add_handler(CommandHandler("clearlogs", clear_logs))

    print("✅ CinePulseBot is running...")
    app.run_polling()