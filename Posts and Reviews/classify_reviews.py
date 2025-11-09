#!/usr/bin/env python3
"""
create_sample_data.py
Creates a sample tmobile_reviews.json file with the proper nested structure.
Run this to generate test data in the data/ folder.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import random

# Sample data for generation
TEXAS_CITIES = ["Dallas", "Houston", "Austin", "San Antonio", "Fort Worth", "Plano", "Arlington"]
CALIFORNIA_CITIES = ["Los Angeles", "San Francisco", "San Diego", "Sacramento", "San Jose"]

POSITIVE_REVIEWS = [
    {"title": "Amazing 5G speeds!", "text": "T-Mobile's 5G is incredibly fast. Downloaded a movie in seconds!"},
    {"title": "Great customer service", "text": "The staff was helpful and knowledgeable. Fixed my issue quickly."},
    {"title": "Best decision ever", "text": "Switched from Verizon and loving the coverage and price."},
    {"title": "Fast data speeds", "text": "Upload and download speeds are excellent in my area."},
    {"title": "Reliable network", "text": "No dropped calls, stable connection throughout the day."},
]

NEGATIVE_REVIEWS = [
    {"title": "Network keeps dropping", "text": "Constantly losing signal and calls drop frequently. Very frustrating."},
    {"title": "Terrible coverage", "text": "Dead zones everywhere. Can't even load basic websites."},
    {"title": "Poor customer service", "text": "Staff was rude and unhelpful. Waited an hour just to be dismissed."},
    {"title": "Billing issues", "text": "Charged extra fees that weren't explained. Bill is confusing."},
    {"title": "Slow speeds", "text": "Network is congested. Can barely stream videos."},
]

NEUTRAL_REVIEWS = [
    {"title": "Average experience", "text": "Nothing special. Service works but nothing to write home about."},
    {"title": "Okay coverage", "text": "Coverage is decent in most areas, spotty in some."},
    {"title": "Standard service", "text": "Got what I expected. No surprises, good or bad."},
    {"title": "Mixed feelings", "text": "Good price but coverage could be better."},
    {"title": "It works", "text": "Does the job. Had better, had worse."},
]

def generate_reviews(num_positive=3, num_negative=3, num_neutral=2):
    """Generate random reviews with dates."""
    reviews = []
    base_date = datetime.now() - timedelta(days=30)
    
    # Add positive reviews
    for i in range(num_positive):
        review = random.choice(POSITIVE_REVIEWS).copy()
        review["rating"] = random.randint(4, 5)
        review["sentiment"] = "positive"
        review["date"] = (base_date + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
        reviews.append(review)
    
    # Add negative reviews
    for i in range(num_negative):
        review = random.choice(NEGATIVE_REVIEWS).copy()
        review["rating"] = random.randint(1, 2)
        review["sentiment"] = "negative"
        review["date"] = (base_date + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
        reviews.append(review)
    
    # Add neutral reviews
    for i in range(num_neutral):
        review = random.choice(NEUTRAL_REVIEWS).copy()
        review["rating"] = 3
        review["sentiment"] = "neutral"
        review["date"] = (base_date + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
        reviews.append(review)
    
    return reviews

def create_tmobile_dataset():
    """Create the nested T-Mobile reviews dataset structure."""
    dataset = {
        "dataset_name": "T-Mobile Store Reviews",
        "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_states": 2,
        "states": []
    }
    
    # Texas stores
    texas_stores = []
    for i, city in enumerate(TEXAS_CITIES[:5], 1):  # First 5 cities
        store = {
            "store_id": f"TX-{city[:3].upper()}-{i:03d}",
            "store_name": f"T-Mobile {city} Store",
            "address": f"{random.randint(100, 9999)} Main St, {city}, TX {75000 + i}",
            "city": city,
            "state": "Texas",
            "reviews": generate_reviews(
                num_positive=random.randint(2, 5),
                num_negative=random.randint(2, 4),
                num_neutral=random.randint(1, 3)
            )
        }
        texas_stores.append(store)
    
    # Group Texas stores by city
    texas_cities = {}
    for store in texas_stores:
        city = store["city"]
        if city not in texas_cities:
            texas_cities[city] = []
        texas_cities[city].append(store)
    
    texas_state = {
        "state": "Texas",
        "cities": [
            {
                "city": city,
                "stores": stores
            }
            for city, stores in texas_cities.items()
        ]
    }
    
    # California stores
    california_stores = []
    for i, city in enumerate(CALIFORNIA_CITIES[:4], 1):  # First 4 cities
        store = {
            "store_id": f"CA-{city[:3].upper()}-{i:03d}",
            "store_name": f"T-Mobile {city} Store",
            "address": f"{random.randint(100, 9999)} Market St, {city}, CA {90000 + i}",
            "city": city,
            "state": "California",
            "reviews": generate_reviews(
                num_positive=random.randint(2, 5),
                num_negative=random.randint(2, 4),
                num_neutral=random.randint(1, 3)
            )
        }
        california_stores.append(store)
    
    # Group California stores by city
    california_cities = {}
    for store in california_stores:
        city = store["city"]
        if city not in california_cities:
            california_cities[city] = []
        california_cities[city].append(store)
    
    california_state = {
        "state": "California",
        "cities": [
            {
                "city": city,
                "stores": stores
            }
            for city, stores in california_cities.items()
        ]
    }
    
    dataset["states"] = [texas_state, california_state]
    
    return dataset

def main():
    """Main function to create the JSON file."""
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    output_file = data_dir / "tmobile_reviews.json"
    
    print("=" * 60)
    print("🏗️  Creating T-Mobile Reviews Dataset")
    print("=" * 60)
    
    # Generate dataset
    dataset = create_tmobile_dataset()
    
    # Count total reviews
    total_reviews = 0
    total_stores = 0
    for state in dataset["states"]:
        for city in state["cities"]:
            for store in city["stores"]:
                total_stores += 1
                total_reviews += len(store["reviews"])
    
    print(f"\n📊 Generated Dataset:")
    print(f"   States: {len(dataset['states'])}")
    print(f"   Cities: {sum(len(s['cities']) for s in dataset['states'])}")
    print(f"   Stores: {total_stores}")
    print(f"   Reviews: {total_reviews}")
    
    # Write to file
    output_file.write_text(
        json.dumps(dataset, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    print(f"\n✅ Successfully created: {output_file.resolve()}")
    print(f"\n💡 You can now run your sentiment analysis on this file!")
    print(f"   The file structure matches the expected format:")
    print(f"   dataset['states'][i]['cities'][j]['stores'][k]['reviews']")
    print("=" * 60)

if __name__ == "__main__":
    main()