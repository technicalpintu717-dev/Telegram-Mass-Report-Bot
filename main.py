import os
import requests
import random
import time
import threading
from faker import Faker
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# --- CONFIG ---
TOKEN = os.getenv("TOKEN", "8648448255:AAFnXq9eLXH9B67W8_im79PTjEyDIW7K6G8")
fake = Faker()
USERNAME_STATE = 1

# --- FILE PATH LOADER ---
def get_resource_file(filename):
    """Pehle attached_assets folder check karta hai fir root"""
    paths = [f"attached_assets/{filename}", filename]
    for path in paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
    return []

# --- CORE ENGINE ---
def send_report_request(payload, proxy=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://telegram.org/support"
    }
    proxies = None
    if proxy:
        # SOCKS4 Support for STAR.txt
        proxies = {'http': f'socks4://{proxy}', 'https': f'socks4://{proxy}'}
    
    try:
        res = requests.post("https://telegram.org/support", data=payload, headers=headers, proxies=proxies, timeout=12)
        return "Thank you" in res.text or res.status_code == 200
    except:
        return False

def report_worker(chat_id, username, bot):
    # Files loading from your structure
    reports = get_resource_file("report.txt")
    proxies = get_resource_file("STAR.txt") or get_resource_file("socks4_proxies.txt")
    
    if not reports:
        bot.send_message(chat_id, "❌ **Error:** `report.txt` nahi mili!")
        return

    status_msg = bot.send_message(chat_id=chat_id, text=f"⚡ **ALPHA ENGINE INITIATED**\n🎯 Target: `@{username}`", parse_mode="Markdown")
    
    success_count = 0
    p_idx = 0
    total = len(reports)

    for i, msg in enumerate(reports):
        # Alpha logic: placeholder replace
        final_msg = msg.replace("{@username}", f"@{username}").replace("@username", f"@{username}")
        
        payload = {
            "message": final_msg,
            "legal_name": fake.name(),
            "email": f"{fake.user_name()}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}",
            "phone": '7' + ''.join([str(random.randint(0, 9)) for _ in range(9)]),
            "setln": ""
        }

        current_proxy = proxies[p_idx] if proxies else None
        
        if send_report_request(payload, current_proxy):
            success_count += 1
        
        if proxies:
            p_idx = (p_idx + 1) % len(proxies)

        # Progress update every 2 reports
        if (i + 1) % 2 == 0 or (i + 1) == total:
            percent = int(((i + 1) / total) * 100)
            bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
            try:
                status_msg.edit_text(
                    f"🛡 **REPORTING STATUS**\n"
                    f"🎯 Target: `@{username}`\n"
                    f"🌐 Proxy: `{current_proxy if current_proxy else 'Direct'}`\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"[{bar}] {percent}%\n✅ Success: `{success_count}/{i+1}`",
                    parse_mode="Markdown"
                )
            except: pass
        
        time.sleep(1.8)

    bot.send_message(chat_id, f"✅ **MISSION COMPLETE**\nTarget: `@{username}`\nReports Sent: `{success_count}`")

# --- HANDLERS ---
def start(update, context):
    update.message.reply_text("💀 **ALPHA REPORTER READY**\nTarget username bhejien (bina @ ke):")
    return USERNAME_STATE

def handle_target(update, context):
    username = update.message.text.strip().lstrip('@')
    update.message.reply_text(f"🚀 Sequence started for `@{username}`. Engine is running in background...")
    # Multi-user thread start
    threading.Thread(target=report_worker, args=(update.effective_chat.id, username, context.bot)).start()
    return USERNAME_STATE

def main():
    updater = Updater(TOKEN, use_context=True, workers=32)
    dp = updater.dispatcher
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={USERNAME_STATE: [MessageHandler(Filters.text & ~Filters.command, handle_target)]},
        fallbacks=[]
    )
    dp.add_handler(conv)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
