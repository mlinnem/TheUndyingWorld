from flask import Flask
import secrets
from routes import routes
import logging
from logging.handlers import RotatingFileHandler
import http.client as http_client
from anthropic import Anthropic
import os
from dotenv import load_dotenv

# Load environment variables and set up Anthropic client
load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')
client = Anthropic(api_key=api_key)

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
app.secret_key = secrets.token_hex(16)
app.register_blueprint(routes)

# Logger setup
class ColorCodes:
    RED = '\033[91m'
    RESET = '\033[0m'

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.ERROR:
            record.msg = f"{ColorCodes.RED}{record.msg}{ColorCodes.RESET}"
        return super().format(record)

# Update the logger configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = ColoredFormatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Set HTTP-related loggers to WARNING
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=True)
