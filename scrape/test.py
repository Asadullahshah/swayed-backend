#!/usr/bin/env python3
"""
Test script for the AI Content Suggestor API
Demonstrates how to use the complete pipeline API
"""

import requests
import json
import time

# API Configuration
API_BASE_URL = "http://localhost:8000"

# ========================================
# EDIT THESE URLs FOR TESTING
# ========================================
TEST_URLS = [
    "https://www.youtube.com/@motiversity/",
    "https://x.com/AndrewYNg", 
    "https://www.instagram.com/cristiano/",
    "https://www.linkedin.com/in/williamhgates/",
    "https://www.tiktok.com/@jennaezarik",
]
# ========================================



def test_api():
    """Test the complete pipeline API"""
    
    # Use predefined URLs from the top of the file
    test_urls = TEST_URLS
    
    if not test_urls:
        print("No URLs configured in TEST_URLS. Please edit the file and add URLs.")
        return
    
    print("AI Content Suggestor API Test")
    print("=" * 50)
    print("Testing with configured URLs:")
    for i, url in enumerate(test_urls, 1):
        print(f"  {i}. {url}")
    print()
    
    print(f"\nStarting API test with {len(test_urls)} URLs")
    print("=" * 50)
    
    # Step 1: Submit URLs for processing
    print("Step 1: Submitting URLs for processing...")
    payload = {
        "urls": test_urls
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/process-content", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result["task_id"]
            
            print(f"Task started successfully!")
            print(f"Task ID: {task_id}")
            print(f"URLs submitted: {len(test_urls)}")
            print(f"Platforms detected: {', '.join(result['platforms_needed'])}")
            print()
            
            # Step 2: Poll for results
            print("Step 2: Waiting for processing to complete...")
            max_attempts = 60  # 5 minutes with 5-second intervals
            attempt = 0
            
            while attempt < max_attempts:
                time.sleep(5)  # Wait 5 seconds between polls
                attempt += 1
                
                try:
                    status_response = requests.get(f"{API_BASE_URL}/results/{task_id}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        current_status = status_data["status"]
                        
                        print(f"Attempt {attempt}: Status = {current_status}")
                        
                        if current_status == "completed":
                            print("\nProcessing completed successfully!")
                            print("Final Results:")
                            print("=" * 30)
                            
                            result_data = status_data.get("result_data", [])
                            
                            if result_data:
                                print(f"Total selected posts: {len(result_data)}")
                                
                                # Display summary of results
                                platforms = {}
                                for item in result_data:
                                    platform = item.get('platform', 'unknown')
                                    platforms[platform] = platforms.get(platform, 0) + 1
                                
                                print(f"Platform distribution:")
                                for platform, count in platforms.items():
                                    print(f"   - {platform.title()}: {count} posts")
                                
                                print(f"\nTop 3 selected posts:")
                                for i, item in enumerate(result_data[:3], 1):
                                    post_num = item.get('post_number', f'post_{i}')
                                    platform = item.get('platform', '').title()
                                    content_type = item.get('type', 'post')
                                    score = item.get('engagement_score', 0)
                                    url_group = item.get('URL_GROUP', 'N/A')
                                    
                                    print(f"   {i}. {post_num}: {platform} {content_type} (Score: {score:.2f})")
                                    print(f"      Source: {url_group}")
                                
                                # Save results to file
                                with open('api_test_results.json', 'w', encoding='utf-8') as f:
                                    json.dump(result_data, f, indent=2, ensure_ascii=False)
                                
                                print(f"\nFull results saved to: api_test_results.json")
                                
                            else:
                                print("No result data found")
                            
                            break
                            
                        elif current_status == "error":
                            print(f"\nProcessing failed!")
                            error_msg = status_data.get("error", "Unknown error")
                            print(f"Error: {error_msg}")
                            break
                            
                    else:
                        print(f"Error checking status: {status_response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"Connection error: {e}")
                    
            if attempt >= max_attempts:
                print(f"\nTimeout: Processing took longer than expected")
                
        else:
            print(f"Failed to start processing: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        print(f"Make sure the API server is running on {API_BASE_URL}")

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("API is healthy and running")
            return True
        else:
            print(f"API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Cannot connect to API: {e}")
        print(f"Make sure to start the server with: python main.py")
        return False

if __name__ == "__main__":
    print("Testing API health...")
    if test_health_check():
        print()
        test_api()
    else:
        print("\nAPI is not accessible. Please start the server first.")
        print("To start the server, run: python main.py")