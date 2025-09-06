from apify_client import ApifyClient
import sys
import os
import json

# Add the root directory to Python path to import admin
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from admin import APIFY_KEY

# Initialize the ApifyClient with your Apify API token
client = ApifyClient(APIFY_KEY)

# Store the input URL for grouping - will be dynamically updated by main.py
instagram_url = "https://wahttps://x.com/elonmuskww.instagram.com/su.mitra_sa/https://www.instagram.com/su.mitra_sa/"
URL_GROUP = instagram_url  # Store the input URL for grouping

# Prepare the Actor input
run_input = {
    "username": [instagram_url],
    "resultsLimit": 50,  # Keep max results for better content selection
    "onlyPostsNewerThan": "7 days"  # Keep 7 days as required
}

# Run the Actor and wait for it to finish
run = client.actor("apify/instagram-reel-scraper").call(run_input=run_input)

# Fetch and save Actor results from the run's dataset to JSON file
data = []
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    # Add URL_GROUP to each item
    item['URL_GROUP'] = URL_GROUP
    data.append(item)

# Save data to temp_data.json (append mode)
temp_data_file = os.path.join(os.path.dirname(__file__), "..", "temp_data.json")

# Load existing temp data if it exists
existing_data = []
if os.path.exists(temp_data_file):
    try:
        with open(temp_data_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        existing_data = []

# Append new data to existing data
existing_data.extend(data)

# Save all data back to temp_data.json
with open(temp_data_file, "w", encoding="utf-8") as f:
    json.dump(existing_data, f, indent=2, ensure_ascii=False)

print(f"Data appended to: {temp_data_file}")
print(f"Total items scraped: {len(data)}")