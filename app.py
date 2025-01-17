from flask import Flask
import secrets
from src.routes import routes
import http.client as http_client
from anthropic import Anthropic
import os
from dotenv import load_dotenv


import logging
logger = logging.getLogger(__name__)

# Load environment variables and set up Anthropic client
load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')
client = Anthropic(api_key=api_key)

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
app.secret_key = secrets.token_hex(16)
app.register_blueprint(routes)

# Keep these warning level settings
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=True)
