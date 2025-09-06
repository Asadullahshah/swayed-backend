from dotenv import load_dotenv
import os

load_dotenv()  # loads .env file into environment

# Get API keys from environment variables
OPENAI_KEY = os.getenv('OPENAI_KEY')
APIFY_KEY = os.getenv('APIFY_KEY')

# Validate that required keys are present
if not OPENAI_KEY:
    print("WARNING: OPENAI_KEY not found in environment variables")
if not APIFY_KEY:
    print("WARNING: APIFY_KEY not found in environment variables")

model = "gpt-4o-mini"