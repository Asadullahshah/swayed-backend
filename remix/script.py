"""
Simple script processing module.
Identifies content type and calls appropriate processing function.
"""

import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_twitter_thread(post_data: Dict[str, Any]) -> str:
    """Process Twitter thread content"""
    logger.info(f"Processing Twitter thread: {post_data.get('post_number', 'unknown')}")
    
    # Extract all tweet texts to create a combined thread
    tweets = post_data.get('tweets', [])
    thread_texts = []
    
    for tweet in tweets:
        tweet_number = tweet.get('tweet_number', 'unknown')
        tweet_text = tweet.get('text', '')
        thread_texts.append(f"Tweet {tweet_number}: {tweet_text}")
    
    combined_thread = "\n\n".join(thread_texts)
    
    # Create GPT prompt for thread processing
    prompt = f"""You are an expert copywriter creating a Twitter thread. 
I'll give you an original thread as inspiration. Please rewrite it for me using:
- Simple, human language for a wide audience
- Copy the general language style of the original thread
- Keep it engaging and natural
- Format it clearly as a thread with numbered steps
- Each tweet should be concise and impactful
- Maintain the core message and flow of the original
- Ensure proper spacing and formatting for readability
- Dont add emojis or other non-text elements

Original thread:
{combined_thread}

Please create a new version based on this content, formatted as a proper Twitter thread with numbered tweets."""

    # Import and use GPT function
    try:
        from support.gpt import chat_completion
        result = chat_completion(prompt)
        return result
    except Exception as e:
        logger.error(f"Error using GPT: {str(e)}")
        return f"[TWITTER THREAD SCRIPT] Processing thread {post_data.get('post_number', 'unknown')}"

def process_text_post(post_data: Dict[str, Any]) -> str:
    """Process text-based posts (Twitter tweets, LinkedIn posts)"""
    platform = post_data.get('platform', 'unknown')
    logger.info(f"Processing {platform} text post: {post_data.get('post_number', 'unknown')}")
    
    # Create GPT prompt for text post processing
    original_text = post_data.get('text', '')
    prompt = f"""You are an expert copywriter creating content for {platform}. 
I'll give you a post as inspiration. Please rewrite it for me using:
- Simple, human language for a wide audience
- Copy the general language style of the original text
- Keep it engaging and natural
- Format the content well with proper spacing
- Maintain the core message and tone
- Dont add emojis or other non-text elements

Original post:
{original_text}

Please create a new version based on this content with improved formatting."""

    # Import and use GPT function
    try:
        from support.gpt import chat_completion
        result = chat_completion(prompt)
        return result
    except Exception as e:
        logger.error(f"Error using GPT: {str(e)}")
        return f"[{platform.upper()} TEXT POST SCRIPT] Processing post {post_data.get('post_number', 'unknown')}"

def process_video_post(post_data: Dict[str, Any]) -> str:
    """Process video-based posts (Instagram, YouTube, TikTok)"""
    platform = post_data.get('platform', 'unknown')
    logger.info(f"Processing {platform} video post: {post_data.get('post_number', 'unknown')}")
    
    # For video posts, we need to get the transcript first
    try:
        from support.transcript import get_video_transcript
        
        # Get video URL (different platforms may have different fields)
        video_url = post_data.get('video_url') or post_data.get('url')
        logger.info(f"Video URL for transcript: {video_url}")
        
        # Get transcript
        transcript = get_video_transcript(platform, post_data, video_url)
        logger.info(f"Transcript result: {transcript}")
        
        if transcript:
            # Create GPT prompt for video transcript processing
            prompt = f"""You are an expert copywriter creating content for {platform}. 
I'll give you a video transcript as inspiration. Please rewrite it for me using:
- Simple, human language for a wide audience
- Copy the general language style of the original content
- Keep it engaging and natural
- Format the content well with proper spacing
- Maintain the core message and tone
- Dont add emojis or other non-text elements

Video transcript:
{transcript}

Please create a new version based on this content with improved formatting."""
            
            # Import and use GPT function
            try:
                from support.gpt import chat_completion
                result = chat_completion(prompt)
                return result
            except Exception as e:
                logger.error(f"Error using GPT: {str(e)}")
                return f"[{platform.upper()} VIDEO POST SCRIPT] Processing post {post_data.get('post_number', 'unknown')} with transcript"
        else:
            # Fallback if no transcript available
            return f"[{platform.upper()} VIDEO POST SCRIPT] Processing post {post_data.get('post_number', 'unknown')} - Transcript not available"
            
    except Exception as e:
        logger.error(f"Error processing video post: {str(e)}")
        return f"[{platform.upper()} VIDEO POST SCRIPT] Error processing post {post_data.get('post_number', 'unknown')}"

def process_content(post_data: Dict[str, Any], remix_instruction: str) -> str:
    """
    Main function to process content based on type.
    
    Args:
        post_data: The complete post data
        remix_instruction: User's specific instruction for remixing
        
    Returns:
        str: The remixed content
    """
    try:
        logger.info(f"Processing post {post_data.get('post_number', 'unknown')} as script")
        
        # Extract platform and content type
        platform = post_data.get('platform', '').lower()
        content_type = post_data.get('content_type', '').lower()
        
        # Determine which function to call based on content type
        if platform == 'twitter' and content_type == 'thread':
            return process_twitter_thread(post_data)
        elif platform in ['twitter', 'linkedin']:
            return process_text_post(post_data)
        elif platform in ['youtube', 'instagram', 'tiktok']:
            return process_video_post(post_data)
        else:
            # Default fallback
            logger.warning(f"Unknown platform/content type: {platform}/{content_type}")
            return f"[UNKNOWN CONTENT TYPE] Processing post {post_data.get('post_number', 'unknown')}"
            
    except Exception as e:
        logger.error(f"Error processing content as script: {str(e)}")
        return f"Error processing content as script: {str(e)}"