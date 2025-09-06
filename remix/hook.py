"""
Hook generation module.
Creates catchy hooks for social media content based on platform and content type.
"""

import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_twitter_hook(post_data: Dict[str, Any]) -> str:
    """Generate a hook for Twitter content"""
    logger.info(f"Generating Twitter hook for post: {post_data.get('post_number', 'unknown')}")
    
    # For Twitter threads, use combined text; for single tweets, use text
    if post_data.get('content_type') == 'thread':
        content_text = post_data.get('combined_text', '')
    else:
        content_text = post_data.get('text', '')
    
    prompt = f"""You are a professional hook writer who makes catchy hooks for Twitter content.
Based on this data, what would be a good hook that grabs attention and encourages engagement?

Content data:
{content_text}

Rules:
- Keep it short and impactful (under 280 characters)
- Use curiosity or emotion to draw readers in
- Make it relevant to the content
- Don't add emojis unless they're in the original
- Don't add hashtags unless they're in the original
- Dont make a hook that's too long
- Dont add a hook that's too wordy"""

    # Import and use GPT function
    try:
        from support.gpt import chat_completion
        result = chat_completion(prompt)
        return result
    except Exception as e:
        logger.error(f"Error generating Twitter hook: {str(e)}")
        return f"[TWITTER HOOK] Error generating hook for post {post_data.get('post_number', 'unknown')}"

def generate_instagram_hook(post_data: Dict[str, Any]) -> str:
    """Generate a hook for Instagram content"""
    logger.info(f"Generating Instagram hook for post: {post_data.get('post_number', 'unknown')}")
    
    content_text = post_data.get('text', '')
    
    prompt = f"""You are a professional hook writer who makes catchy hooks for Instagram content.
Based on this data, what would be a good hook that grabs attention and encourages engagement?

Content data:
{content_text}

Rules:
- Keep it engaging and conversational
- Use curiosity or emotion to draw readers in
- Make it relevant to the content
- Consider using questions or statements that encourage comments
- Don't add emojis unless they're in the original
- Don't add hashtags unless they're in the original
- Dont make a hook that's too long
- Dont add a hook that's too wordy"""

    # Import and use GPT function
    try:
        from support.gpt import chat_completion
        result = chat_completion(prompt)
        return result
    except Exception as e:
        logger.error(f"Error generating Instagram hook: {str(e)}")
        return f"[INSTAGRAM HOOK] Error generating hook for post {post_data.get('post_number', 'unknown')}"

def generate_linkedin_hook(post_data: Dict[str, Any]) -> str:
    """Generate a hook for LinkedIn content"""
    logger.info(f"Generating LinkedIn hook for post: {post_data.get('post_number', 'unknown')}")
    
    content_text = post_data.get('text', '')
    
    prompt = f"""You are a professional hook writer who makes catchy hooks for LinkedIn content.
Based on this data, what would be a good hook that grabs attention and encourages professional engagement?

Content data:
{content_text}

Rules:
- Keep it professional but engaging
- Use curiosity or value proposition to draw readers in
- Make it relevant to professionals and career-focused audience
- Consider using questions or statements that encourage thoughtful comments
- Don't add emojis unless they're in the original
- Don't add hashtags unless they're in the original
- Dont make a hook that's too long
- Dont add a hook that's too wordy"""

    # Import and use GPT function
    try:
        from support.gpt import chat_completion
        result = chat_completion(prompt)
        return result
    except Exception as e:
        logger.error(f"Error generating LinkedIn hook: {str(e)}")
        return f"[LINKEDIN HOOK] Error generating hook for post {post_data.get('post_number', 'unknown')}"

def generate_youtube_hook(post_data: Dict[str, Any]) -> str:
    """Generate a hook for YouTube content"""
    logger.info(f"Generating YouTube hook for post: {post_data.get('post_number', 'unknown')}")
    
    content_text = post_data.get('text', '')  # Video title
    description = post_data.get('description', '')
    combined_text = f"{content_text}\n\n{description}" if description else content_text
    
    prompt = f"""You are a professional hook writer who makes catchy hooks for YouTube content.
Based on this data, what would be a good hook that grabs attention and encourages clicks?

Content data:
{combined_text}

Rules:
- Keep it engaging and curiosity-driven
- Make it relevant to the video content
- Encourage viewers to watch the video
- Don't add emojis unless they're in the original
- Don't add hashtags unless they're in the original
- Dont make a hook that's too long
- Dont add a hook that's too wordy"""

    # Import and use GPT function
    try:
        from support.gpt import chat_completion
        result = chat_completion(prompt)
        return result
    except Exception as e:
        logger.error(f"Error generating YouTube hook: {str(e)}")
        return f"[YOUTUBE HOOK] Error generating hook for post {post_data.get('post_number', 'unknown')}"

def generate_tiktok_hook(post_data: Dict[str, Any]) -> str:
    """Generate a hook for TikTok content"""
    logger.info(f"Generating TikTok hook for post: {post_data.get('post_number', 'unknown')}")
    
    content_text = post_data.get('text', '')
    
    prompt = f"""You are a professional hook writer who makes catchy hooks for TikTok content.
Based on this data, what would be a good hook that grabs attention and encourages engagement?

Content data:
{content_text}

Rules:
- Keep it short, snappy, and attention-grabbing
- Use trending language or slang if appropriate
- Make it relevant to the content
- Encourage users to engage (like, comment, share)
- Don't add emojis unless they're in the original
- Don't add hashtags unless they're in the original
- Dont make a hook that's too long
- Dont add a hook that's too wordy"""

    # Import and use GPT function
    try:
        from support.gpt import chat_completion
        result = chat_completion(prompt)
        return result
    except Exception as e:
        logger.error(f"Error generating TikTok hook: {str(e)}")
        return f"[TIKTOK HOOK] Error generating hook for post {post_data.get('post_number', 'unknown')}"

def process_content(post_data: Dict[str, Any], remix_instruction: str) -> str:
    """
    Main function to generate hooks based on content type.
    
    Args:
        post_data: The complete post data
        remix_instruction: User's specific instruction for remixing (not used for hooks)
        
    Returns:
        str: The generated hook
    """
    try:
        logger.info(f"Generating hook for post {post_data.get('post_number', 'unknown')}")
        
        # Extract platform
        platform = post_data.get('platform', '').lower()
        
        # Determine which function to call based on platform
        if platform == 'twitter':
            return generate_twitter_hook(post_data)
        elif platform == 'instagram':
            return generate_instagram_hook(post_data)
        elif platform == 'linkedin':
            return generate_linkedin_hook(post_data)
        elif platform == 'youtube':
            return generate_youtube_hook(post_data)
        elif platform == 'tiktok':
            return generate_tiktok_hook(post_data)
        else:
            # Default fallback
            logger.warning(f"Unknown platform: {platform}")
            prompt = f"""You are a professional hook writer who makes catchy hooks for social media content.
Based on this data from {platform}, what would be a good hook?

Content data:
{post_data.get('text', '')}

Rules:
- Keep it engaging and attention-grabbing
- Make it relevant to the content
- Don't add emojis unless they're in the original
- Don't add hashtags unless they're in the original
- Dont make a hook that's too long
- Dont add a hook that's too wordy"""
            
            try:
                from support.gpt import chat_completion
                result = chat_completion(prompt)
                return result
            except Exception as e:
                logger.error(f"Error generating generic hook: {str(e)}")
                return f"[GENERIC HOOK] Error generating hook for post {post_data.get('post_number', 'unknown')}"
            
    except Exception as e:
        logger.error(f"Error generating hook: {str(e)}")
        return f"Error generating hook: {str(e)}"