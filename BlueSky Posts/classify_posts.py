# tmobile_auto_collector.py

import re
import json
import ssl
import certifi
import time
from atproto import Client
from dotenv import load_dotenv
from datetime import datetime
import os

# SSL and environment setup
context = ssl.create_default_context(cafile=certifi.where())
load_dotenv()

USERNAME = os.getenv('BLUESKY_USERNAME')
PASSWORD = os.getenv('BLUESKY_PASSWORD')
OUTPUT_FILE = 'tmobile_posts.json'


def preprocess_text(text):
    """Clean and lowercase text."""
    if not text:
        return ""
    text = str(text).lower()
    return re.sub(r'[^a-zA-Z\s]', '', text)


def fetch_tmobile_related_posts(username, password, search_terms=None, limit=50):
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

        print(f"Collected {len(posts)} posts mentioning T-Mobile.")
        return posts

    except Exception as e:
        print(f" Error fetching posts: {e}")
        return []


def load_existing_posts(filename):
    """Load existing posts from JSON to prevent duplicates."""
    if not os.path.exists(filename):
        return []
    with open(filename, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            return data.get('posts', [])
        except json.JSONDecodeError:
            return []


def save_to_json_append(new_posts, filename=OUTPUT_FILE):
    """Append new posts without duplicating."""
    try:
        existing_posts = load_existing_posts(filename)

        # Avoid duplicates by URI
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

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"Added {len(unique_new_posts)} new posts. Total now: {len(all_posts)}")
    except Exception as e:
        print(f" Error saving JSON: {e}")


def main_loop():
    username = USERNAME
    password = PASSWORD

    if not username or not password:
        print("Missing Bluesky credentials in .env file.")
        return

    print("Starting T-Mobile Post Collector (updates every 10 minutes)...")

    while True:
        posts = fetch_tmobile_related_posts(username, password)
        if posts:
            save_to_json_append(posts)
        else:
            print("No relevant posts fetched this cycle.")

        print(" Sleeping for 5 minutes...\n")
        time.sleep(300)


if __name__ == "__main__":
    main_loop()
