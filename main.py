#!/usr/bin/env python3
import asyncio
import hashlib
import json
import os
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
import requests

# ============================================================
# CONFIG
# ============================================================
BOT_TOKEN = "8710953134:AAE9mINQB8kNGRKn4tQS4oaoa57-y1c1HLs"
CHAT_ID = "1079604938"
API_ID = 38014862
API_HASH = "564041be554578ba15eacec6b62707b6"
CHECK_INTERVAL = 300

# Telegram channels to monitor
TG_CHANNELS = [
    "megatron_ron",
    "SM_News_24h",
    "signalsfc",
    "geopolitics_prime",
]

# News websites to scan
NEWS_SOURCES = [
    {"name": "FXStreet Gold", "url": "https://www.fxstreet.com/markets/commodities/metals/gold"},
    {"name": "Investing XAUUSD", "url": "https://www.investing.com/currencies/xau-usd-news"},
    {"name": "CNBC Markets", "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html"},
]

KEYWORDS = {
    "🔴 IRAN WAR": ["iran", "hormuz", "strait", "nuclear", "tehran", "hezbollah", "houthi", "middle east war"],
    "📢 TRUMP POST": ["trump post", "truth social", "trump says", "trump warns", "trump announces", "trump threatens"],
    "🟡 XAUUSD GOLD": ["gold price", "xauusd", "gold surges", "gold falls", "gold rally", "bullion", "silver"],
    "📈 US100 NASDAQ": ["nasdaq", "us100", "tech stocks", "ndx", "s&p 500", "wall street"],
    "🛢️ OIL IMPACT": ["brent crude", "oil price", "wti", "crude oil", "oil surge", "opec"],
}

SEEN_FILE = "seen_news.json"

# ============================================================
# HELPERS
# ============================================================
def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print(f"✅ Alert sent")
        else:
            print(f"❌ Failed: {r.text}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def check_keywords(text):
    found = []
    text = text.lower()
    for category, words in KEYWORDS.items():
        for word in words:
            if word in text:
                found.append(category)
                break
    return list(set(found))

def make_hash(text):
    return hashlib.md5(text[:500].encode()).hexdigest()

def fetch_news(source):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MarketBot/1.0)"}
    try:
        r = requests.get(source["url"], headers=headers, timeout=15)
        return r.text.lower()
    except Exception as e:
        print(f"⚠️ Failed to fetch {source['name']}: {e}")
        return ""

# ============================================================
# TELEGRAM CHANNEL SCANNER
# ============================================================
async def scan_tg_channels(client, seen_hashes):
    alerts_sent = 0
    for channel in TG_CHANNELS:
        try:
            entity = await client.get_entity(channel)
            history = await client(GetHistoryRequest(
                peer=entity,
                limit=10,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            for msg in history.messages:
                if not msg.message:
                    continue
                text = msg.message
                msg_hash = make_hash(text)
                if msg_hash in seen_hashes:
                    continue
                seen_hashes.add(msg_hash)
                matched = check_keywords(text)
                if matched:
                    categories = "\n".join(matched)
                    preview = text[:200] + "..." if len(text) > 200 else text
                    alert = (
                        f"📡 <b>TELEGRAM CHANNEL ALERT</b>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"📢 Channel: <b>@{channel}</b>\n"
                        f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
                        f"<b>Detected:</b>\n{categories}\n\n"
                        f"💬 <i>{preview}</i>\n\n"
                        f"🔗 <a href='https://t.me/{channel}'>Open Channel</a>"
                    )
                    send_telegram(alert)
                    alerts_sent += 1
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"⚠️ Failed to scan @{channel}: {e}")
    save_seen(seen_hashes)
    return alerts_sent

# ============================================================
# MAIN
# ============================================================
async def main():
    seen_hashes = load_seen()

    # Start Telethon client
    client = TelegramClient("session", API_ID, API_HASH)
    await client.start()

    send_telegram(
        "🤖 <b>MarketAlertBot v2 Started!</b>\n\n"
        "📡 Now scanning Telegram channels:\n"
        "• @megatron_ron\n"
        "• @SM_News_24h\n"
        "• @signalsfc\n"
        "• @geopolitics_prime\n\n"
        "📰 Plus news sites every 5 min\n"
        f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print("🚀 Bot v2 started!")

    while True:
        print(f"\n🔍 Scanning at {datetime.now().strftime('%H:%M:%S')}...")

        # Scan news websites
        for source in NEWS_SOURCES:
            content = fetch_news(source)
            if not content:
                continue
            content_hash = make_hash(content)
            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)
            matched = check_keywords(content)
            if matched:
                categories = "\n".join(matched)
                msg = (
                    f"🚨 <b>MARKET ALERT</b>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"📰 Source: <b>{source['name']}</b>\n"
                    f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    f"<b>Detected:</b>\n{categories}\n\n"
                    f"🔗 <a href='{source['url']}'>Read Full News</a>"
                )
                send_telegram(msg)
                await asyncio.sleep(2)

        # Scan Telegram channels
        await scan_tg_channels(client, seen_hashes)
        save_seen(seen_hashes)

        print(f"⏳ Next scan in 5 minutes...")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
