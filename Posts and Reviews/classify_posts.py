import re
import json
import ssl
import certifi
import time
from atproto import Client
from dotenv import load_dotenv
from datetime import datetime
import os

# ==========================
# ⚙️ Setup
# ==========================
context = ssl.create_default_context(cafile=certifi.where())
load_dotenv()

USERNAME = os.getenv('BLUESKY_USERNAME')
PASSWORD = os.getenv('BLUESKY_PASSWORD')

# ✅ Save JSON inside the Data folder (relative to project root)
OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Data', 'tmobile_posts.json'))

# ==========================
# 🧹 Helper: Text Preprocessing
# ==========================
def preprocess_text(text):
    """Clean and lowercase text."""
    if not text:
        return ""
    text = str(text).lower()
    return re.sub(r'[^a-zA-Z\s]', '', text)

# ==========================
# 🔍 Fetch Posts from Bluesky
# ==========================
def fetch_tmobile_related_posts(username, password, search_terms=None, limit=50):
    """Fetch posts mentioning T-Mobile-related keywords."""
    if search_terms is None:
        search_terms = ["tmobile", "t-mobile", "t mobile", "tmobile tuesday", "tmo"]

    try:
        client = Client()
        client.login(username, password)
        posts = []

        for term in search_terms:
            search = client.app.bsky.feed.search_posts({'q': term, 'limit': limit})
            for post in search.posts:
                posts.append({
                    'text': post.record.text,
                    'created_at': post.record.created_at,
                    'author': post.author.handle,
                    'uri': post.uri
                })

        print(f"✅ Collected {len(posts)} posts mentioning T-Mobile.")
        return posts

    except Exception as e:
        print(f"❌ Error fetching posts: {e}")
        return []

# ==========================
# 📂 Load Existing Data
# ==========================
def load_existing_posts(filename):
    """Load existing posts from JSON to prevent duplicates."""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('posts', [])
    except json.JSONDecodeError:
        print("⚠️ JSON decode error — starting with empty data.")
        return []
    except Exception as e:
        print(f"⚠️ Error reading {filename}: {e}")
        return []

# ==========================
# 💾 Save or Append Posts
# ==========================
def save_to_json_append(new_posts, filename=OUTPUT_FILE):
    """Append new posts without duplicating existing ones."""
    try:
        existing_posts = load_existing_posts(filename)
        existing_uris = {post['uri'] for post in existing_posts}
        unique_new_posts = [p for p in new_posts if p['uri'] not in existing_uris]

        if not unique_new_posts:
            print("⚠️ No new posts found.")
            return

        all_posts = existing_posts + unique_new_posts
        data = {
            "last_updated": datetime.utcnow().isoformat(),
            "total_posts": len(all_posts),
            "posts": all_posts
        }

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"💾 Added {len(unique_new_posts)} new posts. Total now: {len(all_posts)}")
        print(f"📁 Updated file: {filename}")

    except Exception as e:
        print(f"❌ Error saving JSON: {e}")

# ==========================
# 🔁 Main Loop
# ==========================
def main_loop():
    """Continuously fetch and save T-Mobile related posts."""
    username = USERNAME
    password = PASSWORD

    if not username or not password:
        print("❌ Missing Bluesky credentials in .env file.")
        return

    print("🚀 Starting T-Mobile Post Collector (updates every 5 minutes)...")
    print(f"📁 Output file: {OUTPUT_FILE}\n")

    while True:
        posts = fetch_tmobile_related_posts(username, password)
        if posts:
            save_to_json_append(posts)
        else:
            print("⚠️ No relevant posts fetched this cycle.")
        print("⏳ Sleeping for 5 minutes...\n")
        time.sleep(300)

# ==========================
# ▶️ Run Script
# ==========================
if __name__ == "__main__":
    main_loop()
