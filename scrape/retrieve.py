import json
import os

def extract_instagram_fields(item):
    """Extract fields from Instagram data with comprehensive stats and media"""
    # Determine post type based on content
    post_type = item.get('type', 'unknown').lower()
    if post_type not in ['video', 'image', 'carousel']:
        post_type = 'video' if item.get('videoUrl') else 'image'
    
    # Extract media URLs
    video_url = item.get('videoUrl')
    image_urls = []
    
    # Handle image URLs (Instagram may have multiple images in carousels)
    if item.get('imageUrl'):
        image_urls.append(item.get('imageUrl'))
    elif item.get('images'):
        image_urls.extend(item.get('images', []))
    
    # Extract comprehensive stats
    stats = {
        'views': safe_int(item.get('videoViewCount', 0)) or safe_int(item.get('videoPlayCount', 0)),
        'likes': safe_int(item.get('likesCount', 0)),
        'comments': safe_int(item.get('commentsCount', 0)),
        'shares': None  # Instagram doesn't provide public share counts
    }
    
    # Extract hashtags
    hashtags = item.get('hashtags', [])
    if isinstance(hashtags, str):
        # If hashtags is a string, extract them
        hashtags = [tag.strip('#') for tag in hashtags.split() if tag.startswith('#')]
    
    # Build result with only essential fields
    result = {
        "platform": "instagram",
        "content_type": "post",
        "type": post_type,
        "url": item.get('url'),
        "text": item.get('caption', ''),
        "video_url": video_url,
        "image_urls": image_urls,
        "media_count": (1 if video_url else 0) + len(image_urls),
        "stats": stats,
        "hashtags": hashtags,
        "author": {
            "username": item.get('ownerUsername')
        },
        "URL_GROUP": item.get('URL_GROUP')  # Preserve URL_GROUP from scraper
    }
    
    # Add optional fields only if they exist
    if item.get('id'):
        result["id"] = item.get('id')
    if item.get('ownerFullName'):
        result["author"]["name"] = item.get('ownerFullName')
    if item.get('ownerUsername'):
        result["author"]["profile_url"] = f"https://instagram.com/{item.get('ownerUsername')}"
    
    # Remove None/null values and empty fields
    return clean_data(result)

def extract_tiktok_fields(item):
    """Extract fields from TikTok data with comprehensive stats and media"""
    author_meta = item.get('authorMeta', {})
    
    # Extract comprehensive stats
    stats = {
        'views': safe_int(item.get('playCount', 0)),
        'likes': safe_int(item.get('diggCount', 0)),
        'comments': safe_int(item.get('commentCount', 0)),
        'shares': safe_int(item.get('shareCount', 0)),
        'collects': safe_int(item.get('collectCount', 0))
    }
    
    # Extract hashtags
    hashtags = []
    if item.get('hashtags'):
        for tag in item.get('hashtags', []):
            if isinstance(tag, dict) and tag.get('name'):
                hashtags.append(tag['name'])
            elif isinstance(tag, str):
                hashtags.append(tag)
    
    # Extract video URL
    video_url = item.get('webVideoUrl') or item.get('videoUrl')
    
    # Build result with only essential fields
    result = {
        "platform": "tiktok",
        "content_type": "video",
        "type": "video",
        "url": item.get('webVideoUrl') or item.get('videoUrl'),
        "text": item.get('text', ''),
        "video_url": video_url,
        "image_urls": [],  # TikTok is video-only
        "media_count": 1 if video_url else 0,
        "stats": stats,
        "hashtags": hashtags,
        "author": {},
        "URL_GROUP": item.get('URL_GROUP')  # Preserve URL_GROUP from scraper
    }
    
    # Add optional fields only if they exist
    if item.get('id'):
        result["id"] = item.get('id')
    if author_meta.get('nickName'):
        result["author"]["name"] = author_meta.get('nickName')
    if author_meta.get('name'):
        result["author"]["username"] = author_meta.get('name')
    if author_meta.get('profileUrl'):
        result["author"]["profile_url"] = author_meta.get('profileUrl')
    if safe_int(author_meta.get('fans', 0)) > 0:
        result["author"]["followers_count"] = safe_int(author_meta.get('fans', 0))
    if item.get('videoDuration'):
        result["duration"] = item.get('videoDuration')
    
    # Remove None/null values and empty fields
    return clean_data(result)

def extract_linkedin_fields(item):
    """Extract fields from LinkedIn data with comprehensive stats and media"""
    author = item.get('author', {})
    
    # Determine post type based on content
    post_type = "text"  # default
    video_url = None
    image_urls = []
    
    if item.get('type') == 'linkedinVideo':
        post_type = "video"
        linkedin_video = item.get('linkedinVideo', {})
        video_meta = linkedin_video.get('videoPlayMetadata', {})
        progressive_streams = video_meta.get('progressiveStreams', [])
        if progressive_streams:
            stream_locations = progressive_streams[0].get('streamingLocations', [])
            if stream_locations:
                video_url = stream_locations[0].get('url')
    elif item.get('images'):
        post_type = "image"
        image_urls = item.get('images', [])
        # Extract URLs if images are objects
        if image_urls and isinstance(image_urls[0], dict):
            image_urls = [img.get('url') for img in image_urls if img.get('url')]
    
    # Extract comprehensive stats
    stats = {
        'likes': safe_int(item.get('numLikes', 0)),
        'comments': safe_int(item.get('numComments', 0)),
        'shares': safe_int(item.get('numShares', 0)),
        'views': None  # LinkedIn doesn't provide public view counts
    }
    
    # Extract hashtags from text
    text = item.get('text', '')
    hashtags = []
    if text:
        words = text.split()
        hashtags = [word.strip('#') for word in words if word.startswith('#')]
    
    # Build result with only essential fields
    result = {
        "platform": "linkedin",
        "content_type": "post",
        "type": post_type,
        "url": item.get('url'),
        "text": text,
        "video_url": video_url,
        "image_urls": image_urls,
        "media_count": (1 if video_url else 0) + len(image_urls),
        "stats": stats,
        "hashtags": hashtags,
        "author": {},
        "URL_GROUP": item.get('URL_GROUP')  # Preserve URL_GROUP from scraper
    }
    
    # Add optional fields only if they exist
    if item.get('urn'):
        result["id"] = item.get('urn')
    if item.get('activityDescription'):
        result["activity_description"] = item.get('activityDescription')
    
    # Add author fields only if they exist
    author_name = f"{author.get('firstName', '')} {author.get('lastName', '')}".strip()
    if author_name:
        result["author"]["name"] = author_name
    if author.get('publicId'):
        result["author"]["username"] = author.get('publicId')
    if author.get('occupation'):
        result["author"]["headline"] = author.get('occupation')
    if author.get('profileUrl') or item.get('authorProfileUrl'):
        result["author"]["profile_url"] = author.get('profileUrl') or item.get('authorProfileUrl')
    
    # Remove None/null values and empty fields
    return clean_data(result)

def load_twitter_data():
    """Load Twitter data from twitter_data.json"""
    scrapers_dir = os.path.join(os.path.dirname(__file__), "scrapers")
    twitter_file = os.path.join(scrapers_dir, "twitter_data.json")
    
    try:
        with open(twitter_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {twitter_file} not found")
        return []



def extract_twitter_fields(item):
    """Extract fields from Twitter data with enhanced thread and tweet support"""
    content_type = item.get('content_type', 'tweet')
    
    # Handle single tweets
    if content_type == 'tweet':
        return extract_single_tweet(item)
    
    # Handle threads
    elif content_type == 'thread':
        return extract_thread(item)
    
    else:
        # Fallback for old format
        return extract_legacy_tweet(item)

def extract_single_tweet(item):
    """Extract data from a single tweet"""
    user = item.get('user', {})
    
    # Determine post type and extract media
    post_type, video_url, image_urls = determine_post_type_and_media(item.get('media', []))
    
    # Extract engagement stats
    stats = {
        'views': safe_int(item.get('view_count', 0)),
        'likes': safe_int(item.get('favorite_count', 0)),
        'retweets': safe_int(item.get('retweet_count', 0)),
        'replies': safe_int(item.get('reply_count', 0)),
        'quotes': safe_int(item.get('quote_count', 0)),
        'bookmarks': safe_int(item.get('bookmark_count', 0))
    }
    
    # Extract text content
    text = item.get('text', '') or item.get('full_text', '')
    hashtags = item.get('hastags', [])  # Note: API uses 'hastags' (typo)
    
    # Extract profile URL from tweet URL
    tweet_url = item.get('tweet_url', '')
    profile_url = extract_profile_url_from_tweet(tweet_url, user.get('screen_name'))
    
    # Build result with only essential fields
    result = {
        "platform": "twitter",
        "content_type": "tweet",
        "type": post_type,
        "url": tweet_url,
        "text": text,
        "video_url": video_url,
        "image_urls": image_urls,
        "media_count": len(item.get('media', [])),
        "stats": stats,
        "hashtags": hashtags,
        "urls": extract_urls(item),
        "author": {
            "username": user.get('screen_name')
        },
        "URL_GROUP": item.get('URL_GROUP')  # Preserve URL_GROUP from scraper
    }
    
    # Add optional fields only if they exist
    if item.get('id'):
        result["id"] = item.get('id')
    if user.get('name'):
        result["author"]["name"] = user.get('name')
    if user.get('description'):
        result["author"]["description"] = user.get('description')
    if safe_int(user.get('followers_count', 0)) > 0:
        result["author"]["followers_count"] = safe_int(user.get('followers_count', 0))
    if profile_url:
        result["author"]["profile_url"] = profile_url
    if user.get('location'):
        result["author"]["location"] = user.get('location')
    if user.get('profile_image_url'):
        result["author"]["profile_image_url"] = user.get('profile_image_url')
    if item.get('created_at_datetime'):
        result["timestamp"] = item.get('created_at_datetime')
    if item.get('lang'):
        result["language"] = item.get('lang')
    
    # Remove None/null values and empty fields
    return clean_data(result)

def extract_thread(item):
    """Extract data from a Twitter thread"""
    thread_tweets = item.get('ordered_tweets', [])
    thread_length = len(thread_tweets)
    
    if not thread_tweets:
        return None
    
    # Process each tweet in the thread
    processed_tweets = []
    combined_stats = {
        'views': 0,
        'likes': 0,
        'retweets': 0,
        'replies': 0,
        'quotes': 0,
        'bookmarks': 0
    }
    
    all_media = {
        'videos': [],
        'images': [],
        'total_count': 0
    }
    
    # Process each tweet in order
    for idx, tweet in enumerate(thread_tweets, 1):
        user = tweet.get('user', {})
        
        # Determine post type and media for this tweet
        post_type, video_url, image_urls = determine_post_type_and_media(tweet.get('media', []))
        
        # Extract stats for this tweet
        tweet_stats = {
            'views': safe_int(tweet.get('view_count', 0)),
            'likes': safe_int(tweet.get('favorite_count', 0)),
            'retweets': safe_int(tweet.get('retweet_count', 0)),
            'replies': safe_int(tweet.get('reply_count', 0)),
            'quotes': safe_int(tweet.get('quote_count', 0)),
            'bookmarks': safe_int(tweet.get('bookmark_count', 0))
        }
        
        # Add to combined stats
        for key in combined_stats:
            combined_stats[key] += tweet_stats[key]
        
        # Collect media
        if video_url:
            all_media['videos'].append({
                'url': video_url,
                'tweet_number': idx,
                'tweet_id': tweet.get('id')
            })
        
        for img_url in image_urls:
            all_media['images'].append({
                'url': img_url,
                'tweet_number': idx,
                'tweet_id': tweet.get('id')
            })
        
        all_media['total_count'] += len(tweet.get('media', []))
        
        # Process individual tweet
        tweet_data = {
            "tweet_number": idx,
            "text": tweet.get('text', '') or tweet.get('full_text', ''),
            "type": post_type,
            "url": tweet.get('tweet_url'),
            "video_url": video_url,
            "image_urls": image_urls,
            "media_count": len(tweet.get('media', [])),
            "stats": tweet_stats,
            "hashtags": tweet.get('hastags', []),
            "urls": extract_urls(tweet)
        }
        
        # Add optional fields only if they exist
        if tweet.get('id'):
            tweet_data["id"] = tweet.get('id')
        if tweet.get('created_at_datetime'):
            tweet_data["timestamp"] = tweet.get('created_at_datetime')
        if tweet.get('lang'):
            tweet_data["language"] = tweet.get('lang')
        
        processed_tweets.append(tweet_data)
    
    # Get main thread info from first tweet
    main_tweet = thread_tweets[0]
    main_user = main_tweet.get('user', {})
    
    # Extract profile URL from main tweet URL
    main_tweet_url = main_tweet.get('tweet_url', '')
    profile_url = extract_profile_url_from_tweet(main_tweet_url, main_user.get('screen_name'))
    
    # Determine overall thread type
    thread_type = "thread"
    if all_media['videos']:
        thread_type = "thread_with_videos"
    elif all_media['images']:
        thread_type = "thread_with_images"
    
    # Build result with only essential fields
    result = {
        "platform": "twitter",
        "content_type": "thread",
        "type": thread_type,
        "url": main_tweet_url,
        "thread_length": thread_length,
        "tweets": processed_tweets,  # Ordered list of tweets with tweet1, tweet2, etc.
        "combined_text": " ".join([t['text'] for t in processed_tweets]),
        "combined_stats": combined_stats,
        "all_media": all_media,
        "author": {
            "username": main_user.get('screen_name')
        },
        "URL_GROUP": item.get('URL_GROUP')  # Preserve URL_GROUP from scraper
    }
    
    # Add optional fields only if they exist
    if item.get('thread_id'):
        result["id"] = item.get('thread_id')
    if main_user.get('name'):
        result["author"]["name"] = main_user.get('name')
    if main_user.get('description'):
        result["author"]["description"] = main_user.get('description')
    if safe_int(main_user.get('followers_count', 0)) > 0:
        result["author"]["followers_count"] = safe_int(main_user.get('followers_count', 0))
    if profile_url:
        result["author"]["profile_url"] = profile_url
    if main_user.get('location'):
        result["author"]["location"] = main_user.get('location')
    if main_user.get('profile_image_url'):
        result["author"]["profile_image_url"] = main_user.get('profile_image_url')
    if main_tweet.get('created_at_datetime'):
        result["timestamp"] = main_tweet.get('created_at_datetime')
    if main_tweet.get('lang'):
        result["language"] = main_tweet.get('lang')
    
    # Remove None/null values and empty fields
    return clean_data(result)

def extract_legacy_tweet(item):
    """Extract data from legacy Twitter format (fallback)"""
    user = item.get('user', {})
    
    # Determine post type and extract media
    post_type, video_url, image_urls = determine_post_type_and_media(item.get('media', []))
    
    # Extract engagement stats
    stats = {
        'views': safe_int(item.get('view_count', 0)),
        'likes': safe_int(item.get('favorite_count', 0)),
        'retweets': safe_int(item.get('retweet_count', 0)),
        'replies': safe_int(item.get('reply_count', 0)),
        'quotes': safe_int(item.get('quote_count', 0)),
        'bookmarks': safe_int(item.get('bookmark_count', 0))
    }
    
    # Extract profile URL from tweet URL
    tweet_url = item.get('tweet_url', '')
    profile_url = extract_profile_url_from_tweet(tweet_url, user.get('screen_name'))
    
    # Extract text content
    text = item.get('text', '') or item.get('full_text', '')
    hashtags = item.get('hastags', [])  # Note: API uses 'hastags' (typo)
    
    # Build result with only essential fields
    result = {
        "platform": "twitter",
        "content_type": "tweet",
        "type": post_type,
        "url": tweet_url,
        "text": text,
        "video_url": video_url,
        "image_urls": image_urls,
        "media_count": len(item.get('media', [])),
        "stats": stats,
        "hashtags": hashtags,
        "urls": extract_urls(item),
        "author": {
            "username": user.get('screen_name')
        },
        "URL_GROUP": item.get('URL_GROUP')  # Preserve URL_GROUP from scraper
    }
    
    # Add optional fields only if they exist
    if item.get('id'):
        result["id"] = item.get('id')
    if user.get('name'):
        result["author"]["name"] = user.get('name')
    if user.get('description'):
        result["author"]["description"] = user.get('description')
    if safe_int(user.get('followers_count', 0)) > 0:
        result["author"]["followers_count"] = safe_int(user.get('followers_count', 0))
    if profile_url:
        result["author"]["profile_url"] = profile_url
    if user.get('location'):
        result["author"]["location"] = user.get('location')
    if user.get('profile_image_url'):
        result["author"]["profile_image_url"] = user.get('profile_image_url')
    if item.get('created_at_datetime'):
        result["timestamp"] = item.get('created_at_datetime')
    if item.get('lang'):
        result["language"] = item.get('lang')
    
    # Remove None/null values and empty fields
    return clean_data(result)

def determine_post_type_and_media(media_list):
    """Determine post type and extract media URLs"""
    post_type = "text"
    video_url = None
    image_urls = []
    
    for media_item in media_list:
        media_type = media_item.get('type')
        
        if media_type == 'video':
            post_type = "video"
            # Get highest quality video URL
            if 'highest_quality_video_url' in media_item:
                video_url = media_item['highest_quality_video_url']
            else:
                # Fallback to extracting from video_info
                video_info = media_item.get('video_info', {})
                variants = video_info.get('variants', [])
                mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4']
                if mp4_variants:
                    highest_quality = max(mp4_variants, key=lambda x: x.get('bitrate', 0))
                    video_url = highest_quality.get('url')
                    
        elif media_type == 'photo':
            post_type = "image" if post_type == "text" else post_type
            image_url = media_item.get('media_url')
            if image_url:
                image_urls.append(image_url)
    
    return post_type, video_url, image_urls

def extract_urls(item):
    """Extract URLs from tweet"""
    urls = []
    if 'urls' in item:
        for url_obj in item['urls']:
            if isinstance(url_obj, dict):
                urls.append(url_obj.get('expanded_url') or url_obj.get('url'))
            else:
                urls.append(str(url_obj))
    return urls

def safe_int(value):
    """Safely convert value to int, return 0 if conversion fails"""
    try:
        if isinstance(value, str) and value.isdigit():
            return int(value)
        elif isinstance(value, (int, float)):
            return int(value)
        else:
            return 0
    except (ValueError, TypeError):
        return 0

def extract_profile_url_from_tweet(tweet_url, username):
    """Extract profile URL from tweet URL by removing the /status/ part"""
    if not tweet_url:
        # Fallback to constructing from username
        return f"https://x.com/{username}" if username else None
    
    try:
        # Extract everything before /status/
        if '/status/' in tweet_url:
            profile_url = tweet_url.split('/status/')[0]
            return profile_url
        else:
            # If no /status/ found, fallback to username
            return f"https://x.com/{username}" if username else None
    except:
        # Fallback in case of any error
        return f"https://x.com/{username}" if username else None

def load_youtube_data():
    """Load YouTube data from youtube_data.json"""
    scrapers_dir = os.path.join(os.path.dirname(__file__), "scrapers")
    youtube_file = os.path.join(scrapers_dir, "youtube_data.json")
    
    try:
        with open(youtube_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {youtube_file} not found")
        return []

def extract_youtube_fields(item):
    """Extract fields from YouTube data with comprehensive stats and media"""
    # Extract comprehensive stats
    stats = {
        'views': safe_int(item.get('viewCount', 0)),
        'likes': safe_int(item.get('likeCount', 0)),
        'comments': safe_int(item.get('commentCount', 0)),
        'shares': None  # YouTube doesn't provide public share count in standard API
    }
    
    # Extract video details
    video_url = item.get('url')
    thumbnail_url = item.get('thumbnailUrl')
    duration = item.get('duration')
    
    # Determine if it's a video or short based on duration
    # YouTube Shorts are typically 60 seconds or less
    video_type = "video"  # default
    if duration:
        # Parse duration (format: PT1M30S or PT45S)
        try:
            # Simple parsing for common formats
            if 'PT' in str(duration):
                duration_str = str(duration).replace('PT', '')
                total_seconds = 0
                
                if 'M' in duration_str:
                    minutes_part = duration_str.split('M')[0]
                    total_seconds += int(minutes_part) * 60
                    duration_str = duration_str.split('M')[1] if 'M' in duration_str else ''
                
                if 'S' in duration_str:
                    seconds_part = duration_str.replace('S', '')
                    if seconds_part:
                        total_seconds += int(seconds_part)
                
                # YouTube Shorts are 60 seconds or less
                if total_seconds <= 60:
                    video_type = "short"
        except:
            # If parsing fails, default to video
            pass
    
    # Extract hashtags from title and description
    title = item.get('title', '')
    description = item.get('description', '')
    combined_text = f"{title} {description}"
    hashtags = []
    if combined_text:
        words = combined_text.split()
        hashtags = [word.strip('#') for word in words if word.startswith('#')]
    
    # Build result with only essential fields
    result = {
        "platform": "youtube",
        "content_type": "video",
        "type": video_type,  # "video" or "short"
        "url": video_url,
        "text": title,
        "description": description,
        "video_url": video_url,
        "image_urls": [thumbnail_url] if thumbnail_url else [],
        "media_count": 1 if video_url else 0,
        "stats": stats,
        "hashtags": hashtags,
        "author": {
            "name": item.get('channelName'),
            "subscribers_count": safe_int(item.get('subscriberCount', 0))
        },
        "URL_GROUP": item.get('URL_GROUP')  # Preserve URL_GROUP from scraper
    }
    
    # Add optional fields only if they exist
    if item.get('videoId'):
        result["id"] = item.get('videoId')
    if item.get('channelHandle'):
        result["author"]["username"] = item.get('channelHandle')
    if item.get('channelUrl'):
        result["author"]["profile_url"] = item.get('channelUrl')
    if item.get('publishedAt'):
        result["timestamp"] = item.get('publishedAt')
    if duration:
        result["duration"] = duration
    if thumbnail_url:
        result["thumbnail_url"] = thumbnail_url
    
    # Remove None/null values and empty fields
    return clean_data(result)

def load_temp_data():
    """Load all scraped data from temp_data.json"""
    temp_file = os.path.join(os.path.dirname(__file__), "temp_data.json")
    
    try:
        with open(temp_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {temp_file} not found - no data to process")
        return []
    except Exception as e:
        print(f"Error loading temp data: {e}")
        return []

def clean_data(data):
    """Remove None/null values, empty lists/dicts, and unnecessary fields from data"""
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            # Skip None values, null values, empty strings, empty lists, and empty dicts
            if value is None or value == "" or value == "null" or (isinstance(value, (list, dict)) and len(value) == 0):
                continue
            # Recursively clean nested dicts and lists
            elif isinstance(value, dict):
                cleaned_value = clean_data(value)
                if cleaned_value:  # Only add non-empty dicts
                    cleaned[key] = cleaned_value
            elif isinstance(value, list):
                cleaned_list = [clean_data(item) for item in value]
                # Filter out None/null values from list
                cleaned_list = [item for item in cleaned_list if item is not None and item != "null"]
                if cleaned_list:  # Only add non-empty lists
                    cleaned[key] = cleaned_list
            else:
                # Keep all other values (strings, numbers, booleans)
                cleaned[key] = value
        return cleaned
    elif isinstance(data, list):
        cleaned_list = [clean_data(item) for item in data]
        return [item for item in cleaned_list if item is not None and item != "null"]
    else:
        return data if data != "null" else None

# Load all scraped data from temp_data.json
all_temp_data = load_temp_data()

# Extract and combine data by processing each item based on its platform
combined_data = []

for item in all_temp_data:
    # Determine platform from the item data
    platform = None
    
    # Check various ways platform might be stored
    if 'platform' in item:
        platform = item['platform']
    elif 'URL_GROUP' in item:
        url_group = item['URL_GROUP']
        if 'instagram.com' in url_group:
            platform = 'instagram'
        elif 'linkedin.com' in url_group:
            platform = 'linkedin'
        elif 'twitter.com' in url_group or 'x.com' in url_group:
            platform = 'twitter'
        elif 'youtube.com' in url_group:
            platform = 'youtube'
        elif 'tiktok.com' in url_group:
            platform = 'tiktok'
    
    # Process based on detected platform
    if platform == 'instagram':
        if item.get("type") == "Video":
            extracted = extract_instagram_fields(item)
            combined_data.append(extracted)
            # Removed ID and extra field printing as requested
            print(f"Instagram - Platform: {extracted['platform']} | Type: {extracted['type']}")
            print("-" * 50)
    
    elif platform == 'tiktok':
        extracted = extract_tiktok_fields(item)
        combined_data.append(extracted)
        # Removed ID and extra field printing as requested
        print(f"TikTok - Platform: {extracted['platform']} | Type: {extracted['type']}")
        print("-" * 50)
    
    elif platform == 'linkedin':
        extracted = extract_linkedin_fields(item)
        combined_data.append(extracted)
        # Removed ID and extra field printing as requested
        print(f"LinkedIn - Platform: {extracted['platform']} | Type: {extracted['type']}")
        print("-" * 50)
    
    elif platform == 'twitter':
        extracted = extract_twitter_fields(item)
        if extracted:  # Only process if extraction was successful
            combined_data.append(extracted)
            
            if extracted['content_type'] == 'thread':
                # Removed ID and extra field printing as requested
                print(f"Twitter Thread - Platform: {extracted['platform']} | Type: {extracted['type']}")
                print("-" * 50)
            else:
                # Removed ID and extra field printing as requested
                print(f"Twitter Tweet - Platform: {extracted['platform']} | Type: {extracted['type']}")
                print("-" * 50)
    
    elif platform == 'youtube':
        extracted = extract_youtube_fields(item)
        combined_data.append(extracted)
        # Removed ID and extra field printing as requested
        print(f"YouTube - Platform: {extracted['platform']} | Type: {extracted['type']}")
        print("-" * 50)
    
    else:
        print(f"Warning: Unknown platform for item")

# Save combined data to data.json in the scrape folder (not scrapers folder)
scrapers_dir = os.path.join(os.path.dirname(__file__), "scrapers")
scrape_dir = os.path.dirname(__file__)  # This is the scrape folder
output_file = os.path.join(scrape_dir, "data.json")

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(combined_data, f, indent=2, ensure_ascii=False)

# Clear the source files after processing
def clear_source_files():
    """Clear temp_data.json after processing"""
    # Clear temp_data.json
    temp_file = os.path.join(os.path.dirname(__file__), "temp_data.json")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump([], f)
        print(f"Cleared: temp_data.json")
    except Exception as e:
        print(f"Error clearing temp_data.json: {e}")

clear_source_files()

print(f"\nEnhanced social media data processing completed!")
print(f"Combined data saved to: {output_file}")
print(f"Total items processed: {len(combined_data)}")
print(f"\nData structure includes:")
print(f"   - Comprehensive stats (views, likes, shares, comments)")
print(f"   - All media URLs (videos, images) with proper extraction")
print(f"   - Thread reconstruction with numbered tweets (tweet1, tweet2, ...)")
print(f"   - Author information and verification status")
print(f"   - Hashtags and URLs extraction")
print(f"   - Timestamp and platform-specific metadata")