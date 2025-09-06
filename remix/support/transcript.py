"""
Transcript support module for video content.
Provides transcript functionality for YouTube, Instagram, and TikTok videos.
"""

import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs
import re
import os
import sys

# Add the parent directory to the path to import admin.py
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(parent_dir)
print(f"Added to sys.path: {parent_dir}")
# Import Apify API key from admin.py
try:
    from admin import APIFY_KEY
    
except ImportError:
    
    APIFY_KEY = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_youtube_video_id(url_or_id: str) -> Optional[str]:
    """
    Extract YouTube video ID from full URL (watch, shorts, embed, youtu.be)
    or return if it's already an ID.
    """
    # Already looks like a video ID
    if len(url_or_id) == 11 and '/' not in url_or_id:
        return url_or_id

    try:
        parsed = urlparse(url_or_id)

        if parsed.hostname in ['www.youtube.com', 'youtube.com']:
            # Handle standard watch URL
            if parsed.path == '/watch':
                return parse_qs(parsed.query).get('v', [None])[0]
            # Handle shorts URL: /shorts/<id>
            if parsed.path.startswith('/shorts/'):
                return parsed.path.split('/shorts/')[1].split('?')[0]
            # Handle embed URL: /embed/<id>
            if parsed.path.startswith('/embed/'):
                return parsed.path.split('/embed/')[1].split('?')[0]

        elif parsed.hostname == 'youtu.be':
            return parsed.path[1:]
    except Exception:
        pass

    # Regex fallback (covers more exotic cases)
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/)([^&\n?#]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    return None

def get_youtube_transcript(video_url: str) -> Optional[str]:
    """
    Get transcript for a YouTube video using youtube-transcript-api.
    
    Args:
        video_url: The URL of the YouTube video
        
    Returns:
        str: The transcript text or None if failed
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # Extract video ID from YouTube URL
        video_id = extract_youtube_video_id(video_url)
        if not video_id:
            logger.error("Could not extract YouTube video ID from URL")
            return None

        logger.info(f"Fetching transcript for video ID: {video_id}")

        # Use new API: instantiate and call fetch()
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)

        # Convert to raw data if available
        if hasattr(fetched_transcript, "to_raw_data"):
            raw_data = fetched_transcript.to_raw_data()
            text = "\n".join([part["text"] for part in raw_data if part.get("text")])
        else:
            # fallback if fetch returns list-like already
            text = "\n".join([getattr(part, "text", part.get("text", "")) for part in fetched_transcript])

        logger.info(f"Successfully retrieved YouTube transcript for video {video_id}")
        return text.strip() if text else None

    except Exception as e:
        logger.error(f"Error getting YouTube transcript: {str(e)}")
        return None

def get_apify_transcript(video_urls: List[str], target_lang: str = "English") -> Optional[str]:
    """
    Get transcript for videos using Apify's video-transcript actor.
    
    Args:
        video_urls: List of video URLs to transcribe
        target_lang: Target language for translation
        
    Returns:
        str: The transcript text or None if failed
    """
    try:
        # Check if Apify key is available
        if not APIFY_KEY:
            logger.error("APIFY_KEY not found in admin.py")
            return None
            
        # Import Apify client
        from apify_client import ApifyClient
        
        # Initialize the ApifyClient with your Apify API token
        client = ApifyClient(APIFY_KEY)

        # Prepare the Actor input
        run_input = {
            "video_urls": video_urls,
            "target_lang": target_lang
        }

        # Run the Actor and wait for it to finish
        run = client.actor("agentx/video-transcript").call(run_input=run_input)

        # Fetch and process Actor results from the run's dataset
        transcript_text = ""
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        # Log the complete response for debugging
        logger.info(f"Apify response items: {items}")
        
        for item in items:
            # Log each item for debugging
            logger.info(f"Apify item: {item}")
            
            # Extract transcript from the proper structure based on the schema
            # Check for target_transcript first (translated text)
            if "target_transcript" in item and item["target_transcript"]:
                target_transcript = item["target_transcript"]
                if isinstance(target_transcript, dict) and "text" in target_transcript:
                    transcript_text += target_transcript["text"] + "\n"
                elif isinstance(target_transcript, str):
                    transcript_text += target_transcript + "\n"
            
            # Fallback to source_transcript if target_transcript not available
            elif "source_transcript" in item and item["source_transcript"]:
                source_transcript = item["source_transcript"]
                if isinstance(source_transcript, dict) and "text" in source_transcript:
                    transcript_text += source_transcript["text"] + "\n"
                elif isinstance(source_transcript, str):
                    transcript_text += source_transcript + "\n"
            
            # Final fallback to direct transcript field
            elif "transcript" in item:
                transcript_text += item["transcript"] + "\n"
            
            # Also check for translation field as a fallback
            elif "translation" in item:
                transcript_text += "\nTranslation:\n" + item["translation"] + "\n"
        
        if transcript_text:
            logger.info(f"Successfully retrieved transcript from Apify for {len(video_urls)} videos")
            return transcript_text.strip()
        else:
            logger.warning("No transcript data found in Apify response")
            return None
            
    except Exception as e:
        logger.error(f"Error getting Apify transcript: {str(e)}")
        return None

def get_instagram_transcript(post_data: Dict[Any, Any]) -> Optional[str]:
    """
    Get transcript for Instagram content using Apify.
    
    Args:
        post_data: The Instagram post data
        
    Returns:
        str: The transcript text or None if failed
    """
    try:
        logger.info("Getting Instagram transcript using Apify")
        
        # Get video URL from post data
        video_url = post_data.get('video_url') or post_data.get('url')
        if not video_url:
            logger.error("No video URL found in Instagram post data")
            return None
            
        # Get transcript using Apify
        transcript = get_apify_transcript([video_url])
        return transcript
        
    except Exception as e:
        logger.error(f"Error getting Instagram transcript: {str(e)}")
        return None

def get_tiktok_transcript(post_data: Dict[Any, Any]) -> Optional[str]:
    """
    Get transcript for TikTok content using Apify.
    
    Args:
        post_data: The TikTok post data
        
    Returns:
        str: The transcript text or None if failed
    """
    try:
        logger.info("Getting TikTok transcript using Apify")
        
        # Get video URL from post data
        video_url = post_data.get('video_url') or post_data.get('url')
        if not video_url:
            logger.error("No video URL found in TikTok post data")
            return None
            
        # Get transcript using Apify
        transcript = get_apify_transcript([video_url])
        return transcript
        
    except Exception as e:
        logger.error(f"Error getting TikTok transcript: {str(e)}")
        return None

def get_video_transcript(platform: str, video_data: Dict[Any, Any], video_url: str = None) -> Optional[str]:
    """
    Main function to get video transcript based on platform.
    
    Args:
        platform: The platform (youtube, instagram, tiktok)
        video_data: The video post data
        video_url: Optional video URL (required for YouTube)
        
    Returns:
        str: The transcript text or None if failed
    """
    try:
        platform = platform.lower()
        
        if platform == 'youtube' and video_url:
            return get_youtube_transcript(video_url)
        elif platform == 'instagram':
            return get_instagram_transcript(video_data)
        elif platform == 'tiktok':
            return get_tiktok_transcript(video_data)
        else:
            logger.warning(f"Unsupported platform for transcript: {platform}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting video transcript for {platform}: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    #Test with TikTok URL from your test data
    test_data = {
        "url": "https://www.instagram.com/p/DOEnN-nj7jS/",
        "video_url": "https://instagram.fcae1-1.fna.fbcdn.net/o1/v/t16/f2/m86/AQM6hbiJZKShbpQq3VkYzhc35U-0xf5Mv23_X5xadQrimEq6CCGkFfg09-VEYL2T7bCK_LBxGvP9MgudVQhE3r75FRLNfk6exIMTlWQ.mp4?stp=dst-mp4&efg=eyJxZV9ncm91cHMiOiJbXCJpZ193ZWJfZGVsaXZlcnlfdnRzX290ZlwiXSIsInZlbmNvZGVfdGFnIjoidnRzX3ZvZF91cmxnZW4uY2xpcHMuYzIuNzIwLmJhc2VsaW5lIn0&_nc_cat=108&vs=764817839579715_3557508775&_nc_vs=HBksFQIYUmlnX3hwdl9yZWVsc19wZXJtYW5lbnRfc3JfcHJvZC84RDREMUI3QzJCMkNGNDBBQUQzMjIxNEYzMDE1NzA5MV92aWRlb19kYXNoaW5pdC5tcDQVAALIARIAFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HR3pKRENCVTEyTGNiNFVDQURTeTVaQkxaV04zYnFfRUFBQUYVAgLIARIAKAAYABsAFQAAJo7cxoz%2BqNY%2FFQIoAkMzLBdAQwU%2FfO2RaBgSZGFzaF9iYXNlbGluZV8xX3YxEQB1%2Fgdl5p0BAA%3D%3D&_nc_rid=e99228b883&ccb=9-4&oh=00_AfaAEExOwNQ9M8ty-0F3eOgmbZcm8s78LAQbbzKUo2bXyw&oe=68BA9AF5&_nc_sid=10d13b"
    }
    
    print("Testing instagram transcript extraction...")
    transcript = get_instagram_transcript(test_data)
    if transcript:
        print("instagram Transcript:")
        print(transcript)
    else:
        print("Failed to get instagram transcript")