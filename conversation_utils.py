import os
import json
from datetime import datetime
import logging
from config import *

logger = logging.getLogger(__name__)

manual_instructions =  ""
with open('LLM_instructions/game_manual.MD', 'r') as file:
    manual_instructions = file.read()


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
                    print(f"Prompt version not found in conversation {conversation_id}. Adding timestamp.")
                    conversation_data['prompt_version'] = datetime.now().isoformat()
                else:
                    print(f"Continuing with old system prompt for conversation {conversation_id}, {conversation_data['prompt_version']}")
                return conversation_data
            else:
                print(f"System prompt not found in conversation {conversation_id}. Using current system prompt.")
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
                save_conversation(conversation_data)
    return sorted(conversations, key=lambda x: x['last_updated'], reverse=True)

def generate_conversation_id():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def create_new_conversation(current_system_prompt):
    logger.info("Creating new conversation")

    conversation = {
        'conversation_id': generate_conversation_id(),
        'name': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'messages': [],
        'last_updated': datetime.now().isoformat(),
        'cache_points': [],
        'system_prompt': current_system_prompt,
        'prompt_version': datetime.now().isoformat()
    }
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