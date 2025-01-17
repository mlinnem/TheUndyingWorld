import os
import json
from datetime import datetime
from .config import *
from flask import request, jsonify, session
from .route_utils import *
from .llm_communication import *

import logging
logger = logging.getLogger(__name__)




# Get the absolute path to the project root directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

manual_instructions = ""
manual_path = os.path.join(project_root, 'LLM_instructions', 'game_manual.MD')
with open(manual_path, 'r') as file:
    manual_instructions = file.read()

# Add intro path constant here
intro_path = os.path.join(project_root, 'LLM_instructions', 'intro_blurb.MD')

zombie_system_prompt = [{
        "type": "text",
        "text": manual_instructions,
        "cache_control": {"type": "ephemeral"}
}]


CONVERSATIONS_DIR = "conversations"

if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)

def save_conversation(conversation):
    logger.info(f"Saving conversation {conversation['conversation_id']}")
    conversation_id = conversation['conversation_id']

    conversation['last_updated'] = datetime.now().isoformat()
    conversation['message_count'] = len(conversation['messages'])
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    with open(file_path, 'w') as f:
        json.dump(conversation, f, indent=2)

def load_conversation(conversation_id):
    logger.info(f"Loading conversation {conversation_id}")

    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            conversation_data = json.load(f)
            if conversation_data.get('system_prompt'):
                # Check if prompt_version exists, if not add it
                if not conversation_data.get('prompt_version'):
                    logger.warning(f"Prompt version not found in conversation {conversation_id}. Adding timestamp.")
                    conversation_data['prompt_version'] = datetime.now().isoformat()
                else:
                    #print(f"Continuing with old system prompt for conversation {conversation_id}, {conversation_data['prompt_version']}")
                    pass
                return conversation_data
            else:
                #print(f"System prompt not found in conversation {conversation_id}. Using current system prompt.")
                conversation_data['system_prompt'] = zombie_system_prompt
                conversation_data['prompt_version'] = datetime.now().isoformat()
            return conversation_data
    return None

def delete_conversation(conversation_id):
    logger.info(f"Deleting conversation {conversation_id}")
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def list_conversations():
    logger.info("Listing conversations")

    conversations = []
    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.endswith(".json"):
            conversation_id = filename[:-5]  # Remove .json extension
            conversation_data = load_conversation(conversation_id)
            if conversation_data:
                conversations.append({
                    'conversation_id': conversation_id,
                    'name': conversation_data['name'],
                    'last_updated': conversation_data['last_updated']
                })
                # save_conversation(conversation_data)
    return sorted(conversations, key=lambda x: x['last_updated'], reverse=True)

def generate_conversation_id():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def create_new_conversation():
    logger.info("Creating new conversation")
    
    conversation_id = generate_conversation_id()
    conversation = {
        'conversation_id': conversation_id,
        'name': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'messages': [],
        'last_updated': datetime.now().isoformat(),
        'cache_points': [],
        'system_prompt': zombie_system_prompt,
        'prompt_version': datetime.now().isoformat()
    }

    logger.info(f"Created conversation with ID: {conversation['conversation_id']}")
    
    # Use the constant intro_path instead of defining it here
    with open(intro_path, 'r') as file:
        intro_blurb = file.read()
        logger.info(f"Read intro blurb, length: {len(intro_blurb)}")

    # Format the intro message properly
    intro_message = {
        'role': 'assistant',
        'content': [{
            'type': 'text',
            'text': intro_blurb
        }],
        'timestamp': datetime.utcnow().isoformat()
    }
    conversation['messages'].append(intro_message)
    logger.info("Added intro message to conversation")
        
    # Save the updated conversation
    save_conversation(conversation)
    logger.info("Saved conversation")

    logger.info(f"Conversation created:" + conversation_id)
    
    return conversation

def update_conversation_cache_points(conversation):
    logger.info(f"Updating cache points for conversation {conversation['conversation_id']}")
    
    # Add a metadata field to track cache point types
    def add_cache_control(content_block, cache_purpose):
        # Create a deep copy of the original block to preserve all fields
        modified_block = content_block.copy()
        
        # Add/update cache control and metadata while preserving existing data
        modified_block["cache_control"] = {"type": "ephemeral"}  # Required by API
        modified_block["cache_metadata"] = {
            "purpose": cache_purpose,  # 'permanent' or 'conversation'
            "timestamp": datetime.now().isoformat()
        }

        if content_block['type'] == "text":
            return modified_block
        elif content_block['type'] == "tool_use":
            return modified_block
        elif content_block['type'] == "tool_result":
            return modified_block
        else:
            raise Exception(f"Unknown message type: {content_block['type']}")

    # Helper function to remove cache control from a content block
    def remove_cache_control(content_block):
        if content_block['type'] == "text":
            return {"type": "text", "text": content_block['text']}
        elif content_block['type'] == "tool_use":
            return {
                "type": "tool_use",
                "id": content_block['id'],
                "name": content_block['name'],
                "input": content_block['input']
            }
        elif content_block['type'] == "tool_result":
            return {
                "type": "tool_result",
                "tool_use_id": content_block['tool_use_id'],
                "content": content_block['content']
            }
        else:
            raise Exception(f"Unknown message type: {content_block['type']}")

    # First, remove all cache points
    logger.info("Removing all existing cache points")
    for message in conversation['messages']:
        message['content'][0] = remove_cache_control(message['content'][0])

    # Determine the boot sequence length
    boot_sequence_length = next(
        (i for i, msg in enumerate(conversation['messages']) 
         if msg.get('is_boot_sequence_end', False)),
        0
    )
    logger.info(f"Boot sequence length detected: {boot_sequence_length}")

    total_messages = len(conversation['messages'])
    logger.info(f"Total messages in conversation: {total_messages}")
    
    # Handle permanent cache point
    if total_messages <= boot_sequence_length + 50:
        # Set permanent cache at end of boot sequence
        if boot_sequence_length > 0:
            logger.info(f"Setting permanent cache point at boot sequence end (message {boot_sequence_length - 1})")
            conversation['messages'][boot_sequence_length - 1]['content'][0] = \
                add_cache_control(conversation['messages'][boot_sequence_length - 1]['content'][0], "ephemeral")
    else:
        # Set permanent cache at message 50 after boot sequence
        permanent_cache_index = boot_sequence_length + 49
        logger.info(f"Setting permanent cache point at message 50 after boot (message {permanent_cache_index})")
        conversation['messages'][permanent_cache_index]['content'][0] = \
            add_cache_control(conversation['messages'][permanent_cache_index]['content'][0], "ephemeral")

    # Handle conversation cache point
    messages_after_initial = total_messages - (boot_sequence_length + 50)
    if messages_after_initial > 0:
        conversation_cache_index = total_messages - (messages_after_initial % 20) - 1
        if conversation_cache_index > boot_sequence_length + 49:
            logger.info(f"Setting conversation cache point at message {conversation_cache_index}")
            conversation['messages'][conversation_cache_index]['content'][0] = \
                add_cache_control(conversation['messages'][conversation_cache_index]['content'][0], "ephemeral")
    else:
        logger.info("No conversation cache point needed yet (fewer than 50 messages after boot)")

    return conversation


def chat(user_message, conversation, should_run_boot_sequence):
    new_messages = []

    if should_run_boot_sequence:
        conversation = run_boot_sequence(conversation)
                # Update cache points after boot sequence is complete
        logger.info("Boot sequence completed, updating cache points")
        conversation = update_conversation_cache_points(conversation)
        
        logger.info("Boot sequence and cache point setup completed successfully")
        return conversation, new_messages
    
    conversation['messages'].append(user_message)
        
    # get and save gm response
    gm_response_json, usage_data = get_next_gm_response(conversation, temperature=0.5)
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
        tool_use_response_json, usage_data = get_next_gm_response(conversation, 0.8)
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

    return conversation, new_messages


