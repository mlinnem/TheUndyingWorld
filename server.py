from flask import Flask, render_template, request, jsonify, session
import os
from conversation_routes import conversation_routes
from conversation_utils import *
from config import *
from utils import calculate_cost
from datetime import datetime
import anthropic
from anthropic import Anthropic
from dotenv import load_dotenv
from random import randint
from tool_utils import *
from convert_utils import *
import logging
from logging.handlers import RotatingFileHandler
import http.client as http_client
import json
import secrets
from logger_config import setup_logging
import traceback

load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')

client = Anthropic(
    api_key=api_key
)

app = Flask(__name__, template_folder='templates')
app.secret_key = secrets.token_hex(16)
app.register_blueprint(conversation_routes)

# Get a logger instance for this module
class ColorCodes:
    RED = '\033[91m'
    RESET = '\033[0m'

# Create a custom formatter class
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.ERROR:
            record.msg = f"{ColorCodes.RED}{record.msg}{ColorCodes.RESET}"
        return super().format(record)

# Update the logger configuration
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = ColoredFormatter('%(message)s')  # You can adjust the format as needed
handler.setFormatter(formatter)
logger.addHandler(handler)

# SET UP INITIAL PROMPTS

manual_instructions =  ""
with open('instructions.MD', 'r') as file:
    manual_instructions = file.read()

tools = []
with open('tools.json', 'r') as file:
    tools = json.load(file)

zombie_system_prompt = [{
        "type": "text",
        "text": manual_instructions,
        "cache_control": {"type": "ephemeral"}
}]

def send_message_to_gm(conversation, temperature=0.7, system_prompt=zombie_system_prompt):
    logger.info(f"Sending message to GM {conversation['messages']}")

    global zombie_system_prompt
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=conversation['messages'],
        system=system_prompt,  
        max_tokens=MAX_OUTPUT_TOKENS,
        temperature=temperature,
        tools = tools,
    )

    print(f"response.usage: {response.usage}")

    usage_data = {
        "uncached_input_tokens" : response.usage.input_tokens,
        "cached_input_tokens" : response.usage.cache_read_input_tokens + response.usage.cache_creation_input_tokens,
        "total_input_tokens" : response.usage.input_tokens + response.usage.cache_read_input_tokens + response.usage.cache_creation_input_tokens,
    }
    # Convert usage data to our own dictionary format

    if len(response.content) > 1 and hasattr(response.content[1], 'type') and response.content[1].type == "tool_use":
        response_json = {
            "role": "assistant",
            "content": [
                {"type": "text", "text": response.content[0].text},
                {"type": "tool_use", "id": response.content[1].id, "name": response.content[1].name, "input": response.content[1].input}
            ]
        }
    else: # Is normal response
        response_json = {
                "role": "assistant",
                "content": [{"type": "text", "text": response.content[0].text}]
        }

    print(f"response.usage: {response.usage}")
        
    return response_json, usage_data

def summarize_with_gm(conversation):
    logger.info(f"Summarizing conversation {conversation['conversation_id']}")
    # Initialize summary variable
    summary = None
        
    # Figure out which portion to summarize
    quarter_point = len(conversation['messages']) // 4
    messages_to_summarize = conversation['messages'][MAGIC_FIRST_MESSAGES_TO_PRESERVE_COUNT:quarter_point] # will return empty list if quarter_point is less than 20
    last_three_quarters_of_messages = conversation['messages'][quarter_point:]

    if len(messages_to_summarize) > 0:
        # Load summarizer instructions from file
        with open('summarizer_instructions.MD', 'r') as file:
            summarizer_instructions = file.read()
    
        # Prepare the messages for summarization

        formatted_messages = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content'][0]['text'] if isinstance(msg['content'], list) else msg['content']}"
            for msg in messages_to_summarize
        ])

        system_prompt = [{
            "type": "text",
            "text": summarizer_instructions
        }]
    
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                tools=tools,
                messages=[{
                    "role": "user",
                    "content": [{"type": "text", "text": f":{formatted_messages}"}]
                }],
                system=system_prompt,
                max_tokens=MAX_OUTPUT_TOKENS,
                temperature=0.35,
            )
        
            summary = response.content[0].text
        except Exception as e:
            print(f"Error generating summary: {e}")
            return None

        print(f"summary: {summary}")
            
        if summary:
            # Replace summarized messages with the summary
            conversation['messages'] = [{
                "role": "assistant",
                "content": [{
                    "type": "text",
                    "text": f"[SUMMARY OF PREVIOUS CONVERSATION]\n\n{summary}\n\n[END SUMMARY]"
                }]
            }] + last_three_quarters_of_messages
            save_conversation(conversation)
    else:
        print("No messages to summarize")
    
    return conversation  # Add return statement

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    new_messages = []
    
    try:
    # get current conversation
        if 'current_conversation_id' in session:
            conversation = load_conversation(session['current_conversation_id'])
        else:
            conversation = create_new_conversation()
            session['current_conversation_id'] = conversation['conversation_id']
    except Exception as e:
        logger.error(f"Error loading or creating conversation: {e}")
        return jsonify({
            'success_type': 'error',
            'error_type': 'internal_error',
            'error_message': "Internal error, please try again later.",
            'parsing_errors': [],
        })

    try:
        # get and save user message
        raw_user_message = request.get_json()['user_message']
        user_message_for_server = convert_user_text_to_message(raw_user_message)
        conversation['messages'].append(user_message_for_server)
        
        # get and save gm response
        gm_response_json, usage_data = send_message_to_gm(conversation, temperature=0.5)
        conversation['messages'].append(gm_response_json)
        new_messages = [gm_response_json]

        # if gm requested tool use
        if (isToolUseRequest(gm_response_json)):
            logger.info("tool use request detected")
            # generate and save tool result
            tool_result_json = generate_tool_result(gm_response_json)
            conversation['messages'].append(tool_result_json)
            new_messages.append(tool_result_json)

            # get and save gm response to tool result
            tool_use_response_json, usage_data = send_message_to_gm(conversation, 0.8)
            conversation['messages'].append(tool_use_response_json)
            new_messages.append(tool_use_response_json)
        else:
            logger.info("no tool use request detected")
        
        # update caching or perform summarization if necessary
        if usage_data['total_input_tokens'] >= MAX_TOTAL_INPUT_TOKENS:
            conversation = summarize_with_gm(conversation)
            update_conversation_cache_points(conversation)
        elif usage_data['uncached_input_tokens'] >= MAX_UNCACHED_INPUT_TOKENS:
            conversation = update_conversation_cache_points(conversation)


        conversation_objects = convert_messages_to_cos(new_messages)
        logger.debug(f"conversation_objects: {conversation_objects}")

        jsonified_result = jsonify({
            'success_type': 'full_success',
            'conversation_id': session['current_conversation_id'],
            'conversation_name': conversation['name'],
            'new_conversation_objects': conversation_objects,
            'parsing_errors': [],
        })
        return jsonified_result

    except anthropic.AnthropicError as e:

        conversation_objects = convert_messages_to_cos(new_messages)
        response = {
            'success_type': 'partial_success',
            'conversation_id': session['current_conversation_id'],
            'conversation_name': conversation['name'],
            'new_conversation_objects': conversation_objects,
            'parsing_errors': [],
        }
        if isinstance(e, anthropic.BadRequestError):
            logger.error(f"Bad request error: {e}")
            response['error_type'] = 'internal_error'
            response['error_message'] = "Internal error, please try again later."
        elif isinstance(e, anthropic.AuthenticationError):
            logger.error(f"Authentication error: {e}")
            response['error_type'] = 'authentication_error'
            response['error_message'] = "Authentication error, please check your API key and try again."
        elif isinstance(e, anthropic.PermissionDeniedError):
            logger.error(f"Permission denied error: {e}")
            response['error_type'] = 'permission_denied_error'
            response['error_message'] = "Permission denied, please check your API key and try again."
        elif isinstance(e, anthropic.NotFoundError):
            logger.error(f"Not found error: {e}")
            response['error_type'] = 'internal_error'
            response['error_message'] = "Internal error, please try again later."
        elif isinstance(e, anthropic.UnprocessableEntityError):
            logger.error(f"Unprocessable entity error: {e}")
            response['error_type'] = 'internal_error'
            response['error_message'] = "Internal error, please try again later."
        elif isinstance(e, anthropic.RateLimitError):
            logger.error(f"Rate limit error: {e}")
            response['error_type'] = 'rate_limit_error'
            response['error_message'] = "Anthropic rate limit exceeded, please try again in at least one minute."
        elif isinstance(e, anthropic.APIConnectionError):
            logger.error(f"API connection error: {e}")
            response['error_type'] = 'internal_error'
            response['error_message'] = "Internal error, please try again later."
        else:
            logger.error(f"Unknown error: {e}")
            response['error_type'] = 'internal_error'
            response['error_message'] = "Internal error, please try again later."

        return jsonify(response)

    except Exception as e:
        logger.error(f"Non-Anthropic error: {e}")
        logger.error(f"Stack at time of error: {''.join(traceback.format_tb(e.__traceback__))}")
        conversation_objects = convert_messages_to_cos(new_messages)
        jsonified_result = jsonify({
            'success_type': 'partial_success',
            'error_type': 'unknown_error',
            'error_message': str(e),
            'conversation_id': session['current_conversation_id'],
            'conversation_name': conversation['name'],
            'conversation_objects': conversation_objects,
            'parsing_errors': [],
        })
        return jsonified_result
    finally:
        save_conversation(conversation)

@app.route('/set_current_conversation', methods=['POST'])
def set_current_conversation():
    data = request.get_json()
    conversation_id = data['conversation_id']
    conversation = load_conversation(conversation_id)
    if conversation:
        session['current_conversation_id'] = conversation_id

        conversation_objects = convert_messages_to_cos(conversation['messages'])
        jsonified_result = jsonify({
            'status' : 'success',
            'success_type': 'full_success',
            'conversation_id': session['current_conversation_id'],
            'conversation_name': conversation['name'],
            'new_conversation_objects': conversation_objects,
            'parsing_errors': [],
        })
        return jsonified_result
    else:
        return jsonify({'status': 'error', 'message': 'Conversation not found'}), 404

@app.route('/system_prompt', methods=['GET', 'POST'])
def system_prompt():
    if request.method == 'POST':
        data = request.get_json()
        app.config['current_system_prompt'] = data['system_prompt']
        logger.info(f"System prompt updated to: {app.config['current_system_prompt']}")  # Debug print
        return jsonify({'status': 'system prompt updated'})
    else:
        return jsonify({'system_prompt': app.config['current_system_prompt']})

def log_conversation_messages(messages):
    """Log conversation messages to a file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_dir = "conversation_logs"
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, "conversation_logs.txt")
    
    with open(log_file, "a", encoding='utf-8') as f:
        f.write(f"\n\n=== Conversation Log {timestamp} ===\n")
        for msg in messages:
            role = msg['role']
            
            # Handle different message content types
            if isinstance(msg['content'], list):
                # Process each content item
                for content_item in msg['content']:
                    if content_item['type'] == 'text':
                        f.write(f"\n{role.upper()}: {content_item['text']}\n")
                    elif content_item['type'] == 'tool_use':
                        f.write(f"\n{role.upper()} TOOL REQUEST: {content_item['name']}\n")
                    elif content_item['type'] == 'tool_result':
                        f.write(f"\n{role.upper()} TOOL RESULT: {content_item['content']}\n")
            else:
                # Handle legacy format
                f.write(f"\n{role.upper()}: {msg['content']}\n")
                
        f.write("\n" + "="*50)

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(debug=True)