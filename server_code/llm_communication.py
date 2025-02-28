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

# In any file where you need temporary debug output
from .logger_config import set_console_level_for_module
# Later, when done debugging
set_console_level_for_module(__name__, logging.DEBUG)

# SET UP INITIAL PROMPTS

# Get the absolute path to the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tools_path = os.path.join(project_root, 'tools.json')

tools = []
with open(tools_path, 'r') as file:
    tools = json.load(file)


def get_next_gm_response(messages, system_prompt, temperature=0.7, permanent_cache_index=None, dynamic_cache_index=None):
    
    logger.debug(f"Sending message to GM (omitted for brevity)")

    # Add validation for cache indices
    if permanent_cache_index is not None and (permanent_cache_index < 0 or permanent_cache_index >= len(messages)):
        logger.warning(f"Invalid permanent_cache_index: {permanent_cache_index}")
        permanent_cache_index = None
    
    if dynamic_cache_index is not None and (dynamic_cache_index < 0 or dynamic_cache_index >= len(messages)):
        logger.warning(f"Invalid dynamic_cache_index: {dynamic_cache_index}")
        dynamic_cache_index = None

    # Clean messages for API consumption
    cleaned_messages = []
    for i, msg in enumerate(messages):
        cleaned_content = []
        for content in msg['content']:
            if content['type'] == "text":
                clean_content = {
                    "type": "text",
                    "text": content['text']
                }
                # Add cache control if this message is at a cache index
                if i == permanent_cache_index:
                    logger.debug("Adding permanent cache control at index: " + str(i))
                    clean_content['cache_control'] = {"type": "ephemeral"}
                elif i == dynamic_cache_index:
                    logger.debug("Adding dynamic cache control at index: " + str(i))
                    clean_content['cache_control'] = {"type": "ephemeral"}
                    
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
        model="claude-3-7-sonnet-20250219",
        messages=cleaned_messages,
        system=system_prompt,  
        max_tokens=MAX_OUTPUT_TOKENS,
        temperature=temperature,
        tools=tools,
    )

    logger.info(f"...received response from GM...")

    logger.debug(f"response.usage: {response.usage}")

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

    logger.debug(f"response.usage: {response.usage}")
        
    return response_json, usage_data

def summarize_with_gm_2(conversation):
    logger.debug(f"Starting summarization for conversation {conversation['conversation_id']}")
    
    permanent_cache_index = conversation.get('permanent_cache_index')
    
    if permanent_cache_index is None or permanent_cache_index == -1:
        logger.debug("No permanent cache point found, skipping summarization")
        return conversation

    logger.debug(f"Using permanent cache point at message index {permanent_cache_index}")

    # Calculate initial range to summarize
    start_index = permanent_cache_index + 1
    logger.debug(f"Initial start index is: {start_index}")
    logger.debug(f"The message there is as follows: {conversation['messages'][start_index]}")
    # Skip any tool_use or tool_result messages at the start
    while start_index < len(conversation['messages']):
        logger.debug(f"Let's check the first message at index {start_index} to see if it's a tool message")
        first_message = conversation['messages'][start_index]
        logger.debug(f"First message looks like this: {first_message}")
        found_a_tool = False
        for content_bit in first_message['content']:
            logger.debug(f"This message has a content bit that looks like this: {content_bit}")
            if content_bit['type'] == 'tool_use' or content_bit['type'] == 'tool_result':
                logger.debug(f"Found a tool message at index {start_index}")
                found_a_tool = True
                break
        if found_a_tool:
            logger.debug(f"Moving to the next message at index {start_index + 1}")
            start_index += 1
        else:
            logger.debug(f"No tool message found at index {start_index}, breaking out of the loop")
            break

    logger.debug(f"We've found the first non-tool message at index {start_index}, so that should be it going forward")
 

    end_index = min(start_index + SUMMARIZATION_BLOCK_SIZE, len(conversation['messages']) - 1)
    # Skip any tool_use or tool_result messages at the end
    while end_index < len(conversation['messages']):
        last_message = conversation['messages'][end_index]
        logger.debug(f"Last message: {last_message}")
        found_a_tool = False
        for content_bit in last_message['content']:
            logger.debug(f"Content bit: {content_bit}")
            if content_bit['type'] == 'tool_use' or content_bit['type'] == 'tool_result':
                found_a_tool = True
                break
        if found_a_tool:
            end_index += 1
        else:
            break
        logger.debug(f"Skipped tool message at end, new end_index: {end_index}")
    
    messages_to_summarize = conversation['messages'][start_index:end_index + 1]
    remaining_messages = conversation['messages'][end_index + 1:]

    logger.debug(f"Preparing to summarize messages from index {start_index} to {end_index}")
    logger.debug(f"Number of messages to summarize: {len(messages_to_summarize)}")
    logger.debug(f"Number of remaining messages: {len(remaining_messages)}")

    if len(messages_to_summarize) > 0:
        logger.debug("Loading summarizer instructions...")
        summarizer_instructions = conversation['summarizer_system_prompt']

        formatted_messages = "\n\n".join([
            f"{msg['role'].upper()}: {format_message_content(msg['content'])}"
            for msg in messages_to_summarize
        ])

        logger.debug("Preparing to call Claude for summarization...")

        # Extract just the text from the system prompt if it's in the wrong format
        if isinstance(summarizer_instructions, list):
            for item in summarizer_instructions:
                if isinstance(item, dict) and item.get('type') == 'text':
                    system_prompt = item.get('text', '')
                    break
        else:
            system_prompt = summarizer_instructions

        logger.debug(f"System prompt: {system_prompt}")

        try:
            logger.debug("Calling Claude API for summarization...")
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                messages=[{
                    "role": "user",
                    "content": [{
                        "type": "text", 
                        "text": f"Please provide a comprehensive summary of the following conversation:\n\n{formatted_messages}"
                    }]
                }],
                system=system_prompt,  # Now using the corrected system prompt
                max_tokens=MAX_OUTPUT_TOKENS,
                temperature=0.6,
            )

            logger.debug(f"Response: {response}")
            summary = response.content[0].text
            logger.debug("Successfully generated summary")
            logger.debug(f"Summary: {summary}")
            
            # Reconstruct conversation
            logger.debug("Reconstructing conversation with summary...")
            original_length = len(conversation['messages'])
            
            # Create summary message with cache control
            summary_message = {
                "role": "assistant",
                "content": [{
                    "type": "text",
                    "text": f"[SUMMARY OF PREVIOUS CONVERSATION]\n\n{summary}\n\n[END SUMMARY]",
                    "cache_control": {"type": "ephemeral"}
                }]
            }
            
            # Update conversation messages
            conversation['messages'] = (
                conversation['messages'][:start_index + 1] +
                [summary_message] +
                remaining_messages
            )
            
            # Update permanent cache index to be after the summary message
            conversation['permanent_cache_index'] = start_index + 1
            
            # Should also update dynamic cache if it would overlap
            if conversation.get('dynamic_cache_index') is not None:
                if conversation['dynamic_cache_index'] <= conversation['permanent_cache_index']:
                    conversation['dynamic_cache_index'] = None
            
            # Clear dynamic cache index as it needs to be recalculated
            conversation['dynamic_cache_index'] = None
            
            new_length = len(conversation['messages'])
            logger.debug(f"Conversation length changed from {original_length} to {new_length} messages")
            logger.debug(f"Successfully replaced {len(messages_to_summarize)} messages with summary")
            logger.debug(f"New permanent cache index set to {conversation['permanent_cache_index']}")
            
        except Exception as e:
            logger.error(f"Error during summarization process: {str(e)}", exc_info=True)
            return conversation

    else:
        logger.debug("No messages to summarize after permanent cache point")

    return conversation

def format_message_content(content):
    """Helper function to format message content based on its type."""
    if not isinstance(content, list):
        return str(content)
    
    formatted_parts = []
    for item in content:
        if item['type'] == 'text':
            formatted_parts.append(item['text'])
        elif item['type'] == 'tool_use':
            formatted_parts.append(f"[Tool Request: {item['name']} - {item['input']}]")
        elif item['type'] == 'tool_result':
            formatted_parts.append(f"[Tool Result: {item['content']}]")
        else:
            formatted_parts.append(f"[Unknown content type: {item['type']}]")
    
    return " ".join(formatted_parts)

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
                    logger.debug(f"Processing content item: {content_item}")
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