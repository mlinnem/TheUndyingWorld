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
    logger.info("Received request for main menu")
    main_menu_rendered = render_template('main_menu.html')
    logger.info("...Main menu returned")
    return main_menu_rendered;

@routes.route('/new_game')
def new_game_route():
    logger.info("Received request for new game screen...")
    new_game_screen_rendered = render_template('new_game_screen.html')
    logger.info("...New game screen returned")
    return new_game_screen_rendered;

@routes.route('/load_game')
def load_game_route():
    logger.info("Received request for load game screen...")
    load_game_screen_rendered = render_template('load_game_screen.html')
    logger.info("...Load game screen returned")
    return load_game_screen_rendered;

@routes.route('/game/<conversation_id>')
def game_route(conversation_id):
    logger.info(f"Received request for game with conversation_id: {conversation_id}")

    conversation = get_conversation(conversation_id)
    if not conversation:
        logger.warning(f"Conversation not found: {conversation_id}. Redirecting to main menu.")
        return redirect(url_for('routes.index_route'))
    
    # Set the conversation in session
    session['current_conversation_id'] = conversation_id
    
    # Render the game template with the conversation ID
    game_screen_rendered = render_template('game.html', conversation_id=conversation_id)
    logger.info(f"...Game screen for conversation_id: {conversation_id} returned")
    return game_screen_rendered;


# Game seed routes

@routes.route('/get_game_world_listings', methods=['GET'])
def get_seed_listings_route():
    logger.info("Received request for game seed listings data...")
    game_seed_listings = get_game_seed_listings()    
    logger.info("...Game seed listings returned")
    return jsonify({'game_seed_listings': game_seed_listings})

# @routes.route('/start_game', methods=['POST'])
# def start_game_route():


# Conversation routes

@routes.route('/advance_conversation', methods=['POST'])
def advance_conversation_route():
    try:
        logger.info("Received request to advance conversation...")
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        
        # Check for valid conversation_id
        if not conversation_id:
            logger.error("...No conversation ID provided. Returning error.")
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
            logger.error(f"...Conversation for id: {conversation_id} not found. Returning error.")
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
        logger.info(f"...Conversation with id {conversation_id} advanced and saved...")

        new_conversation_objects = convert_messages_to_cos(new_messages)
        new_conversation_objects = filter_conversation_objects(new_conversation_objects)

        logger.info("...Returning new info on advanced conversation")
        return jsonify({
            'status': 'success',
            'success_type': 'full_success',
            'conversation_id': conversation_id,
            'conversation_name': conversation['name'],
            'message_count': conversation['message_count'],
            'last_updated': conversation['last_updated'],
            'new_conversation_objects': new_conversation_objects,
            'game_has_begun': conversation['game_has_begun'],
            'parsing_errors': [],
        })
    
    except Exception as e:
        logger.error(f"Error in chat route: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        logger.info("...Returning error")
        return jsonify({
            'status': 'error',
            'success_type': 'error',
            'error_type': 'internal_error',
            'error_message': 'An error occurred while processing your request. Please try again.',
            'new_conversation_objects': [],
            'parsing_errors': [],
        }), 500

@routes.route('/create_conversation_from_seed', methods=['POST'])
def create_conversation_from_seed_route():
    try:
        data = request.get_json()
        seed_id = data.get('seed_id')
        logger.info(f"Received request to create new conversation from seed id: {seed_id}")
        
        if not seed_id:
            logger.error("...No seed ID provided. Returning error.")
            return jsonify({
                'status': 'error',
                'message': 'No seed ID provided'
            }), 400

        conversation = create_conversation_from_seed(seed_id)

        # Save the seeded conversation
        save_conversation(conversation)
        logger.info(f"...Conversation with id {conversation['conversation_id']} created from seed and saved...")
        logger.info(f"...Returning instruction to redirect to new conversation (based on our seed) with id: {conversation['conversation_id']}")
        return jsonify({
            'status': 'success',
            'redirect_url': f'/game/{conversation["conversation_id"]}',
            'conversation_id': conversation['conversation_id']
        })

    except Exception as e:
        logger.error(f"Error creating conversation from seed: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        logger.info("...Returning error")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
        
        
@routes.route('/create_conversation', methods=['POST'])
def create_conversation_route():
    try:
        logger.info("Received new conversation creation request...")
        
        # Create the conversation
        conversation = create_new_conversation_from_scratch()
        conversation_id = conversation['conversation_id']
        logger.info(f"...New conversation with id: {conversation_id} created...")
        # Instead of returning JSON, return a redirect URL
        logger.info(f"...Returning redirect URL to new conversation with id: {conversation_id}")
        return jsonify({
            'status': 'success',
            'redirect_url': f'/game/{conversation_id}',
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        logger.error(f"Error creating new conversation: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        logger.info("...Returning error")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@routes.route('/delete_conversation', methods=['POST'])
def delete_conversation_route():
    data = request.get_json()
    conversation_id = data['conversation_id']
    logger.info(f"Received request to delete conversation with id: {conversation_id}")
    if delete_conversation(conversation_id):
        logger.info(f"...Conversation with id: {conversation_id} deleted successfully...")
        logger.info(f"...Returning success")
        return jsonify({'status': 'success'})
    else:
        logger.error(f"...Conversation with id: {conversation_id} not found...")
        logger.info(f"...Returning error")
        return jsonify({'status': 'error', 'message': 'Conversation not found'}), 404

@routes.route('/get_conversation_listings', methods=['GET'])
def get_conversation_listings_route():
    logger.info("Received request for conversation listings...")
    conversation_listings = get_conversation_listings()
    logger.info("...Conversation listings returned")
    return jsonify({'conversation_listings': conversation_listings})

@routes.route('/get_conversation', methods=['POST'])
def get_conversation_route():
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        
        # Check if conversation_id was provided
        if not conversation_id:
            logger.error("...No conversation ID provided. Returning error.")
            return jsonify({
                'status': 'error',
                'message': 'No conversation ID provided'
            }), 400
            
        logger.info(f"Received request for conversation with id: {conversation_id}...")
        conversation = get_conversation(conversation_id)
        
        if conversation:
            conversation_objects = convert_messages_to_cos(conversation['messages'])
            filtered_conversation_objects = filter_conversation_objects(conversation_objects)
            logger.info(f"...Returning conversation with id: {conversation_id}")
            jsonified_result = jsonify({
                'status': 'success',
                'success_type': 'full_success',
                'conversation_id': conversation_id,
                'conversation_name': conversation['name'],
                'message_count': conversation['message_count'],
                'last_updated': conversation['last_updated'],
                'intro_blurb': conversation['intro_blurb'],
                'new_conversation_objects': filtered_conversation_objects,
                'game_has_begun': conversation['game_has_begun'],
                'created_at': conversation['created_at'],
                'location': conversation['location'],
                'parsing_errors': [],
            })
            return jsonified_result
        else:
            logger.error(f"...Conversation with id: {conversation_id} not found. Returning error.")
            return jsonify({'status': 'error', 'message': 'Conversation not found'}), 404
    except Exception as e:
        logger.error(f"Error setting current conversation: {e}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        logger.info("...Returning error")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    

