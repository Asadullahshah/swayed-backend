import json
import os
from collections import defaultdict
import math

def load_data():
    """Load data from data.json"""
    scrape_dir = os.path.dirname(__file__)
    data_file = os.path.join(scrape_dir, "data.json")
    
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {data_file} not found")
        return []

def calculate_score(item):
    """Calculate engagement score for each platform"""
    platform = item.get('platform', '').lower()
    
    # For Twitter threads, use combined_stats; for regular posts, use stats
    if platform == 'twitter' and item.get('content_type') == 'thread':
        stats = item.get('combined_stats', {})
    else:
        stats = item.get('stats', {})
    
    if platform == 'twitter':
        # Twitter: Views + Engagement (likes + retweets + replies)
        views = safe_int(stats.get('views', 0))
        likes = safe_int(stats.get('likes', 0))
        retweets = safe_int(stats.get('retweets', 0))
        replies = safe_int(stats.get('replies', 0))
        
        # Formula: Views * 0.3 + (Likes * 2 + Retweets * 3 + Replies * 1.5)
        # Retweets weighted highest as they show viral potential
        engagement_score = (likes * 2) + (retweets * 3) + (replies * 1.5)
        total_score = (views * 0.3) + engagement_score
        
    elif platform == 'linkedin':
        # LinkedIn: Comments and Likes (comments weighted higher)
        comments = safe_int(stats.get('comments', 0))
        likes = safe_int(stats.get('likes', 0))
        
        # Formula: Comments * 5 + Likes * 1 (comments are more valuable on LinkedIn)
        total_score = (comments * 5) + likes
        
    elif platform in ['youtube', 'tiktok', 'instagram']:
        # YouTube, TikTok, Instagram: Views only
        views = safe_int(stats.get('views', 0))
        
        # Formula: Views with platform-specific multipliers
        if platform == 'youtube':
            # YouTube views are generally higher, so lower multiplier
            total_score = views * 0.1
        elif platform == 'tiktok':
            # TikTok views can be very high, moderate multiplier
            total_score = views * 0.2
        else:  # instagram
            # Instagram views are typically lower, higher multiplier
            total_score = views * 0.5
    else:
        total_score = 0
    
    return max(total_score, 0)  # Ensure non-negative score

def safe_int(value):
    """Safely convert value to int, return 0 if conversion fails"""
    try:
        if value is None:
            return 0
        if isinstance(value, str) and value.isdigit():
            return int(value)
        elif isinstance(value, (int, float)):
            return int(value)
        else:
            return 0
    except (ValueError, TypeError):
        return 0

def get_url_group(item):
    """Extract URL_GROUP for grouping"""
    return item.get('URL_GROUP', '')

def select_top_content(data, target_total=9):  # Back to 9 as per specifications
    """Select top content ensuring even distribution across unique URL_GROUPs"""
    if not data:
        return []
    
    # Group content by URL_GROUP
    url_group_groups = defaultdict(list)
    
    for item in data:
        url_group = get_url_group(item)
        if url_group:  # Only include items with valid URL_GROUP
            # Calculate score and add to item
            score = calculate_score(item)
            item_with_score = item.copy()
            item_with_score['engagement_score'] = score
            url_group_groups[url_group].append(item_with_score)
    
    if not url_group_groups:
        return []
    
    # Sort each URL_GROUP's content by score (highest first)
    for url_group in url_group_groups:
        url_group_groups[url_group].sort(key=lambda x: x['engagement_score'], reverse=True)
    
    unique_url_groups = len(url_group_groups)
    total_available_posts = sum(len(posts) for posts in url_group_groups.values())
    
    print(f"Found content from {unique_url_groups} unique URL groups")
    print(f"Total available posts: {total_available_posts}")
    
    # Calculate distribution with multiples of 3 priority
    if unique_url_groups == 0:
        return []
    
    # Determine actual target based on available content
    actual_target = min(target_total, total_available_posts)
    
    # If we can't make exactly 9, prioritize multiples of 3
    if actual_target < target_total:
        # Find the largest multiple of 3 that's <= actual_target
        multiples_of_3 = [9, 6, 3]
        for multiple in multiples_of_3:
            if multiple <= actual_target:
                actual_target = multiple
                print(f"Adjusted target to {actual_target} (multiple of 3)")
                break
        else:
            # If can't even make 3, just use what we have
            print(f"Using all available content: {actual_target} posts")
    
    # Calculate distribution
    base_posts_per_url_group = actual_target // unique_url_groups
    extra_posts = actual_target % unique_url_groups
    
    print(f"Target distribution: {base_posts_per_url_group} posts per URL group")
    if extra_posts > 0:
        print(f"{extra_posts} URL groups will get 1 extra post")
    
    # Select content
    selected_content = []
    url_groups = list(url_group_groups.keys())
    
    # First, give each URL group their base allocation
    for url_group in url_groups:
        available_content = url_group_groups[url_group]
        posts_to_take = min(base_posts_per_url_group, len(available_content))
        
        for i in range(posts_to_take):
            selected_content.append(available_content[i])
    
    # Then distribute extra posts to URL groups with highest scoring remaining content
    remaining_content = []
    for url_group in url_groups:
        available_content = url_group_groups[url_group]
        if len(available_content) > base_posts_per_url_group:
            # Add remaining content with URL group identifier
            for i in range(base_posts_per_url_group, len(available_content)):
                content_item = available_content[i].copy()
                content_item['source_url_group'] = url_group
                remaining_content.append(content_item)
    
    # Sort remaining content by score and take the best ones
    remaining_content.sort(key=lambda x: x['engagement_score'], reverse=True)
    
    # Add extra posts until we reach the target
    for i in range(min(extra_posts, len(remaining_content))):
        content_item = remaining_content[i]
        # Remove the temporary field
        del content_item['source_url_group']
        selected_content.append(content_item)
    
    # Sort final selection by score (highest first)
    selected_content.sort(key=lambda x: x['engagement_score'], reverse=True)
    
    return selected_content[:actual_target]  # Ensure we don't exceed target

def generate_results():
    """Main function to generate results.json"""
    print("Starting content selection process...")
    
    # Load data
    data = load_data()
    if not data:
        print("No data found to process")
        return
    
    print(f"Loaded {len(data)} total content items")
    
    # Select top content
    selected_content = select_top_content(data, target_total=9)  # Back to 9 as per specifications
    
    if not selected_content:
        print("No content selected")
        return
    
    # Add post numbering to selected content
    for i, item in enumerate(selected_content, 1):
        item['post_number'] = f"post_{i}"
    
    # Generate summary statistics
    platform_counts = defaultdict(int)
    url_group_counts = defaultdict(int)
    total_score = 0
    
    for item in selected_content:
        platform_counts[item['platform']] += 1
        url_group = get_url_group(item)
        if url_group:
            url_group_counts[url_group] += 1
        total_score += item.get('engagement_score', 0)
    
    # Save results
    scrape_dir = os.path.dirname(__file__)
    results_file = os.path.join(scrape_dir, "result.json")
    
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(selected_content, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\nContent selection completed!")
    print(f"Results saved to: {results_file}")
    print(f"Selected {len(selected_content)} items (target: 9, actual: {len(selected_content)})")
    if len(selected_content) != 9:
        if len(selected_content) in [3, 6]:
            print(f"Used multiple of 3 strategy due to limited content")
        else:
            print(f"Limited content available, used all {len(selected_content)} items")
    print(f"Total engagement score: {total_score:.2f}")
    
    print(f"\nPlatform distribution:")
    for platform, count in sorted(platform_counts.items()):
        print(f"   - {platform.title()}: {count} items")
    
    print(f"\nURL Group distribution:")
    for url_group, count in sorted(url_group_counts.items()):
        # Extract username from URL for display
        username = url_group.split('/')[-1] if url_group else 'Unknown'
        # Remove common URL patterns to get clean username
        if username.startswith('@'):
            username = username[1:]  # Remove leading @
        username = username or 'Unknown'
        print(f"   - @{username}: {count} items")
    
    print(f"\nTop 3 scoring items:")
    for i, item in enumerate(selected_content[:3], 1):
        platform = item['platform'].title()
        score = item.get('engagement_score', 0)
        content_type = item.get('type', 'post')
        url_group = get_url_group(item)
        username = url_group.split('/')[-1] if url_group else 'Unknown'
        post_number = item.get('post_number', f'post_{i}')
        print(f"   {i}. {post_number}: {platform} {content_type} by @{username} (Score: {score:.2f})")

if __name__ == "__main__":
    generate_results()