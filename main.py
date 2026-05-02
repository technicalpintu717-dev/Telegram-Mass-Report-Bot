import os
import requests
import random
import time
import re
import threading
from faker import Faker
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler

# --- CONFIGURATION ---
TOKEN = os.getenv("TOKEN", "8648448255:AAFnXq9eLXH9B67W8_im79PTjEyDIW7K6G8")
CHANNEL_ID = -1003823759691
CHANNEL_LINK = "https://t.me/+0Qj5AqURgcw2ZmFl"

fake = Faker()
USERNAME_STATE = 1

# --- CORE FUNCTIONS ---
def load_reports():
    """Default report messages agar file na ho"""
    return [
        "This user @username is violating Telegram terms.",
        "Report @username for spamming group links.",
        "This account @username is sharing harmful content.",
        "Impersonation and fake account: @username",
        "Abusive behavior detected: @username"
    ]

def is_valid_username(username):
    """Check if Telegram user exists"""
    try:
        response = requests.get(f"https://t.me/{username}", timeout=5)
        return "tgme_page_title" in response.text
    except: return False

def generate_report_data(username, message):
    """Fake user data for reporting"""
    name = fake.name()
    email = f"{fake.user_name()}{random.randint(10,99)}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}"
    number = '9' + ''.join([str(random.randint(0, 9)) for _ in range(9)])
    final_msg = message.replace("@username", f"@{username}")
    return {"message": final_msg, "legal_name": name, "email": email, "phone": number, "setln": ""}

def send_to_support(data):
    """Post to Telegram Support"""
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://telegram.org/support"}
    try:
        res = requests.post("https://telegram.org/support", data=data, headers=headers, timeout=10)
        return res.status_code == 200 or "Thank you" in res.text
    except: return False

def check_subscription(update, context):
    """Check if user joined the channel"""
    user_id = update.effective_user.id
    try:
        member = context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return True # Fallback agar channel access na ho

# --- MULTI-USER WORKER ---
def report_worker(chat_id, username, bot):
    reports = load_reports()
    total = len(reports)
    success_count = 0
    
    status_msg = bot.send_message(chat_id=chat_id, text="🚀 **Initializing Engine...**", parse_mode="Markdown")

    for i, msg in enumerate(reports):
        data = generate_report_data(username, msg)
        success = send_to_support(data)
        if success: success_count += 1
        
        # Update progress every 2 reports
        if (i + 1) % 2 == 0 or (i + 1) == total:
            percent = int(((i + 1) / total) * 100)
            bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
            try:
                status_msg.edit_text(
                    f"🛡 **REPORTING...**\nTarget: `@{username}`\n"
                    f"[{bar}] {percent}%\n✅ Success: `{success_count}/{i+1}`",
                    parse_mode="Markdown"
                )
            except: pass
        time.sleep(1.5)

    bot.send_message(chat_id, f"✅ **TASK FINISHED**\nTarget: `@{username}`\nSent: `{success_count}`")

# --- HANDLERS ---
def start(update: Update, context: CallbackContext):
    if not check_subscription(update, context):
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)]]
        update.message.reply_text("🛑 **JOIN CHANNEL FIRST!**", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    update.message.reply_text("🛡 **ACCESS GRANTED**\nTarget ka **username** bhejien (without @):")
    return USERNAME_STATE

def handle_target(update: Update, context: CallbackContext):
    username = update.message.text.strip().lstrip('@')
    chat_id = update.effective_chat.id

    if not is_valid_username(username):
        update.message.reply_text("❌ Target not found.")
        return USERNAME_STATE

    update.message.reply_text("✅ Target Verified. Task started in background.")
    
    # threading ensures multiple users can report at same time
    threading.Thread(target=report_worker, args=(chat_id, username, context.bot)).start()
    return USERNAME_STATE

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

# --- MAIN ---
def main():
    updater = Updater(TOKEN, use_context=True, workers=32)
    dp = updater.dispatcher

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={USERNAME_STATE: [MessageHandler(Filters.text & ~Filters.command, handle_target)]},
        fallbacks=[CommandHandler('cancel', cancel)],
        per_user=True
    )
    dp.add_handler(conv)

    updater.start_polling()
    print(">>> Bot is running on Railway!")
    updater.idle()

if __name__ == "__main__":
    main()
