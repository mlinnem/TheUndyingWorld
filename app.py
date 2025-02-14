from flask import Flask
import secrets
from server_code.routes import routes
import http.client as http_client
from anthropic import Anthropic
import os
from dotenv import load_dotenv
from server_code.logger_config import setup_logging

# Initialize logging first
setup_logging()

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load environment variables and set up Anthropic client
load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')
client = Anthropic(api_key=api_key)

# Get the absolute path to the project root directory
root_dir = os.path.dirname(os.path.abspath(__file__))

# Initialize Flask app with correct template and static folders using absolute paths
app = Flask(__name__, 
           template_folder=os.path.join(root_dir, 'templates'),
           static_folder=os.path.join(root_dir, 'static'))
app.secret_key = secrets.token_hex(16)
app.register_blueprint(routes)

# Keep these warning level settings
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    logger.debug("Present Working Directory: %s", os.getcwd())
    if os.getenv('DEPLOY_ENV') == 'Railway':
        logger.info("Running in Railway environment")
        app.run(debug=True, host='0.0.0.0')
    else:
        logger.info("Running in local environment")
        app.run(debug=True, host='127.0.0.1')
