from flask import Blueprint, request, jsonify
from conversation_utils import save_conversation, load_conversation, delete_conversation, list_conversations, generate_conversation_id
from datetime import datetime

conversation_routes = Blueprint('conversation_routes', __name__)

@conversation_routes.route('/new_conversation', methods=['POST'])
def new_conversation():
    conversation_id = generate_conversation_id()
    new_conversation = {
        'id': conversation_id,
        'name': 'New Conversation',
        'messages': [],
        'last_updated': datetime.now().isoformat()
    }
    save_conversation(conversation_id, new_conversation, 0, 0)  # Initialize with 0 tokens
    return jsonify({'status': 'success', 'conversation_id': conversation_id})

@conversation_routes.route('/load_conversation', methods=['POST'])
def load_conversation_route():
    data = request.get_json()
    conversation_id = data['conversation_id']
    conversation, input_tokens, output_tokens = load_conversation(conversation_id)
    if conversation:
        return jsonify({
            'status': 'success', 
            'conversation': conversation,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens
        })
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
    conversation, input_tokens, output_tokens = load_conversation(conversation_id)
    if conversation:
        conversation['name'] = new_name
        save_conversation(conversation_id, conversation, input_tokens, output_tokens)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Conversation not found'}), 404