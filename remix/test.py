import requests
import json

# Load the test data
test_data = {
    "remix_type": "script",
    "platform": "youtube",
    "content_type": "video",
    "type": "video",
    "url": "https://www.youtube.com/shorts/j83q29xCm9k",
    "text": "The Reality Check You Need 🔥 #motivation #inspiration #mindset",
    "video_url": "https://www.youtube.com/shorts/j83q29xCm9k",
    "image_urls": [
      "https://i.ytimg.com/vi/j83q29xCm9k/oar2.jpg?sqp=-oaymwEoCJUDENAFSFqQAgHyq4qpAxcIARUAAIhC2AEB4gEKCBgQAhgGOAFAAQ==&rs=AOn4CLAc3L9cLTWjx0XorQ1Ck-u7vxeiaw"
    ],
    "media_count": 1,
    "stats": {
      "views": 7600,
      "likes": 0,
      "comments": 0
    },
    "hashtags": [
      "motivation",
      "inspiration",
      "mindset"
    ],
    "author": {
      "name": "Motiversity",
      "subscribers_count": 0,
      "profile_url": "https://www.youtube.com/channel/UCAPByrKU5-R1emswVlyH_-g"
    },
    "URL_GROUP": "https://www.youtube.com/@motiversity/",
    "thumbnail_url": "https://i.ytimg.com/vi/j83q29xCm9k/oar2.jpg?sqp=-oaymwEoCJUDENAFSFqQAgHyq4qpAxcIARUAAIhC2AEB4gEKCBgQAhgGOAFAAQ==&rs=AOn4CLAc3L9cLTWjx0XorQ1Ck-u7vxeiaw"
  }

def test_remix_api():
    """Test the remix API endpoint"""
    url = "http://localhost:8001/remix"
    
    try:
        response = requests.post(url, json=test_data)
        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print(f"Status: {result['status']}")
            print(f"Remix Type: {result['remix_type']}")
            print(f"Post Number: {result['post_number']}")
            print("\nRemixed Content:")
            print("=" * 50)
            print(result.get('remixed_content', 'No content returned'))
            print("=" * 50)
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        print("Make sure the API server is running on port 8001")

if __name__ == "__main__":
    test_remix_api()