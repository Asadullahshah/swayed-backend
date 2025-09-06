from fastapi import FastAPI, Request
from typing import Dict, Any
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Import the script and hook modules
try:
    import script
    logger.info("Successfully imported script module")
except ImportError as e:
    logger.error(f"Failed to import script module: {e}")
    script = None

try:
    import hook
    logger.info("Successfully imported hook module")
except ImportError as e:
    logger.error(f"Failed to import hook module: {e}")
    hook = None

@app.post("/remix")
async def remix_content(request: Request):
    # Receive raw JSON data
    data = await request.json()
    
    print("Received remix request:")
    print(f"Remix type: {data.get('remix_type', 'unknown')}")
    print(f"Platform: {data.get('platform', 'unknown')}")
    print(f"Content type: {data.get('content_type', 'unknown')}")
    print(f"Post number: {data.get('post_number', 'unknown')}")
    
    # Process based on remix_type
    remix_type = data.get('remix_type', 'unknown')
    result_content = ""
    if remix_type == 'script' and script:
        print("Calling script.process_content function")
        result_content = script.process_content(data, "Sample instruction")
        print(f"Script processing result: {result_content}")
    elif remix_type == 'hook' and hook:
        print("Calling hook.process_content function")
        result_content = hook.process_content(data, "Sample instruction")
        print(f"Hook processing result: {result_content}")
    else:
        print(f"No processing function called for remix_type: {remix_type}")
        result_content = "No processing performed"
    
    return {
        "status": "success",
        "message": "Data received and processed",
        "remix_type": remix_type,
        "post_number": data.get('post_number', 'unknown'),
        "remixed_content": result_content
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)