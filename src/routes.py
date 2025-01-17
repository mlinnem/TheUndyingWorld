from flask import Blueprint, request, jsonify
from flask import Flask, render_template, request, jsonify, session
from .business_logic import *
from datetime import datetime
from .route_utils import *
import traceback

import logging
logger = logging.getLogger(__name__)

routes = Blueprint('routes', __name__)

@routes.route('/chat', methods=['POST'])
def chat_in_current_conversation_route():
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
        conversation = load_conversation(session['current_conversation_id'])
        
        # Check if this request should trigger boot sequence
        if data.get('run_boot_sequence') == True:
            conversation = run_boot_sequence(conversation)
            return jsonify({
                'success_type': 'full_success',
                'conversation_id': session['current_conversation_id'],
                'conversation_name': conversation['name'],
                'message_count': conversation['message_count'],
                'last_updated': conversation['last_updated'],
                'new_conversation_objects': convert_messages_to_cos(conversation['messages']),
                'parsing_errors': [],
            })

        # get and save user message
        raw_user_message = request.get_json()['user_message']

        return chat(raw_user_message, conversation)

@routes.route('/')
def index_route():
    return render_template('index.html')

@routes.route('/create_conversation', methods=['POST'])
def create_conversation_route():
    try:
        logger.info("Starting new conversation creation")
        
        # Create the conversation
        conversation = create_new_conversation()
        
        logger.info("Added intro message to conversation")
        # Set the current conversation ID in the session
        from flask import session  # Add this import at the top
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
        conversation = load_conversation(conversation_id)
        
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
    

