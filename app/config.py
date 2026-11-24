import os


class Config:
    # Every request from the backend must carry this key (header: X-API-Key)
    AI_SERVICE_API_KEY = os.getenv("AI_SERVICE_API_KEY", "")
