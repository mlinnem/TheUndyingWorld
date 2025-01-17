from flask import Flask, render_template, request, jsonify, session
import os
from .config import *
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from random import randint
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

    logger.info(f"response.usage: {response.usage}")

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
        summarizer_path = os.path.join(project_root, 'LLM_instructions', 'summarizer.MD')
        with open(summarizer_path, 'r') as file:
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
        # Use project root to find boot sequence file
        boot_sequence_path = os.path.join(project_root, 'LLM_instructions', 'boot_sequence.MD')
        with open(boot_sequence_path, 'r') as file:
            content = file.read()
            # Split by "# Instruction" and skip the first empty section
            sections = content.split("# Instruction")[1:]  # Skip first split which is empty
            # Clean each instruction and filter out empty ones
            boot_sequence_messages = [
                section.strip() 
                for section in sections 
                if section.strip()  # Skip empty messages
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