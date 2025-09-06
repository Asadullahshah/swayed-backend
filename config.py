import os

# Environment configuration for deployment
def get_storage_path():
    """Get appropriate storage path for different environments"""
    if os.getenv('RENDER'):
        # On Render, use /tmp for temporary files
        return '/tmp/tasks'
    else:
        # Local development
        return './tasks'

# You can also use environment-based database URLs
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./local.db')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')