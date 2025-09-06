# AI Content Suggestor API

A FastAPI-based service that orchestrates the complete social media content scraping and selection pipeline.

## 🚀 Features

- **Multi-platform support**: Instagram, LinkedIn, Twitter/X, YouTube, TikTok
- **Complete pipeline**: Scraping → Processing → Content Selection
- **Intelligent scoring**: Platform-specific engagement algorithms
- **Even distribution**: Content balanced across URL groups
- **Post numbering**: Sequential numbering (post_1, post_2, etc.)
- **Async processing**: Background tasks for long-running operations

## 📋 API Endpoints

### `POST /process-content`

Submit URLs for complete pipeline processing.

**Request Body:**
```json
{
  "urls": [
    "https://www.instagram.com/natgeo/",
    "https://www.linkedin.com/in/andrewyng/",
    "https://x.com/theinsiderzclub",
    "https://www.youtube.com/@NatGeo",
    "https://www.tiktok.com/@natgeo"
  ]
}
```

**Response:**
```json
{
  "task_id": "task_20231203_143022_123456",
  "status": "started",
  "message": "Started processing 5 URLs",
  "urls_detected": [...],
  "platforms_needed": ["instagram", "linkedin", "twitter", "youtube", "tiktok"]
}
```

### `GET /results/{task_id}`

Get processing results for a specific task.

**Response:**
```json
{
  "task_id": "task_20231203_143022_123456",
  "status": "completed",
  "result_data": [
    {
      "post_number": "post_1",
      "platform": "twitter",
      "content_type": "tweet",
      "type": "text",
      "text": "Amazing content...",
      "stats": {
        "views": 15420,
        "likes": 892,
        "retweets": 156,
        "replies": 43
      },
      "author": {
        "name": "The Insiders Club",
        "username": "theinsiderzclub",
        "profile_url": "https://x.com/theinsiderzclub"
      },
      "engagement_score": 1245.67,
      "URL_GROUP": "https://x.com/theinsiderzclub"
    }
  ]
}
```

### `GET /health`

Health check endpoint.

## 🛠️ Setup and Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Make sure your `.env` file contains:
```
APIFY_KEY=your_apify_api_key
OPENAI_KEY=your_openai_api_key
```

### 3. Start the Server

```bash
# Navigate to the scrape directory
cd scrape

# Start the FastAPI server
python main.py
```

The API will be available at `http://localhost:8000`

### 4. Test the API

#### Using the Test Script
```bash
python test_api.py
```

#### Using curl
```bash
# Submit URLs for processing
curl -X POST "http://localhost:8000/process-content" \
     -H "Content-Type: application/json" \
     -d '{
       "urls": [
         "https://www.instagram.com/natgeo/",
         "https://x.com/theinsiderzclub"
       ]
     }'

# Check results (replace with actual task_id)
curl "http://localhost:8000/results/task_20231203_143022_123456"
```

#### Using Python requests
```python
import requests
import time

# Submit URLs
response = requests.post("http://localhost:8000/process-content", json={
    "urls": [
        "https://www.instagram.com/natgeo/",
        "https://x.com/theinsiderzclub"
    ]
})

task_id = response.json()["task_id"]

# Poll for results
while True:
    result = requests.get(f"http://localhost:8000/results/{task_id}")
    status = result.json()["status"]
    
    if status == "completed":
        final_data = result.json()["result_data"]
        print(f"Got {len(final_data)} selected posts!")
        break
    elif status == "error":
        print("Processing failed:", result.json()["error"])
        break
    
    time.sleep(5)  # Wait 5 seconds before checking again
```

## 🎯 Pipeline Process

1. **URL Analysis**: Detect platforms and extract usernames
2. **Dynamic Scraper Update**: Update scraper files with provided URLs
3. **Parallel Scraping**: Execute platform-specific scrapers
4. **Data Processing**: Run `retrieve.py` to unify and standardize data
5. **Content Selection**: Run `results.py` to score and select top 9 posts
6. **Result Generation**: Return final `result.json` with post numbering

## 📊 Scoring Algorithm

### Platform-Specific Formulas

- **Twitter**: `Views × 0.3 + (Likes × 2 + Retweets × 3 + Replies × 1.5)`
- **LinkedIn**: `Comments × 5 + Likes × 1`
- **YouTube**: `Views × 0.1`
- **TikTok**: `Views × 0.2`
- **Instagram**: `Views × 0.5`

### Content Distribution

- Target: 9 posts total
- Even distribution across unique URL groups
- Fallback to multiples of 3 (9 → 6 → 3) if insufficient content
- Highest scoring content prioritized within each group

## 🔧 Configuration

### Scraper Timeouts
- Individual scrapers: 5 minutes
- Data processing: 2 minutes
- Content selection: 1 minute

### URL Limits
- Minimum: 1 URL
- Maximum: 10 URLs per request

### Supported Platforms
- ✅ Instagram (`instagram.com`)
- ✅ LinkedIn (`linkedin.com`)
- ✅ Twitter/X (`twitter.com`, `x.com`)
- ✅ YouTube (`youtube.com`, `youtu.be`)
- ✅ TikTok (`tiktok.com`)

## 📁 File Structure

```
scrape/
├── main.py              # FastAPI application
├── retrieve.py          # Data processing
├── results.py           # Content selection
├── test_api.py          # API test script
├── scrapers/
│   ├── instagram.py     # Instagram scraper
│   ├── linkedin.py      # LinkedIn scraper
│   ├── twitter.py       # Twitter scraper
│   ├── youtube.py       # YouTube scraper
│   └── tiktok.py        # TikTok scraper
├── data.json           # Processed data (intermediate)
└── result.json         # Final selected content
```

## 🐛 Troubleshooting

### Common Issues

1. **"Task not found"**: The task_id has expired or doesn't exist
2. **"All scrapers failed"**: Check APIFY_KEY configuration
3. **Timeout errors**: Scrapers may take longer for accounts with lots of content
4. **Connection refused**: Make sure the server is running on port 8000

### Logs

Check the console output and `log.txt` file for detailed error messages.

### Debug Mode

Set logging level to DEBUG in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## 🔒 Security Notes

- Configure CORS properly for production
- Implement rate limiting
- Add authentication if needed
- Validate and sanitize URL inputs