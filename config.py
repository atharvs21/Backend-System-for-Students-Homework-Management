from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# MongoDB credentials
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')

# Together API key
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
