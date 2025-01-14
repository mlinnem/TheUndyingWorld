from flask import Blueprint, request, jsonify
from conversation_utils import *
from datetime import datetime
from convert_utils import *
import traceback

conversation_routes = Blueprint('conversation_routes', __name__)

@conversation_routes.route('/new_conversation', methods=['POST'])
def new_conversation():
    try:
        from server import zombie_system_prompt, logger  # Import logger too
        
        logger.info("Starting new conversation creation")
        
        # Create the conversation
        conversation = create_new_conversation(zombie_system_prompt)
        logger.info(f"Created conversation with ID: {conversation['conversation_id']}")
        
        # Read and add the intro blurb with proper message format
        with open('LLM_instructions/intro_blurb.MD', 'r') as file:
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

@conversation_routes.route('/load_conversation', methods=['POST'])
def load_conversation_route():
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
                'new_conversation_objects': conversation_objects,
                'parsing_errors': []
            })
            return jsonified_result
        else:
            return jsonify({'status': 'error', 'message': 'Conversation not found'}), 404
    except Exception as e:
        logger.error(f"Error loading conversation: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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
        return jsonify({'status': 'success', 'success_type': 'full_success'})
    else:
        return jsonify({'status': 'error', 'message': 'Conversation not found'}), 404

@conversation_routes.route('/set_current_conversation', methods=['POST'])
def set_current_conversation():
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