import os
import json
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

CONVERSATIONS_DIR = "conversations"

if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)


def read_conversation(conversation_id):
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            conversation_data = json.load(f)
            return conversation_data
    return None

def write_conversation(conversation):
    logger.info(f"Saving conversation {conversation['conversation_id']}")
    conversation_id = conversation['conversation_id']
    conversation['last_updated'] = datetime.now().isoformat()
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    with open(file_path, 'w') as f:
        json.dump(conversation, f, indent=2)

def delete_conversation(conversation_id):
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def read_all_conversation_ids():
    conversation_ids = []
    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.endswith(".json"):
            conversation_id = filename[:-5]  # Remove .json extension
            conversation_ids.append(conversation_id)
    return conversation_ids
            
