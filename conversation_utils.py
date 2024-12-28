import os
import json
from datetime import datetime
import logging
from config import *

logger = logging.getLogger(__name__)

CONVERSATIONS_DIR = "conversations"

if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)

def save_conversation(conversation):
    logger.info(f"Saving conversation {conversation['conversation_id']}")
    conversation_id = conversation['conversation_id']

    conversation['last_updated'] = datetime.now().isoformat()
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    with open(file_path, 'w') as f:
        json.dump(conversation, f, indent=2)

def load_conversation(conversation_id):
    logger.info(f"Loading conversation {conversation_id}")

    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            conversation_data = json.load(f)
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
    return sorted(conversations, key=lambda x: x['last_updated'], reverse=True)

def generate_conversation_id():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def create_new_conversation():
    logger.info("Creating new conversation")

    conversation = {
        'conversation_id': generate_conversation_id(),
        'name': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'messages': [],
        'last_updated': datetime.now().isoformat(),
        'cache_points': []
    }
    return conversation

def update_conversation_cache_points(conversation):
    # remove all existing cache points

    for i, message in enumerate(conversation['messages']):
        # Skip first 20 messages
        if i < 20:
            continue
                
        content_block_to_clean = message['content'][0]
        print(f"content_block_to_clean (before): {content_block_to_clean}")

        if content_block_to_clean['type'] == "text":
            content_block_to_clean = {
                "type": "text",
                "text": content_block_to_clean['text']
                #no cache control
            }
        elif content_block_to_clean['type'] == "tool_use":
            content_block_to_clean = {
                "type": "tool_use",
                "id": content_block_to_clean['id'],
                "name": content_block_to_clean['name'],
                "input": content_block_to_clean['input']
                #no cache control
            }
        elif content_block_to_clean['type'] == "tool_result":
            content_block_to_clean = {
                "type": "tool_result",
                "tool_use_id": content_block_to_clean['tool_use_id'],
                "content": content_block_to_clean['content']
                #no cache control
            }
        else:
            raise Exception(f"Unknown message type: {content_block_to_clean['type']}")
        
        conversation['messages'][i]['content'][0] = content_block_to_clean
        print(f"content_block_to_clean (after): {content_block_to_clean}")


    conversation_id = conversation['conversation_id']
    print("Triggered cache point adding and removing")

    # add new cache point
    cache_point_to_be = len(conversation['messages']) - 1

    content_block_to_add_cache_point = conversation['messages'][cache_point_to_be]['content'][0]
    print(f"content_block_to_add_cache_point (before): {content_block_to_add_cache_point}")

    if content_block_to_add_cache_point['type'] == "text":
        content_block_to_add_cache_point = {
            "type": "text",
            "text": content_block_to_add_cache_point['text'],
            "cache_control": {"type": "ephemeral"}
                }
    elif content_block_to_add_cache_point['type'] == "tool_use":
        content_block_to_add_cache_point = {
            "type": "tool_use",
            "id": content_block_to_add_cache_point['id'],
            "name": content_block_to_add_cache_point['name'],
            "input": content_block_to_add_cache_point['input'],
            "cache_control": {"type": "ephemeral"}
        }
    elif content_block_to_add_cache_point['type'] == "tool_result":
        content_block_to_add_cache_point = {
            "type": "tool_result",
            "tool_use_id": content_block_to_add_cache_point['tool_use_id'],
            "content": content_block_to_add_cache_point['content'],
            "cache_control": {"type": "ephemeral"}
        }
    else:
        raise Exception(f"Unknown message type: {content_block_to_add_cache_point['type']}")
        
    conversation['messages'][cache_point_to_be]['content'][0] = content_block_to_add_cache_point
    print(f"content_block_to_add_cache_point (after): {content_block_to_add_cache_point}")

    return conversation