import os
import json
from datetime import datetime

CONVERSATIONS_DIR = "conversations"

if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)

def save_conversation(conversation_id, conversation, input_tokens, output_tokens):
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    conversation_data = {
        "conversation": conversation,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens
    }
    with open(file_path, 'w') as f:
        json.dump(conversation_data, f, indent=2)


def load_conversation(conversation_id):
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            conversation_data = json.load(f)
            return conversation_data["conversation"], conversation_data["input_tokens"], conversation_data["output_tokens"]
    return None, 0, 0

def delete_conversation(conversation_id):
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def list_conversations():
    conversations = []
    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.endswith(".json"):
            conversation_id = filename[:-5]  # Remove .json extension
            conversation_data, _, _ = load_conversation(conversation_id)
            if conversation_data:
                conversations.append({
                    'id': conversation_id,
                    'name': conversation_data['name'],
                    'last_updated': conversation_data['last_updated']
                })
    return sorted(conversations, key=lambda x: x['last_updated'], reverse=True)

def generate_conversation_id():
    return datetime.now().strftime("%Y%m%d%H%M%S")