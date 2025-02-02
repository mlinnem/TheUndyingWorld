from flask import Blueprint, request, jsonify, redirect, url_for
from flask import render_template, request, jsonify, session
from .business_logic import *
from .route_utils import *
import traceback

import logging
logger = logging.getLogger(__name__)

routes = Blueprint('routes', __name__, url_prefix='')


@routes.route('/')
def index_route():
    return render_template('main_menu.html')

@routes.route('/new_game')
def new_game_route():
    return render_template('new_game_screen.html')

@routes.route('/load_game')
def load_game_route():
    return render_template('load_game_screen.html')

@routes.route('/game/<conversation_id>')
def game_route(conversation_id):
    logger.info(f"Accessing game route with conversation_id: {conversation_id}")
    # Verify the conversation exists
    conversation = get_conversation(conversation_id)
    if not conversation:
        logger.warning(f"Conversation not found: {conversation_id}")
        # Redirect to index if conversation doesn't exist
        return redirect(url_for('routes.index_route'))
    
    # Set the conversation in session
    session['current_conversation_id'] = conversation_id
    
    # Render the game template with the conversation ID
    return render_template('game.html', conversation_id=conversation_id)


# Game seed routes

@routes.route('/get_game_world_listings', methods=['GET'])
def get_get_seed_listings_route():
    game_seed_listings = get_game_seed_listings()
    return jsonify({'game_seed_listings': game_seed_listings})

# @routes.route('/start_game', methods=['POST'])
# def start_game_route():


# Conversation routes

@routes.route('/advance_conversation', methods=['POST'])
def advance_conversation_route():
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        
        # Check for valid conversation_id
        if not conversation_id:
            return jsonify({
                'status': 'error',
                'success_type': 'error',
                'error_type': 'no_conversation',
                'error_message': 'No conversation ID provided.',
                'new_conversation_objects': [],
                'parsing_errors': [],
            }), 400
            
        should_run_boot_sequence = data.get('run_boot_sequence')
        raw_user_message = data.get('user_message')
        user_message_for_server = convert_user_text_to_message(raw_user_message)

        conversation = get_conversation(conversation_id)
        if not conversation:
            return jsonify({
                'status': 'error',
                'success_type': 'error',
                'error_type': 'invalid_conversation',
                'error_message': 'Conversation not found.',
                'new_conversation_objects': [],
                'parsing_errors': [],
            }), 404
            
        conversation, new_messages = advance_conversation(user_message_for_server, conversation, should_run_boot_sequence)
        
        save_conversation(conversation)

        new_conversation_objects = convert_messages_to_cos(new_messages)

        return jsonify({
            'status': 'success',
            'success_type': 'full_success',
            'conversation_id': conversation_id,
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

@routes.route('/create_conversation', methods=['POST'])
def create_conversation_route():
    try:
        logger.info("Starting new conversation creation")
        
        # Create the conversation
        conversation = create_new_conversation()
        conversation_id = conversation['conversation_id']
        
        # Instead of returning JSON, return a redirect URL
        return jsonify({
            'status': 'success',
            'redirect_url': f'/game/{conversation_id}',
            'conversation_id': conversation_id
        })
        
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

@routes.route('/get_conversation_listings', methods=['GET'])
def get_conversation_listings_route():
    conversation_listings = get_conversation_listings()
    return jsonify({'conversation_listings': conversation_listings})

@routes.route('/get_conversation', methods=['POST'])
def get_conversation_route():
    try:
        data = request.get_json()
        conversation_id = data['conversation_id']
        conversation = get_conversation(conversation_id)
        
        if conversation:
            conversation_objects = convert_messages_to_cos(conversation['messages'])
            jsonified_result = jsonify({
                'status': 'success',
                'success_type': 'full_success',
                'conversation_id': conversation_id,
                'conversation_name': conversation['name'],
                'message_count': conversation['message_count'],
                'last_updated': conversation['last_updated'],
                'new_conversation_objects': conversation_objects,
                'created_at': conversation['created_at'],
                'location': conversation['location'],
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
    

