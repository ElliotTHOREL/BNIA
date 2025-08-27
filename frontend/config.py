import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = f"http://localhost:{os.getenv('PORT_API')}"