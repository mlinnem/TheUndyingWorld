import os
from .config import *
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from .tool_utils import *
import json
from typing import List, Dict
from .route_utils import * 

import logging
logger = logging.getLogger(__name__)

load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')

client = Anthropic(
    api_key=api_key
)

# Update the logger configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Keep your app's logger at INFO
handler = logging.StreamHandler()
logger.addHandler(handler)

# Set HTTP-related loggers to WARNING to suppress detailed dumps
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

# SET UP INITIAL PROMPTS

# Get the absolute path to the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tools_path = os.path.join(project_root, 'tools.json')

tools = []
with open(tools_path, 'r') as file:
    tools = json.load(file)


def get_next_gm_response(messages, system_prompt, temperature=0.7):
    logger.info(f"Sending message to GM (omitted for brevity)")

    # Clean messages for API consumption
    cleaned_messages = []
    for msg in messages:
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
        system=system_prompt,  
        max_tokens=MAX_OUTPUT_TOKENS,
        temperature=temperature,
        tools=tools,
    )

    logger.info(f"response.usage: {response.usage}")

    usage_data = {
        "uncached_input_tokens": response.usage.input_tokens,
        "cached_input_tokens": response.usage.cache_read_input_tokens + response.usage.cache_creation_input_tokens,
        "total_input_tokens": response.usage.input_tokens + response.usage.cache_read_input_tokens + response.usage.cache_creation_input_tokens,
    }

    # Initialize response_json with basic structure
    response_json = {
        "role": "assistant",
        "content": []
    }

    # Process each content block from the response
    for content_block in response.content:
        if hasattr(content_block, 'type'):
            if content_block.type == "text":
                response_json["content"].append({
                    "type": "text",
                    "text": content_block.text
                })
            elif content_block.type == "tool_use":
                response_json["content"].append({
                    "type": "tool_use",
                    "id": content_block.id,
                    "name": content_block.name,
                    "input": content_block.input
                })

    logger.info(f"response.usage: {response.usage}")
        
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
        summarizer_instructions = conversation['summarizer']

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
            
            logger.info("Saved updated conversation with summary")
            
        except Exception as e:
            logger.error(f"Error during summarization process: {str(e)}", exc_info=True)
            return conversation

    else:
        logger.info("No messages to summarize after permanent cache point")

    return conversation

def log_conversation_messages(messages):
    """Log conversation messages to a file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_dir = "persistent/conversation_logs"
    
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