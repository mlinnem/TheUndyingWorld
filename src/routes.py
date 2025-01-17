from flask import Blueprint, request, jsonify
from flask import render_template, request, jsonify, session
from .business_logic import *
from .route_utils import *
import traceback

import logging
logger = logging.getLogger(__name__)

routes = Blueprint('routes', __name__)

@routes.route('/chat', methods=['POST'])
def chat_in_current_conversation_route():
    try:
        # Check for valid current_conversation_id first
        if 'current_conversation_id' not in session:
            return jsonify({
                'status': 'error',
                'success_type': 'error',
                'error_type': 'no_conversation',
                'error_message': 'No active conversation. Please start or select a conversation first.',
                'new_conversation_objects': [],
                'parsing_errors': [],
            }), 400
            
        data = request.get_json()
        should_run_boot_sequence = data.get('run_boot_sequence')
        raw_user_message = data.get('user_message')
        user_message_for_server = convert_user_text_to_message(raw_user_message)

        conversation = get_conversation(session['current_conversation_id'])
        conversation, new_messages = chat(user_message_for_server, conversation, should_run_boot_sequence)
        
        save_conversation(conversation)

        new_conversation_objects = convert_messages_to_cos(new_messages)

        return jsonify({
            'status': 'success',
            'success_type': 'full_success',
            'conversation_id': session['current_conversation_id'],
            'conversation_name': conversation['name'],
            'message_count': conversation['message_count'],
            'last_updated': conversation['last_updated'],
            'new_conversation_objects': new_conversation_objects,
            'parsing_errors': [],
        })
    
    except Exception as e:
        logger.error(f"Error in chat route: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'success_type': 'error',
            'error_type': 'internal_error',
            'error_message': 'An error occurred while processing your request. Please try again.',
            'new_conversation_objects': [],
            'parsing_errors': [],
        }), 500

@routes.route('/')
def index_route():
    return render_template('index.html')

@routes.route('/create_conversation', methods=['POST'])
def create_conversation_route():
    try:
        logger.info("Starting new conversation creation")
        
        # Create the conversation
        conversation = create_new_conversation()
        
        session['current_conversation_id'] = conversation['conversation_id']
        logger.info(f"Set current conversation ID in session: {conversation['conversation_id']}")
        
        conversation_objects = convert_messages_to_cos(conversation['messages'])
        logger.info(f"Converted messages to objects, count: {len(conversation_objects)}")
        logger.debug(f"Conversation objects: {conversation_objects}")
        
        response = {
            'status': 'success',
            'success_type': 'full_success',
            'conversation_id': conversation['conversation_id'],
            'conversation_name': conversation['name'],
            'message_count': conversation['message_count'],
            'last_updated': conversation['last_updated'],
            'new_conversation_objects': conversation_objects,
            'parsing_errors': []
        }
        logger.info("Preparing response")
        logger.debug(f"Full response: {response}")
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error creating new conversation: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@routes.route('/delete_conversation', methods=['POST'])
def delete_conversation_route():
    data = request.get_json()
    conversation_id = data['conversation_id']
    if delete_conversation(conversation_id):
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Conversation not found'}), 404

@routes.route('/list_conversations', methods=['GET'])
def list_conversations_route():
    conversations = list_conversations()
    return jsonify({'conversations': conversations})

@routes.route('/set_current_conversation', methods=['POST'])
def set_current_conversation_route():
    try:
        data = request.get_json()
        conversation_id = data['conversation_id']
        conversation = get_conversation(conversation_id)
        
        if conversation:
            # Add this line to set the current conversation in session
            session['current_conversation_id'] = conversation_id
            
            conversation_objects = convert_messages_to_cos(conversation['messages'])
            jsonified_result = jsonify({
                'status': 'success',
                'success_type': 'full_success',
                'conversation_id': conversation_id,
                'conversation_name': conversation['name'],
                'message_count': conversation['message_count'],
                'last_updated': conversation['last_updated'],
                'new_conversation_objects': conversation_objects,
                'parsing_errors': [],
            })
            return jsonified_result
        else:
            return jsonify({'status': 'error', 'message': 'Conversation not found'}), 404
    except Exception as e:
        logger.error(f"Error setting current conversation: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    

