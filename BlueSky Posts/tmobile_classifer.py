# tmobile_classifier.py
import os
import re
import json
import time
import ssl
import certifi
from datetime import datetime
from atproto import Client
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────
#  SETUP
# ──────────────────────────────────────────────────────────────
context = ssl.create_default_context(cafile=certifi.where())
load_dotenv()

USERNAME = os.getenv('BLUESKY_USERNAME')
PASSWORD = os.getenv('BLUESKY_PASSWORD')

# always save in same folder as this script
BASE_DIR = os.path.dirname(__file__)
LOG_FILE = os.path.join(BASE_DIR, "tmobile_log.txt")

# ──────────────────────────────────────────────────────────────
#  CATEGORY DEFINITIONS
# ──────────────────────────────────────────────────────────────
CATEGORIES = {
    # General brand mentions
    "tmobile": [
        "tmobile", "t-mobile", "t mobile", "tmobileus", "tmo", "tmob",
        "team magenta", "uncarrier", "t mobile coverage"
    ],

    # T-Mobile Tuesdays and promos
    "tmobile_tuesday": [
        "tmobile tuesday", "t-mobile tuesday", "t mobile tuesday",
        "tuesday deal", "tuesday rewards", "tuesday freebie", "tuesday promo"
    ],

    # Plans & pricing tiers
    "tmobile_plans": [
        "magenta max", "magenta plan", "essentials plan", "go5g", "go5g next", "go5g plus",
        "simple choice", "one plan", "unlimited plan", "family plan", "5g plan", "prepaid plan",
        "postpaid plan", "switch to tmobile", "tmobile upgrade"
    ],

    # Products & services
    "tmobile_products": [
        "tmobile home internet", "home internet", "internet gateway", "5g home internet",
        "tmobile money", "tmobile travel", "tmobile syncup", "tmobile hotspot",
        "tmobile coverage map", "international pass", "roaming", "tmobile business",
        "tmobile enterprise", "tmobile phone", "tmobile sim", "tmobile esim",
        "tmobile store", "tmobile support", "tmobile app"
    ],

    # 🔹 Devices & bundles
    "tmobile_devices": [
        "iphone 15", "iphone 14", "samsung galaxy", "pixel 8", "tmobile trade in",
        "tmobile upgrade deal", "tmobile discount", "tmobile bundle",
        "tmobile free phone", "tmobile watch plan", "tmobile tablet plan"
    ]
}

# ──────────────────────────────────────────────────────────────
#  LOGGING
# ──────────────────────────────────────────────────────────────
def log_message(msg: str):
    """Append timestamped log entries to tmobile_log.txt."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {msg}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(entry)
    print(entry.strip())

# ──────────────────────────────────────────────────────────────
#  FETCH POSTS
# ──────────────────────────────────────────────────────────────
def fetch_posts(username, password, search_terms, limit=50):
    """Search the Bluesky network for posts matching any keyword."""
    posts = []
    try:
        client = Client()
        client.login(username, password)

        for term in search_terms:
            search = client.app.bsky.feed.search_posts({'q': term, 'limit': limit})
            for post in search.posts:
                posts.append({
                    'text': post.record.text,
                    'created_at': post.record.created_at,
                    'author': post.author.handle,
                    'uri': post.uri
                })

    except Exception as e:
        log_message(f"❌ Error fetching posts: {e}")
    return posts

# ──────────────────────────────────────────────────────────────
#  FILE HELPERS
# ──────────────────────────────────────────────────────────────
def load_existing_posts(filename):
    """Load posts already saved to avoid duplicates."""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("posts", [])
    except (json.JSONDecodeError, OSError):
        return []

def save_posts(posts, filename):
    """Append only unique posts to existing JSON file."""
    existing = load_existing_posts(filename)
    existing_uris = {p["uri"] for p in existing}

    # keep only new posts
    new_posts = [p for p in posts if p["uri"] not in existing_uris]
    if not new_posts:
        log_message(f"⚠️ No new posts for {os.path.basename(filename)}.")
        return

    combined = existing + new_posts
    data = {
        "last_updated": datetime.utcnow().isoformat(),
        "total_posts": len(combined),
        "posts": combined
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    log_message(f"💾 Added {len(new_posts)} new → {os.path.basename(filename)} (Total: {len(combined)})")

# ──────────────────────────────────────────────────────────────
#  CLASSIFICATION
# ──────────────────────────────────────────────────────────────
def classify_and_save(posts):
    """Categorize posts by keyword group and save to JSON."""
    for category, keywords in CATEGORIES.items():
        file_path = os.path.join(BASE_DIR, f"{category}_posts.json")
        category_posts = [
            post for post in posts
            if any(keyword in post["text"].lower() for keyword in keywords)
        ]
        if category_posts:
            save_posts(category_posts, file_path)
        else:
            log_message(f"⚠️ No new matches for category '{category}' this run.")

# ──────────────────────────────────────────────────────────────
#  MAIN LOOP
# ──────────────────────────────────────────────────────────────
def main_loop():
    username = USERNAME
    password = PASSWORD

    if not username or not password:
        print("⚠️ Missing Bluesky credentials in .env file.")
        return

    log_message("🚀 Starting T-Mobile Post Classifier (updates every 10 minutes)...")

    while True:
        all_posts = []
        for keywords in CATEGORIES.values():
            all_posts += fetch_posts(username, password, keywords)

        # remove duplicates globally
        seen_uris = set()
        unique_posts = []
        for post in all_posts:
            if post["uri"] not in seen_uris:
                seen_uris.add(post["uri"])
                unique_posts.append(post)

        log_message(f"✅ Collected {len(unique_posts)} total posts this cycle.")
        classify_and_save(unique_posts)

        # summary
        summary = ", ".join([
            f"{cat}: {len(load_existing_posts(os.path.join(BASE_DIR, f'{cat}_posts.json')))}"
            for cat in CATEGORIES.keys()
        ])
        log_message(f"📊 Cycle summary → {summary}")

        log_message("⏳ Sleeping for 10 minutes...\n")
        time.sleep(600)  # 10 minutes


if __name__ == "__main__":
    main_loop()
