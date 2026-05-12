#!/usr/bin/env python3
import requests
import time
import hashlib
import json
import os
from datetime import datetime

8710953134:AAE9mINQB8kNGRKn4tQS4oaoa57-y1c1HLs
CHAT_ID = "1079604938"
CHECK_INTERVAL = 300

NEWS_SOURCES = [
    {"name": "FXStreet Gold", "url": "https://www.fxstreet.com/markets/commodities/metals/gold"},
    {"name": "Investing XAUUSD", "url": "https://www.investing.com/currencies/xau-usd-news"},
    {"name": "Reuters Markets", "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"name": "CNBC Markets", "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html"},
]

KEYWORDS = {
    "🔴 IRAN WAR": ["iran", "hormuz", "strait", "nuclear", "tehran", "hezbollah", "houthi", "middle east war", "operation epic fury"],
    "📢 TRUMP POST": ["trump post", "truth social", "trump says", "trump warns", "trump tweets", "trump announces", "trump threatens"],
    "🟡 XAUUSD GOLD": ["gold price", "xauusd", "gold surges", "gold falls", "gold rally", "bullion", "gold hits", "gold forecast"],
    "📈 US100 NASDAQ": ["nasdaq", "us100", "tech stocks", "ndx", "s&p 500", "wall street", "stock market rally", "market crash"],
    "🛢️ OIL IMPACT": ["brent crude", "oil price", "wti", "crude oil", "oil surge", "opec", "energy market"],
}

SEEN_FILE = "seen_news.json"

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

def fetch_news(source):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MarketBot/1.0)"}
    try:
        r = requests.get(source["url"], headers=headers, timeout=15)
        return r.text.lower()
    except Exception as e:
        print(f"⚠️ Failed to fetch {source['name']}: {e}")
        return ""

def check_keywords(text):
    found = []
    for category, words in KEYWORDS.items():
        for word in words:
            if word in text:
                found.append(category)
                break
    return list(set(found))

def make_hash(text):
    return hashlib.md5(text[:500].encode()).hexdigest()

def run_bot():
    seen_hashes = load_seen()
    send_telegram(
        "🤖 <b>MarketAlertJeffBot Started!</b>\n\n"
        "Scanning every 5 minutes for:\n"
        "🔴 Iran conflict news\n"
        "📢 Trump posts\n"
        "🟡 XAUUSD Gold moves\n"
        "📈 US100/Nasdaq impact\n"
        "🛢️ Oil price alerts\n\n"
        f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print("🚀 Bot started. Scanning every 5 minutes...")

    while True:
        print(f"\n🔍 Scanning at {datetime.now().strftime('%H:%M:%S')}...")
        alerts_sent = 0

        for source in NEWS_SOURCES:
            content = fetch_news(source)
            if not content:
                continue
            content_hash = make_hash(content)
            if content_hash in seen_hashes:
                print(f"  ⏭️ No new content from {source['name']}")
                continue
            seen_hashes.add(content_hash)
            save_seen(seen_hashes)
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
                alerts_sent += 1
                time.sleep(2)

        if alerts_sent == 0:
            print("  ✅ No new alerts this cycle")
        print(f"⏳ Next scan in 5 minutes...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    run_bot()
