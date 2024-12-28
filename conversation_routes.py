from flask import Blueprint, request, jsonify
from conversation_utils import *
from datetime import datetime
from convert_utils import *

conversation_routes = Blueprint('conversation_routes', __name__)

@conversation_routes.route('/new_conversation', methods=['POST'])
def new_conversation():
    conversation_id = generate_conversation_id()
    new_conversation = {
        'conversation_id': conversation_id,
        'name': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'messages': [],
        'last_updated': datetime.now().isoformat()
    }
    save_conversation(new_conversation)  # Initialize with 0 tokens
    return jsonify({'status': 'success', 'conversation_id': conversation_id})

@conversation_routes.route('/load_conversation', methods=['POST'])
def load_conversation_route():
    data = request.get_json()
    conversation_id = data['conversation_id']
    conversation  = load_conversation(conversation_id)


    if conversation:
        conversation_objects = convert_messages_to_cos(conversation['messages'])
        logger.debug(f"conversation_objects: {conversation_objects}")
        jsonified_result = jsonify({
            'success_type': 'full_success',
            'conversation_id': conversation_id,
            'conversation_name': conversation['name'],
            'new_conversation_objects': conversation_objects,
            'parsing_errors': []
        })
        return jsonified_result
    else:
        return jsonify({'status': 'error', 'message': 'Conversation not found'}), 404

@conversation_routes.route('/delete_conversation', methods=['POST'])
def delete_conversation_route():
    data = request.get_json()
    conversation_id = data['conversation_id']
    if delete_conversation(conversation_id):
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Conversation not found'}), 404

@conversation_routes.route('/list_conversations', methods=['GET'])
def list_conversations_route():
    conversations = list_conversations()
    return jsonify({'conversations': conversations})

@conversation_routes.route('/rename_conversation', methods=['POST'])
def rename_conversation():
    data = request.get_json()
    conversation_id = data['conversation_id']
    new_name = data['new_name']
    conversation = load_conversation(conversation_id)  # Unpack the tuple, ignoring token counts
    if conversation:
        conversation['name'] = new_name
        save_conversation(conversation)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Conversation not found'}), 404