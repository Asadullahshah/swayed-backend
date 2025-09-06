"""
Main FastAPI application for AI Content Suggestor.
Orchestrates the complete social media scraping and content processing pipeline.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime
import logging
import re
import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path

# Import configuration
try:
    from config import get_storage_path
except ImportError:
    def get_storage_path():
        return './tasks'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Content Suggestor - Complete Pipeline",
    description="Backend service for social media scraping, processing, and content selection",
    version="2.0.0"
)

# CORS middleware for web integration
allowed_origins = ["*"] if os.getenv('RENDER') else ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage for processing tasks with file persistence
processing_tasks = {}

def save_task_to_file(task_id: str, task_data: Dict[str, Any]):
    """Save task data to file for persistence"""
    try:
        tasks_dir = Path(get_storage_path())
        tasks_dir.mkdir(exist_ok=True, parents=True)
        task_file = tasks_dir / f'{task_id}.json'
        
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving task {task_id}: {e}")

def load_task_from_file(task_id: str) -> Optional[Dict[str, Any]]:
    """Load task data from file"""
    try:
        tasks_dir = Path(get_storage_path())
        task_file = tasks_dir / f'{task_id}.json'
        
        if task_file.exists():
            with open(task_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading task {task_id}: {e}")
    return None

# Pydantic Models
class ContentRequest(BaseModel):
    urls: List[str]
    
    @validator('urls')
    def validate_urls(cls, v):
        if len(v) < 1:
            raise ValueError('At least 1 URL is required')
        if len(v) > 10:
            raise ValueError('Maximum 10 URLs allowed')
        return v

class ProcessingResult(BaseModel):
    task_id: str
    status: str  # 'processing', 'completed', 'error'
    message: str
    urls_processed: Optional[List[Dict[str, Any]]] = None
    result_data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

# Platform Detection and URL Processing
def detect_platform(url: str) -> str:
    """Detect social media platform from URL"""
    url_lower = url.lower()
    
    if 'instagram.com' in url_lower:
        return 'instagram'
    elif 'linkedin.com' in url_lower:
        return 'linkedin'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'tiktok.com' in url_lower:
        return 'tiktok'
    else:
        return 'unknown'

def extract_username(url: str, platform: str) -> str:
    """Extract username from social media URL"""
    try:
        if platform == 'instagram':
            match = re.search(r'instagram\.com/([^/?]+)', url)
            return match.group(1) if match else ''
        elif platform == 'linkedin':
            match = re.search(r'linkedin\.com/(?:in|company)/([^/?]+)', url)
            return match.group(1) if match else ''
        elif platform == 'twitter':
            match = re.search(r'(?:twitter|x)\.com/([^/?]+)', url)
            return match.group(1) if match else ''
        elif platform == 'youtube':
            match = re.search(r'youtube\.com/(?:c/|@|channel/|user/)([^/?]+)', url)
            return match.group(1) if match else ''
        elif platform == 'tiktok':
            match = re.search(r'tiktok\.com/@([^/?]+)', url)
            return match.group(1) if match else ''
        return ''
    except Exception as e:
        logger.error(f"Error extracting username from {url}: {str(e)}")
        return ''

def update_scraper_url(scraper_path: str, platform: str, url: str) -> bool:
    """Update the URL in a scraper file dynamically"""
    try:
        with open(scraper_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Platform-specific URL variable patterns
        if platform == 'instagram':
            pattern = r'instagram_url = "[^"]*"'
            replacement = f'instagram_url = "{url}"'
        elif platform == 'linkedin':
            pattern = r'linkedin_url = "[^"]*"'
            replacement = f'linkedin_url = "{url}"'
        elif platform == 'twitter':
            pattern = r'twitter_url = "[^"]*"'
            replacement = f'twitter_url = "{url}"'
        elif platform == 'youtube':
            pattern = r'youtube_url = "[^"]*"'
            replacement = f'youtube_url = "{url}"'
        elif platform == 'tiktok':
            pattern = r'tiktok_url = "[^"]*"'
            replacement = f'tiktok_url = "{url}"'
        else:
            return False
        
        # Update the content
        updated_content = re.sub(pattern, replacement, content)
        
        # Write back to file
        with open(scraper_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        return True
    except Exception as e:
        logger.error(f"Error updating scraper {scraper_path}: {str(e)}")
        return False

def run_scraper(platform: str) -> bool:
    """Execute a specific platform scraper"""
    try:
        scrapers_dir = Path(__file__).parent / 'scrapers'
        scraper_file = scrapers_dir / f'{platform}.py'
        
        if not scraper_file.exists():
            logger.error(f"Scraper file not found: {scraper_file}")
            return False
        
        # Run the scraper with proper encoding handling
        result = subprocess.run(
            [sys.executable, str(scraper_file)],
            cwd=str(scrapers_dir),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',  # Ignore encoding errors
            timeout=300  # 5-minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully executed {platform} scraper")
            logger.info(f"Scraper output: {result.stdout}")
            return True
        else:
            logger.error(f"Error running {platform} scraper: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout running {platform} scraper")
        return False
    except Exception as e:
        logger.error(f"Exception running {platform} scraper: {str(e)}")
        return False

def run_retrieve_process() -> bool:
    """Execute retrieve.py to process scraped data"""
    try:
        retrieve_file = Path(__file__).parent / 'retrieve.py'
        
        result = subprocess.run(
            [sys.executable, str(retrieve_file)],
            cwd=str(Path(__file__).parent),
            capture_output=True,
            text=True,
            timeout=120  # 2-minute timeout
        )
        
        if result.returncode == 0:
            logger.info("Successfully executed retrieve.py")
            logger.info(f"Retrieve output: {result.stdout}")
            return True
        else:
            logger.error(f"Error running retrieve.py: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout running retrieve.py")
        return False
    except Exception as e:
        logger.error(f"Exception running retrieve.py: {str(e)}")
        return False

def run_results_process() -> bool:
    """Execute results.py to select and score content"""
    try:
        results_file = Path(__file__).parent / 'results.py'
        
        result = subprocess.run(
            [sys.executable, str(results_file)],
            cwd=str(Path(__file__).parent),
            capture_output=True,
            text=True,
            timeout=60  # 1-minute timeout
        )
        
        if result.returncode == 0:
            logger.info("Successfully executed results.py")
            logger.info(f"Results output: {result.stdout}")
            return True
        else:
            logger.error(f"Error running results.py: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout running results.py")
        return False
    except Exception as e:
        logger.error(f"Exception running results.py: {str(e)}")
        return False

def load_result_json() -> Optional[List[Dict[str, Any]]]:
    """Load the final result.json file"""
    try:
        result_file = Path(__file__).parent / 'result.json'
        if result_file.exists():
            with open(result_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.error("result.json file not found")
            return None
    except Exception as e:
        logger.error(f"Error loading result.json: {str(e)}")
        return None

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return {
        "message": "AI Content Suggestor - Complete Pipeline", 
        "version": "2.0.0",
        "description": "Social media scraping, processing, and content selection API"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/process-content")
async def process_content(request: ContentRequest, background_tasks: BackgroundTasks):
    """Main endpoint to process URLs through the complete pipeline"""
    try:
        # Generate task ID
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Analyze input URLs
        url_analysis = []
        platforms_needed = set()
        
        for i, url in enumerate(request.urls):
            platform = detect_platform(url)
            username = extract_username(url, platform)
            
            analysis = {
                "index": i + 1,
                "url": url,
                "platform": platform,
                "username": username,
                "status": "pending"
            }
            
            if platform != 'unknown':
                platforms_needed.add(platform)
            
            url_analysis.append(analysis)
            logger.info(f"URL {i+1}: {platform} - @{username} ({url})")
        
        # Initialize task status with file persistence
        processing_tasks[task_id] = {
            "status": "processing",
            "started_at": datetime.now().isoformat(),
            "urls_processed": url_analysis,
            "platforms_needed": list(platforms_needed),
            "total_urls": len(request.urls),
            "result_data": None,
            "error": None,
            "completed_at": None
        }
        
        # Save to file for persistence
        save_task_to_file(task_id, processing_tasks[task_id])
        
        # Start background processing
        background_tasks.add_task(process_pipeline, task_id, request.urls, url_analysis)
        
        logger.info(f"Started content processing task: {task_id}")
        logger.info(f"Platforms needed: {list(platforms_needed)}")
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": f"Started processing {len(request.urls)} URLs",
            "urls_detected": url_analysis,
            "platforms_needed": list(platforms_needed)
        }
        
    except Exception as e:
        logger.error(f"Error in process_content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{task_id}")
async def get_results(task_id: str):
    """Get the results of a processing task"""
    # Try to get from memory first
    task_data = processing_tasks.get(task_id)
    
    # If not in memory, try to load from file
    if not task_data:
        task_data = load_task_from_file(task_id)
        if task_data:
            processing_tasks[task_id] = task_data  # Cache in memory
    
    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    logger.info(f"Retrieved results for task: {task_id}")
    
    return {
        "task_id": task_id,
        "status": task_data["status"],
        "message": get_status_message(task_data["status"]),
        "started_at": task_data.get("started_at"),
        "completed_at": task_data.get("completed_at"),
        "urls_processed": task_data.get("urls_processed"),
        "platforms_needed": task_data.get("platforms_needed"),
        "result_data": task_data.get("result_data"),
        "error": task_data.get("error")
    }

def get_status_message(status: str) -> str:
    """Get descriptive message for status"""
    messages = {
        "processing": "Processing URLs through the complete pipeline...",
        "completed": "Content processing completed successfully!",
        "error": "An error occurred during processing."
    }
    return messages.get(status, "Unknown status")

# Background Processing Functions
async def process_pipeline(task_id: str, urls: List[str], url_analysis: List[Dict]):
    """Complete pipeline processing: scrapers → retrieve.py → results.py"""
    try:
        logger.info(f"Starting complete pipeline processing for task {task_id}")
        
        # Step 1: Group URLs by platform and update scrapers
        platforms_to_run = set()
        platform_urls = {}
        
        for analysis in url_analysis:
            platform = analysis['platform']
            url = analysis['url']
            
            if platform != 'unknown':
                platforms_to_run.add(platform)
                if platform not in platform_urls:
                    platform_urls[platform] = []
                platform_urls[platform].append(url)
        
        logger.info(f"Platforms to process: {list(platforms_to_run)}")
        logger.info(f"Platform URLs: {platform_urls}")
        
        # Step 2: Initialize temp_data.json and process ALL URLs
        temp_data_file = Path(__file__).parent / 'temp_data.json'
        
        # Clear temp_data.json at the start
        with open(temp_data_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
        logger.info("Initialized temp_data.json")
        
        scrapers_dir = Path(__file__).parent / 'scrapers'
        successful_scrapers = []
        failed_scrapers = []
        
        # Process each URL individually
        for analysis in url_analysis:
            platform = analysis['platform']
            url = analysis['url']
            
            if platform == 'unknown':
                continue
                
            try:
                logger.info(f"Processing {platform} with URL: {url}")
                
                # Update scraper file with this specific URL
                scraper_path = scrapers_dir / f'{platform}.py'
                if update_scraper_url(str(scraper_path), platform, url):
                    logger.info(f"Updated {platform} scraper with URL: {url}")
                    
                    # Run the scraper for this specific URL
                    if run_scraper(platform):
                        successful_scrapers.append(f"{platform}:{url}")
                        logger.info(f"Successfully completed {platform} scraping for {url}")
                    else:
                        failed_scrapers.append(f"{platform}:{url}")
                        logger.error(f"Failed to run {platform} scraper for {url}")
                else:
                    failed_scrapers.append(f"{platform}:{url}")
                    logger.error(f"Failed to update {platform} scraper for {url}")
                    
            except Exception as e:
                failed_scrapers.append(f"{platform}:{url}")
                logger.error(f"Error processing {platform} with {url}: {str(e)}")
        
        # Check if temp_data.json has any data
        with open(temp_data_file, 'r', encoding='utf-8') as f:
            temp_data = json.load(f)
            
        if not temp_data:
            raise Exception("No data was scraped from any URLs")
        
        logger.info(f"Collected {len(temp_data)} total items in temp_data.json")
        logger.info(f"Successful scrapers: {successful_scrapers}")
        logger.info(f"Failed scrapers: {failed_scrapers}")
        
        # Step 3: Run retrieve.py to process and unify scraped data
        logger.info("Starting data processing with retrieve.py...")
        if not run_retrieve_process():
            raise Exception("Failed to run retrieve.py data processing")
        
        logger.info("Data processing completed successfully")
        
        # Step 4: Run results.py to select and score content
        logger.info("Starting content selection with results.py...")
        if not run_results_process():
            raise Exception("Failed to run results.py content selection")
        
        logger.info("Content selection completed successfully")
        
        # Step 5: Load the final result.json
        result_data = load_result_json()
        if result_data is None:
            raise Exception("Failed to load final results from result.json")
        
        # Update task with completed results
        processing_tasks[task_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "result_data": result_data,
            "successful_scrapers": successful_scrapers,
            "failed_scrapers": failed_scrapers
        })
        
        # Save to file for persistence
        save_task_to_file(task_id, processing_tasks[task_id])
        
        logger.info(f"Pipeline processing completed successfully for task {task_id}")
        logger.info(f"Final result contains {len(result_data)} selected content items")
        
    except Exception as e:
        logger.error(f"Error in pipeline processing for task {task_id}: {str(e)}")
        processing_tasks[task_id].update({
            "status": "error",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })
        
        # Save to file for persistence
        save_task_to_file(task_id, processing_tasks[task_id])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)