from apify_client import ApifyClient
import sys
import os
import json
from datetime import datetime, timedelta
import re
import requests

# Add the root directory to Python path to import admin
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from admin import APIFY_KEY

def extract_username_from_url(url):
    """Extract username from Twitter/X URL"""
    pattern = r'(?:twitter\.com|x\.com)/([^/?]+)'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def fetch_unroll_html(tweet_id):
    """Fetch HTML from UnrollNow for thread detection"""
    url = f"https://unrollnow.com/status/{tweet_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)  # Reduced from 30 to 10 seconds
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching UnrollNow HTML for tweet {tweet_id}: {e}")
        return None

def extract_thread_tweet_ids(html, target_username=None):
    """Extract thread tweet IDs from UnrollNow HTML, excluding quoted tweets and attachments"""
    if not html:
        return []

    # If we have a target username, only extract tweet IDs associated with that user
    if target_username:
        # Look for tweet IDs in URLs or data attributes that contain the target username
        # Pattern: href="/username/status/tweet_id" or data-username="username"
        user_pattern = rf'(?:href="/{target_username}/status/|data-username="{target_username}")'
        user_matches = re.findall(user_pattern, html, re.IGNORECASE)

        # Extract tweet IDs that are associated with the target username
        tweet_url_pattern = rf'href="/{target_username}/status/(\d{{18,19}})"'
        thread_ids = re.findall(tweet_url_pattern, html, re.IGNORECASE)

        # Also look for tweet IDs in data-tweet-id attributes
        tweet_data_pattern = r'data-tweet-id="(\d{18,19})"'
        data_thread_ids = re.findall(tweet_data_pattern, html)
        thread_ids.extend(data_thread_ids)

        # Exclude quoted tweets (these appear in quote-tweet containers)
        quoted_tweet_pattern = r'<div[^>]*class="[^"]*quote[^"]*"[^>]*>.*?(\d{18,19})'
        quoted_ids = set(re.findall(quoted_tweet_pattern, html, re.DOTALL | re.IGNORECASE))

        # Filter out quoted tweet IDs
        thread_ids = [tid for tid in thread_ids if tid not in quoted_ids]

        # If we didn't find tweet URLs, fall back to data-tweet-id attributes near the username
        if not thread_ids:
            # Find tweet IDs in data attributes that are near the target username
            tweet_data_pattern = r'data-tweet-id="(\d{18,19})"'
            all_tweet_ids = re.findall(tweet_data_pattern, html)

            # Filter to only include tweet IDs that appear in contexts with the target username
            username_context_pattern = rf'(?:{target_username}|@{target_username}).*?data-tweet-id="(\d{{18,19}})"|data-tweet-id="(\d{{18,19}})".*?(?:{target_username}|@{target_username})'
            context_matches = re.findall(username_context_pattern, html, re.DOTALL | re.IGNORECASE)

            # Extract tweet IDs from context matches
            context_tweet_ids = []
            for match in context_matches:
                # Each match tuple may have empty strings, filter them out
                tweet_ids_in_match = [tid for tid in match if tid]
                context_tweet_ids.extend(tweet_ids_in_match)

            # Combine and deduplicate
            thread_ids = list(set(all_tweet_ids) & set(context_tweet_ids)) if context_tweet_ids else all_tweet_ids[:10]  # Limit to reasonable number
    else:
        # Original logic when no target username is provided
        # Find all tweet IDs in the HTML
        all_tweet_ids = re.findall(r'\b\d{18,19}\b', html)

        if not all_tweet_ids:
            return []

        # Remove quoted tweets (these appear in quote-tweet containers)
        quoted_tweet_pattern = r'<div[^>]*class="[^"]*quote[^"]*"[^>]*>.*?(\d{18,19})'
        quoted_ids = set(re.findall(quoted_tweet_pattern, html, re.DOTALL | re.IGNORECASE))

        # Remove embedded/attachment tweets (these appear in different containers)
        embedded_pattern = r'<div[^>]*class="[^"]*embed[^"]*"[^>]*>.*?(\d{18,19})'
        embedded_ids = set(re.findall(embedded_pattern, html, re.DOTALL | re.IGNORECASE))

        # Remove video attachments and media containers
        media_pattern = r'<div[^>]*class="[^"]*media[^"]*"[^>]*>.*?(\d{18,19})'
        media_ids = set(re.findall(media_pattern, html, re.DOTALL | re.IGNORECASE))

        # Combine all IDs to exclude
        excluded_ids = quoted_ids | embedded_ids | media_ids

        # Filter out excluded IDs and remove duplicates while preserving order
        seen = set()
        thread_ids = []
        for tweet_id in all_tweet_ids:
            if tweet_id not in excluded_ids and tweet_id not in seen:
                seen.add(tweet_id)
                thread_ids.append(tweet_id)

    # Remove duplicates while preserving order and limit to reasonable number
    seen = set()
    unique_thread_ids = []
    for tweet_id in thread_ids:
        if tweet_id not in seen:
            seen.add(tweet_id)
            unique_thread_ids.append(tweet_id)

    return unique_thread_ids[:25]  # Increased limit to 25 to capture longer threads

def get_highest_quality_video(video_info):
    """Extract highest quality video URL from video_info"""
    if not video_info or 'variants' not in video_info:
        return None
    
    mp4_variants = [v for v in video_info['variants'] if v.get('content_type') == 'video/mp4']
    if mp4_variants:
        highest = max(mp4_variants, key=lambda x: x.get('bitrate', 0))
        return highest.get('url')
    return None

def enhance_tweet_data(tweet):
    """Enhance tweet data while preserving original structure from twitter_data.json"""
    if 'id' in tweet and tweet['id']:
        username = tweet.get('user', {}).get('screen_name', 'unknown')
        tweet['tweet_url'] = f"https://x.com/{username}/status/{tweet['id']}"
    
    # Add highest quality video URLs to existing media structure
    for media in tweet.get('media', []):
        if media.get('type') == 'video' and 'video_info' in media:
            highest_video_url = get_highest_quality_video(media['video_info'])
            if highest_video_url:
                media['highest_quality_video_url'] = highest_video_url
    
    return tweet

def classify_and_process_tweets(tweets):
    """Classify tweets as single tweets or threads and process accordingly"""
    client = ApifyClient(APIFY_KEY)
    classified_data = []

    # Get the main username from the first tweet to ensure consistency
    main_username = None
    if tweets:
        main_username = tweets[0].get('user', {}).get('screen_name')

    for tweet in tweets:
        tweet_id = tweet.get('id')
        text = tweet.get('text', '')
        current_username = tweet.get('user', {}).get('screen_name')

        # Only process tweets from the main user
        if main_username and current_username != main_username:
            print(f"Skipping tweet {tweet_id} from different user: @{current_username}")
            continue

        # Enhance the original tweet data
        enhanced_tweet = enhance_tweet_data(tweet)

        # Always check UnrollNow for thread detection (no pre-filtering by text)
        print(f"Checking UnrollNow for tweet: {tweet_id}")

        # Fetch UnrollNow HTML to get thread structure
        html = fetch_unroll_html(tweet_id)
        thread_ids = extract_thread_tweet_ids(html, main_username)

        # Additional check: if the tweet text contains a thread link, try to extract tweet IDs from it
        if not thread_ids and ('t.co/' in text or 'thread' in text.lower() or '🧵' in text):
            print(f"Tweet might be part of a thread, checking: {tweet_id}")
            # Try to get thread IDs from the tweet text itself
            text_thread_ids = extract_thread_ids_from_text(text, tweet_id)
            if text_thread_ids:
                thread_ids = text_thread_ids
                print(f"Found potential thread IDs from text: {thread_ids}")

        if len(thread_ids) > 1:
            print(f"Thread detected with {len(thread_ids)} tweets")

            # Process all threads without limits
            run_input = {
                "mode": "Get a Few Tweets",
                "tweets": ",".join(thread_ids),
                "max_results": len(thread_ids)
            }

            try:
                run = client.actor("scrape.badger/twitter-tweets-scraper").call(run_input=run_input)
                thread_tweets = []

                for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                    # Filter to only include tweets from the same user and exclude quoted tweets
                    item_username = item.get('user', {}).get('screen_name')
                    is_quoted = item.get('is_quote_status', False)
                    if item_username == main_username and not is_quoted:
                        enhanced_item = enhance_tweet_data(item)
                        thread_tweets.append(enhanced_item)
                    else:
                        print(f"Filtering out tweet from different user or quoted tweet: @{item_username}")

                if thread_tweets:  # Only create thread if we have valid tweets
                    # Sort tweets by their position in thread_ids to maintain order
                    id_to_position = {tid: i for i, tid in enumerate(thread_ids)}
                    thread_tweets.sort(key=lambda x: id_to_position.get(x.get('id'), 999))

                    # Double-check that we have the main tweet in the thread
                    main_tweet_in_thread = any(tweet.get('id') == tweet_id for tweet in thread_tweets)
                    if not main_tweet_in_thread:
                        # Add the main tweet to the thread if it's not already there
                        thread_tweets.insert(0, enhanced_tweet)
                        print(f"Added main tweet to thread: {tweet_id}")

                    # Return thread data in enhanced format
                    classified_data.append({
                        'content_type': 'thread',
                        'thread_id': tweet_id,
                        'thread_length': len(thread_tweets),
                        'ordered_tweets': thread_tweets,  # All tweets in proper order for reconstruction
                        'scraped_at': datetime.now().isoformat()
                    })
                else:
                    # If no valid thread tweets found, treat as single tweet
                    print(f"No valid thread tweets found for {tweet_id}, treating as single tweet")
                    classified_data.append({
                        'content_type': 'tweet',
                        **enhanced_tweet,
                        'scraped_at': datetime.now().isoformat()
                    })

            except Exception as e:
                print(f"Error processing thread {tweet_id}: {e}")
                # Fallback to single tweet
                classified_data.append({
                    'content_type': 'tweet',
                    **enhanced_tweet,
                    'scraped_at': datetime.now().isoformat()
                })
        else:
            print(f"No thread found, treating as single tweet: {tweet_id}")
            classified_data.append({
                'content_type': 'tweet',
                **enhanced_tweet,
                'scraped_at': datetime.now().isoformat()
            })

    return classified_data

# Initialize the ApifyClient
client = ApifyClient(APIFY_KEY)

# Store the input URL for grouping - will be dynamically updated by main.py
twitter_url = "https://x.com/elonmusk"
URL_GROUP = twitter_url  # Store the input URL for grouping
username = extract_username_from_url(twitter_url)

if not username:
    raise ValueError(f"Could not extract username from URL: {twitter_url}")

# Calculate dates dynamically - 7 days ago to today (keep full week as required)
today = datetime.now()
seven_days_ago = today - timedelta(days=7)
start_date = seven_days_ago.strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")

# Prepare the Actor input with date filtering
run_input = {
    "mode": "Advanced Search",
    "query": f"from:{username} -filter:replies since:{start_date} until:{end_date}",
    "query_type": "Latest",
    "max_results": 10,  # Keep max results for better content selection
}

print(f"Starting enhanced Twitter scraper for @{username}")
print(f"Date range: {start_date} to {end_date}")

# Run the Actor
run = client.actor("scrape.badger/twitter-tweets-scraper").call(run_input=run_input)

# Fetch initial tweet data
raw_tweets = []
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    if 'id' in item and item['id']:
        tweet_username = item.get('user', {}).get('screen_name', username)
        item['tweet_url'] = f"https://x.com/{tweet_username}/status/{item['id']}"
    # Add URL_GROUP to each tweet
    item['URL_GROUP'] = URL_GROUP
    raw_tweets.append(item)

print(f"Retrieved {len(raw_tweets)} initial tweets")

# Classify and process tweets (detect threads vs single tweets)
processed_data = classify_and_process_tweets(raw_tweets)

# Save processed data to temp_data.json (append mode)
import os
temp_data_file = os.path.join(os.path.dirname(__file__), "..", "temp_data.json")

# Load existing temp data if it exists
existing_data = []
if os.path.exists(temp_data_file):
    try:
        with open(temp_data_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        existing_data = []

# Add URL_GROUP to each processed item and append to existing data
for item in processed_data:
    item['URL_GROUP'] = URL_GROUP
    existing_data.append(item)

# Save all data back to temp_data.json
with open(temp_data_file, "w", encoding="utf-8") as f:
    json.dump(existing_data, f, indent=2, ensure_ascii=False)

# Summary
tweets_count = sum(1 for item in processed_data if item['content_type'] == 'tweet')
threads_count = sum(1 for item in processed_data if item['content_type'] == 'thread')
total_thread_tweets = sum(item['thread_length'] for item in processed_data if item['content_type'] == 'thread')

print(f"\nEnhanced Twitter scraping completed!")
print(f"Data appended to: {temp_data_file}")
print(f"Summary:")
print(f"   - {tweets_count} single tweets")
print(f"   - {threads_count} threads ({total_thread_tweets} total thread tweets)")
print(f"   - {len(processed_data)} total content items")


def extract_thread_ids_from_text(text, main_tweet_id):
    """Extract thread tweet IDs from tweet text that might contain thread links"""
    # This is a helper function to extract tweet IDs from text
    # We can try to resolve t.co links or look for patterns in the text
    thread_ids = []
    
    # Always include the main tweet ID
    if main_tweet_id:
        thread_ids.append(main_tweet_id)
    
    # Look for common thread indicators in the text
    # Patterns like "1/", "1.", "Part 1", etc.
    thread_indicators = [
        r'\b1[/.]\s*\d+\s*part',
        r'\bpart\s*1\b',
        r'\b\d+\s*/\s*\d+',
        r'\b\d+\s*of\s*\d+',
        r'\bthread\b',
        r'\b🧵\b'
    ]
    
    for pattern in thread_indicators:
        if re.search(pattern, text, re.IGNORECASE):
            # If we find thread indicators, we should try to get more tweets
            # For now, we'll just return with the main tweet ID
            # In a more advanced implementation, we could try to resolve the t.co link
            break
    
    return thread_ids if thread_ids else [main_tweet_id] if main_tweet_id else []


def get_conversation_tweets(tweet_id, client):
    """Get tweets from the same conversation/thread using Twitter API"""
    try:
        # Try to get conversation tweets using Apify
        run_input = {
            "mode": "Get a Few Tweets",
            "tweets": tweet_id,
            "max_results": 1
        }
        
        run = client.actor("scrape.badger/twitter-tweets-scraper").call(run_input=run_input)
        conversation_tweets = []
        
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            # Get the conversation ID if available
            conversation_id = item.get('conversation_id')
            if conversation_id and conversation_id != tweet_id:
                # Try to get more tweets from this conversation
                conv_run_input = {
                    "mode": "Get a Few Tweets",
                    "tweets": conversation_id,
                    "max_results": 10
                }
                
                conv_run = client.actor("scrape.badger/twitter-tweets-scraper").call(run_input=conv_run_input)
                for conv_item in client.dataset(conv_run["defaultDatasetId"]).iterate_items():
                    conv_tweet_id = conv_item.get('id')
                    if conv_tweet_id and conv_tweet_id not in conversation_tweets:
                        conversation_tweets.append(conv_tweet_id)
        
        # Add the original tweet ID if not already present
        if tweet_id not in conversation_tweets:
            conversation_tweets.insert(0, tweet_id)
            
        return conversation_tweets
    except Exception as e:
        print(f"Error getting conversation tweets for {tweet_id}: {e}")
        return [tweet_id]  # Return just the original tweet ID as fallback
