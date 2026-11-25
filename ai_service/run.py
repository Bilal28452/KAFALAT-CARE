import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

from ai_service.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("AI_SERVICE_PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")
