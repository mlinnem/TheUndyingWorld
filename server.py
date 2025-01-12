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
from typing import List, Dict

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
logger.setLevel(logging.INFO)  # Keep your app's logger at INFO
handler = logging.StreamHandler()
formatter = ColoredFormatter('%(message)s')  # You can adjust the format as needed
handler.setFormatter(formatter)
logger.addHandler(handler)

# Set HTTP-related loggers to WARNING to suppress detailed dumps
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

# SET UP INITIAL PROMPTS


tools = []
with open('tools.json', 'r') as file:
    tools = json.load(file)

manual_instructions =  ""
with open('LLM_instructions/game_manual.MD', 'r') as file:
    manual_instructions = file.read()


zombie_system_prompt = [{
        "type": "text",
        "text": manual_instructions,
        "cache_control": {"type": "ephemeral"}
}]

def send_message_to_gm(conversation, temperature=0.7):
    logger.info(f"Sending message to GM (omitted for brevity)")

    # Clean messages for API consumption
    cleaned_messages = []
    for msg in conversation['messages']:
        cleaned_content = []
        for content in msg['content']:
            if content['type'] == "text":
                clean_content = {
                    "type": "text",
                    "text": content['text']
                }
                # Only add cache_control if it exists
                if 'cache_control' in content:
                    clean_content['cache_control'] = content['cache_control']
                    
            elif content['type'] == "tool_use":
                clean_content = {
                    "type": "tool_use",
                    "id": content['id'],
                    "name": content['name'],
                    "input": content['input']
                }
                
            elif content['type'] == "tool_result":
                clean_content = {
                    "type": "tool_result",
                    "tool_use_id": content['tool_use_id'],
                    "content": content['content']
                }
            else:
                logger.warning(f"Unknown content type: {content['type']}")
                continue
                
            cleaned_content.append(clean_content)
            
        cleaned_messages.append({
            "role": msg['role'],
            "content": cleaned_content
        })

    # Log the first few cleaned messages for verification
    logger.debug(f"First cleaned message: {cleaned_messages[0] if cleaned_messages else 'No messages'}")

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        messages=cleaned_messages,
        system=conversation['system_prompt'],  
        max_tokens=MAX_OUTPUT_TOKENS,
        temperature=temperature,
        tools=tools,
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
    logger.info(f"Starting summarization for conversation {conversation['conversation_id']}")
    
    # Find the last permanent cache point
    permanent_cache_index = -1
    for i, msg in enumerate(conversation['messages']):
        if (isinstance(msg['content'][0], dict) and 
            msg['content'][0].get('cache_control', {}).get('type') == 'ephemeral'):
            permanent_cache_index = i
    
    if permanent_cache_index == -1:
        logger.info("No permanent cache point found, skipping summarization")
        return conversation

    logger.info(f"Found permanent cache point at message index {permanent_cache_index}")

    # Calculate the range to summarize
    start_index = permanent_cache_index + 1
    end_index = min(start_index + SUMMARIZATION_BLOCK_SIZE, len(conversation['messages']))
    
    messages_to_summarize = conversation['messages'][start_index:end_index]
    remaining_messages = conversation['messages'][end_index:]

    logger.info(f"Preparing to summarize messages from index {start_index} to {end_index}")
    logger.info(f"Number of messages to summarize: {len(messages_to_summarize)}")
    logger.info(f"Number of remaining messages: {len(remaining_messages)}")

    if len(messages_to_summarize) > 0:
        logger.info("Loading summarizer instructions...")
        with open('LLM_instructions/summarizer.MD', 'r') as file:
            summarizer_instructions = file.read()

        formatted_messages = "\n\n".join([
            f"{msg['role'].upper()}: {msg['content'][0]['text'] if isinstance(msg['content'], list) else msg['content']}"
            for msg in messages_to_summarize
        ])

        logger.info("Preparing to call Claude for summarization...")
        system_prompt = [{
            "type": "text",
            "text": summarizer_instructions
        }]

        try:
            logger.info("Calling Claude API for summarization...")
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                tools=tools,
                messages=[{
                    "role": "user",
                    "content": [{"type": "text", "text": f":{formatted_messages}"}]
                }],
                system=system_prompt,
                max_tokens=MAX_OUTPUT_TOKENS,
                temperature=0.6,
            )

            summary = response.content[0].text
            logger.info("Successfully generated summary")
            
            # Reconstruct conversation
            logger.info("Reconstructing conversation with summary...")
            original_length = len(conversation['messages'])
            conversation['messages'] = (
                conversation['messages'][:permanent_cache_index + 1] +
                [{
                    "role": "assistant",
                    "content": [{
                        "type": "text",
                        "text": f"[SUMMARY OF PREVIOUS CONVERSATION]\n\n{summary}\n\n[END SUMMARY]",
                        "cache_control": {"type": "ephemeral"}
                    }]
                }] +
                remaining_messages
            )
            new_length = len(conversation['messages'])
            
            logger.info(f"Conversation length changed from {original_length} to {new_length} messages")
            logger.info(f"Successfully replaced {len(messages_to_summarize)} messages with summary")
            
            save_conversation(conversation)
            logger.info("Saved updated conversation with summary")
            
        except Exception as e:
            logger.error(f"Error during summarization process: {str(e)}", exc_info=True)
            return conversation

    else:
        logger.info("No messages to summarize after permanent cache point")

    return conversation

def run_boot_sequence(conversation: Dict) -> Dict:
    """
    Runs a sequence of predetermined messages from boot_sequence_messages.MD to initialize a new game conversation.
    Returns the updated conversation with all boot sequence messages included.
    """
    try:
        # Read boot sequence messages from file
        with open('LLM_instructions/boot_sequence.MD', 'r') as file:
            boot_sequence_messages = [
                line.strip() for line in file.readlines() 
                if line.strip()  # Skip empty lines
            ]

        logger.info(f"Starting boot sequence with {len(boot_sequence_messages)} messages")
        
        for i, message in enumerate(boot_sequence_messages):
            logger.info(f"Processing boot sequence message {i+1}/{len(boot_sequence_messages)}")
            try:
                # Convert and add user message
                user_message = convert_user_text_to_message(message)
                conversation['messages'].append(user_message)
                
                # Get GM response
                gm_response, usage_data = send_message_to_gm(conversation, temperature=0.3)
                
                # Mark the last GM response of the boot sequence
                if i == len(boot_sequence_messages) - 1:
                    logger.info("Marking last GM response as boot sequence end")
                    gm_response['is_boot_sequence_end'] = True
                
                conversation['messages'].append(gm_response)
                
                # Handle tool use if requested
                if isToolUseRequest(gm_response):
                    logger.info("Tool use requested during boot sequence")
                    tool_result = generate_tool_result(gm_response)
                    conversation['messages'].append(tool_result)
                    
                    tool_response, _ = send_message_to_gm(conversation, temperature=0.3)
                    # If this is the last message, mark it instead of the previous response
                    if i == len(boot_sequence_messages) - 1:
                        logger.info("Moving boot sequence end marker to tool response")
                        gm_response.pop('is_boot_sequence_end', None)
                        tool_response['is_boot_sequence_end'] = True
                    conversation['messages'].append(tool_response)
                
                # Save after each message exchange
                save_conversation(conversation)
                
            except Exception as e:
                logger.error(f"Error in boot sequence at message '{message}': {e}")
                raise
        
        # Update cache points after boot sequence is complete
        logger.info("Boot sequence completed, updating cache points")
        conversation = update_conversation_cache_points(conversation)
        save_conversation(conversation)
        
        logger.info("Boot sequence and cache point setup completed successfully")
        return conversation
        
    except FileNotFoundError:
        logger.error("boot_sequence_messages.MD file not found")
        raise
    except Exception as e:
        logger.error(f"Error reading boot sequence messages: {e}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    new_messages = []
    
    try:
        data = request.get_json()
        
        # get current conversation
        if 'current_conversation_id' in session:
            conversation = load_conversation(session['current_conversation_id'])
        else:
            conversation = create_new_conversation(zombie_system_prompt)
            session['current_conversation_id'] = conversation['conversation_id']
            
        # Check if this request should trigger boot sequence
        if data.get('run_boot_sequence') == True:
            conversation = run_boot_sequence(conversation)
            return jsonify({
                'success_type': 'full_success',
                'conversation_id': session['current_conversation_id'],
                'conversation_name': conversation['name'],
                'new_conversation_objects': convert_messages_to_cos(conversation['messages']),
                'parsing_errors': [],
            })

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
            response['error_message'] = "Anthropic rate limit exceeded. Either you've sent too many requests in a short period of time, or you've exceeded your monthly request limit. Either wait a few minutes, or raise your monthly spending limit to proceed."
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