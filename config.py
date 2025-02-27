import os
from dotenv import load_dotenv

# Google Cloud Platform envs stored as one giant secret
if os.getenv("ENV"):
    with open('.env', 'w') as f:
        f.write(os.getenv("ENV"))

# Load environment variables from .env
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GOOGLE_SERVICE_ACCOUNT = os.getenv("GOOGLE_SERVICE_ACCOUNT")