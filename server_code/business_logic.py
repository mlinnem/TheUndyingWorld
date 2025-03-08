import os

from datetime import datetime
from .config import *
from .persistence import *
from .route_utils import *
from .llm_communication import *
from .format_utils import *

import logging
logger = logging.getLogger(__name__)

from .logger_config import LogCategory, log_with_category, preview

# In modules where you want DEBUG output:
import logging

logger = logging.getLogger(__name__)
world_gen_logger = logging.getLogger('world_gen')


CONVERSATIONS_DIR = "persistent/conversations"

if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)


def get_game_seed_listings():
    game_seed_ids = read_all_game_seed_ids()
    game_seed_listings = []
    for game_seed_id in game_seed_ids:
        game_seed = read_game_seed(game_seed_id)
        game_seed_listing = {
            'id': game_seed_id,
            'name': game_seed['location'],
            'location': game_seed['location'],
            'description': game_seed['description'],
            'created_at': game_seed['created_at'],
            'last_updated': game_seed['last_updated'],
            'message_count': len(game_seed['messages'])
        }
        game_seed_listings.append(game_seed_listing)
    return game_seed_listings


def save_conversation(conversation):
    log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, f"Saving conversation {conversation['conversation_id']}")
    conversation['last_updated'] = datetime.now().isoformat()
    conversation['message_count'] = len(conversation['messages'])
    write_conversation(conversation)

def get_conversation(conversation_id):
    return read_conversation(conversation_id)

def get_conversation_listings():
    conversation_ids = read_all_conversation_ids()
    conversation_listings = []
    for conversation_id in conversation_ids:
        conversation = read_conversation(conversation_id)
        conversation_listing = {
            'conversation_id': conversation_id,
            'name': conversation['name'],
            'last_updated': conversation['last_updated'],
            'created_at': conversation['created_at'],
            'location': conversation['location'],
            'message_count': len(conversation['messages'])
        };
        conversation_listings.append(conversation_listing)
    return sorted(conversation_listings, key=lambda x: x['last_updated'], reverse=True)

def generate_conversation_id():
    return datetime.now().strftime("%Y%m%d%H%M%S")

def create_new_conversation_from_scratch():
    log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, "Creating new conversation from scratch")
    
    conversation_id = generate_conversation_id()
    conversation = {
        'conversation_id': conversation_id,
        'name': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'messages': [],
        'last_updated': datetime.now().isoformat(),
        'created_at': datetime.now().isoformat(),
        'cache_points': [],
        'game_has_begun': False,
        'gameplay_system_prompt': get_gameplay_system_prompt(),
        'gameplay_system_prompt_date' : datetime.now().isoformat(),
        'game_setup_system_prompt': get_game_setup_system_prompt(),
        'game_setup_system_prompt_date' : datetime.now().isoformat(),
        'summarizer_system_prompt': get_summarizer_system_prompt(),
        'summarizer_system_prompt_date' : datetime.now().isoformat(),
    }

    log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, f"Created conversation with ID: {conversation['conversation_id']}")
    
    # Save the updated conversation

    save_conversation(conversation)
    log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, "Saved conversation")

    log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, f"Conversation created:" + conversation_id)
    
    return conversation

def create_conversation_from_seed(seed_id):
    log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, "Creating new conversation based on seed: " + seed_id)

    seed = read_game_seed(seed_id)

    # Filter out user messages from seed, keeping only assistant messages

    log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, "Filtering out user messages from seed")
    log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, "Pre-filtering messages: " + str(len(seed['messages'])))

    # No user messages in initial conversation (if we haven't already filtered out elsewhere)

    seed['messages'] = [msg for msg in seed['messages'] if msg['role'] == 'assistant']
 
    log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, "Post-filtering messages: " + str(len(seed['messages'])))
    
    conversation_id = generate_conversation_id()
    # Create short date string for conversation name
    short_date = datetime.now().strftime("%b %d")

    conversation = {
        'conversation_id': conversation_id,
        'name': seed['location'] + " (" + short_date +")",
        'location': seed['location'],
        'messages': seed['messages'],
        'boot_sequence_end_index': seed.get('boot_sequence_end_index', None),
        'last_updated': datetime.now().isoformat(),
        'created_at': datetime.now().isoformat(),
        'cache_points': [],
        'intro_blurb': seed['intro_blurb'],
        'intro_blurb_date': seed['intro_blurb_date'],
        'game_has_begun': False,
        'gameplay_system_prompt': seed['gameplay_system_prompt'],
        'gameplay_system_prompt_date' : seed['gameplay_system_prompt_date'],
        'game_setup_system_prompt': seed['game_setup_system_prompt'],
        'game_setup_system_prompt_date' : seed['game_setup_system_prompt_date'],
        'summarizer_system_prompt': seed['summarizer_system_prompt'],
        'summarizer_system_prompt_date' : seed['summarizer_system_prompt_date'],
    }
    logger.debug("Conversation created with name: " + str(conversation['name']))

    logger.debug(f"Created conversation based on seed with new ID: {conversation['conversation_id']}")
    
    # Save the updated conversation

    logger.debug("Saved conversation")

    logger.debug(f"Conversation created:" + conversation_id)
    
    return conversation



def update_conversation_cache_points_2(conversation):
    log_with_category(LogCategory.CACHING, logging.DEBUG, f"Updating cache points for conversation {conversation['conversation_id']}")
    log_with_category(LogCategory.CACHING, logging.DEBUG, f"Current permanent_cache_index: {conversation.get('permanent_cache_index')}")
    log_with_category(LogCategory.CACHING, logging.DEBUG, f"Current dynamic_cache_index: {conversation.get('dynamic_cache_index')}")

    num_boot_sequence_messages = conversation.get('boot_sequence_end_index', -1) + 1
    num_messages = len(conversation['messages'])

    if num_messages > CACHE_EVERY_N_MESSAGES:
        dynamic_cache_index = num_messages - (num_messages % CACHE_EVERY_N_MESSAGES) - 1
        log_with_category(LogCategory.CACHING, logging.INFO, f"...Dynamic cache index set to {dynamic_cache_index}..." + "(out of " + str(num_messages) + " messages)")
    else:
        log_with_category(LogCategory.CACHING, logging.INFO, "Not enough messages for dynamic cache")
        dynamic_cache_index = None

    conversation['dynamic_cache_index'] = dynamic_cache_index

    # Initialize permanent_cache_index if it doesn't exist
    if conversation.get('permanent_cache_index') is None:
        if num_messages > num_boot_sequence_messages + MESSAGES_TO_PRESERVE_AFTER_BOOT_SEQUENCE:
            new_permanent_index = num_boot_sequence_messages + MESSAGES_TO_PRESERVE_AFTER_BOOT_SEQUENCE - 1
            log_with_category(LogCategory.CACHING, logging.DEBUG, f"Setting initial permanent cache index to {new_permanent_index}" + "(out of " + str(num_messages) + " messages)")
            conversation['permanent_cache_index'] = new_permanent_index
            log_with_category(LogCategory.CACHING, logging.INFO, f"...Permanent cache index set to {conversation['permanent_cache_index']}..." + "(out of " + str(num_messages) + " messages)")
        else:
            log_with_category(LogCategory.CACHING, logging.DEBUG, "Not enough messages after boot sequence for permanent cache")
            conversation['permanent_cache_index'] = None
    else:
        log_with_category(LogCategory.CACHING, logging.DEBUG, "Permanent cache index already set")

    log_with_category(LogCategory.CACHING, logging.DEBUG, f"Final cache indices - permanent: {conversation.get('permanent_cache_index')}, dynamic: {conversation.get('dynamic_cache_index')}")
    return conversation


def advance_conversation(user_message, conversation, should_create_generated_plot_info):
    new_messages = []

    if should_create_generated_plot_info:
        log_with_category([LogCategory.WORLD_GEN, LogCategory.ADVANCE_CONVERSATION_LOGIC], logging.INFO, "Initiating world generation sequence")
        logger.debug("...Request to run boot sequence identified...")
        # First create the generated plot info
        plot_messages = create_dynamic_world_gen_data_messages(conversation['messages'], conversation['game_setup_system_prompt'])
        conversation['messages'].extend(plot_messages)
        new_messages.extend(plot_messages)
        
        # Then execute the final startup instruction
        log_with_category([LogCategory.WORLD_GEN, LogCategory.ADVANCE_CONVERSATION_LOGIC], logging.DEBUG, "Executing final startup instruction")
        conversation, final_messages = execute_final_startup_instruction(conversation)
        new_messages.extend(final_messages)
        
        # Update cache points after boot sequence is complete
        log_with_category([LogCategory.WORLD_GEN, LogCategory.ADVANCE_CONVERSATION_LOGIC], logging.DEBUG, "Boot sequence completed, updating cache points")
        conversation = update_conversation_cache_points_2(conversation)
        
        log_with_category([LogCategory.WORLD_GEN, LogCategory.ADVANCE_CONVERSATION_LOGIC], logging.DEBUG, "Boot sequence and cache point setup completed successfully")
        log_with_category([LogCategory.WORLD_GEN, LogCategory.ADVANCE_CONVERSATION_LOGIC], logging.INFO, "World generation sequence completed successfully")
        return conversation, new_messages
        # Check if we need to inject the begin game message

      
   
    else:
        # Add debug logging for incoming user message
        log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, f"Received user message: {preview(user_message, 500)}")
        
        # Add timestamp to user message
        user_message['timestamp'] = datetime.now().isoformat()
        conversation['messages'].append(user_message)
        
        # Get and save gm response with timestamp
        gm_response_json, usage_data = get_next_gm_response(conversation['messages'], conversation['gameplay_system_prompt'], temperature=0.5, permanent_cache_index=conversation.get('permanent_cache_index', None), dynamic_cache_index=conversation.get('dynamic_cache_index', None))
        gm_response_json['timestamp'] = datetime.now().isoformat()
        conversation['messages'].append(gm_response_json)
        new_messages = [gm_response_json]

        if (isToolUseRequest(gm_response_json)):
            log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, "tool use request detected")
            # Generate and save tool result with timestamp
            tool_result_json = generate_tool_result(gm_response_json)
            tool_result_json['timestamp'] = datetime.now().isoformat()
            conversation['messages'].append(tool_result_json)
            new_messages.append(tool_result_json)

            # Get and save gm response to tool result with timestamp
            tool_use_response_json, usage_data = get_next_gm_response(conversation['messages'], conversation['gameplay_system_prompt'], temperature=0.8, permanent_cache_index=conversation.get('permanent_cache_index', None), dynamic_cache_index=conversation.get('dynamic_cache_index', None))
            tool_use_response_json['timestamp'] = datetime.now().isoformat()
            conversation['messages'].append(tool_use_response_json)
            new_messages.append(tool_use_response_json)
        else:
            log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, "no tool use request detected")


        # Get coaching feedback if we have enough messages since boot
        log_with_category(LogCategory.ADVANCE_CONVERSATION_LOGIC, logging.DEBUG, f"conversation['game_has_begun']: {conversation['game_has_begun']}")
        if conversation['game_has_begun']:
            log_with_category([LogCategory.COACHING, LogCategory.ADVANCE_CONVERSATION_LOGIC], logging.DEBUG, "Getting coaching feedback")
            # Get boot sequence end index
            boot_sequence_end_index = conversation.get('boot_sequence_end_index', -1)
            
            # Get all messages after boot sequence
            post_boot_messages = conversation['messages'][boot_sequence_end_index + 1:]
            
            # If we have at least one message since boot, get coaching feedback
            log_with_category([LogCategory.COACHING, LogCategory.ADVANCE_CONVERSATION_LOGIC], logging.DEBUG, f"len(post_boot_messages): {len(post_boot_messages)}")
            if len(post_boot_messages) > 0:
                log_with_category([LogCategory.COACHING, LogCategory.ADVANCE_CONVERSATION_LOGIC], logging.DEBUG, "post boot messages found")
                log_with_category([LogCategory.COACHING, LogCategory.ADVANCE_CONVERSATION_LOGIC], logging.DEBUG, f"Getting coaching feedback on {len(post_boot_messages)} messages since boot")
                messages_to_coach = post_boot_messages[-10:] if len(post_boot_messages) > 10 else post_boot_messages
                coaching_response, _ = get_coaching_message(
                    messages_to_coach, 
                    conversation['coaching_system_prompt'],
                    temperature=0.4 
                )
                conversation['messages'].append(coaching_response)
                log_with_category(LogCategory.COACHING, logging.INFO, f"Coaching feedback received: {coaching_response}")
        else:
            log_with_category(LogCategory.COACHING, logging.DEBUG, "game has not begun")
        


        # update caching or perform summarization if necessary
        if usage_data['total_input_tokens'] >= MAX_TOTAL_INPUT_TOKENS:
            log_with_category([LogCategory.SUMMARIZATION, LogCategory.ADVANCE_CONVERSATION_LOGIC], logging.INFO, "Identified need to summarize conversation with GM, because total input tokens are at " + str(usage_data['total_input_tokens']) + " (max is " + str(MAX_TOTAL_INPUT_TOKENS) + ")")
            log_with_category([LogCategory.SUMMARIZATION, LogCategory.ADVANCE_CONVERSATION_LOGIC], logging.DEBUG, "...Identified need to summarize conversation with GM...")
            conversation = summarize_with_gm_2(conversation)
            log_with_category([LogCategory.SUMMARIZATION, LogCategory.ADVANCE_CONVERSATION_LOGIC], logging.DEBUG, "...Summarization produced (not yet saved)...")
            update_conversation_cache_points_2(conversation)
        elif usage_data['uncached_input_tokens'] >= MAX_UNCACHED_INPUT_TOKENS:
            conversation = update_conversation_cache_points_2(conversation)

        conversation['game_has_begun'] = True
        conversation['game_has_begun_date'] = datetime.now().isoformat()

        return conversation, new_messages

def create_dynamic_world_gen_data_messages(existing_messages, game_setup_system_prompt):
    logger.debug("Creating dynamic world gen data messages")
    try:
        import random
        import re   

        # Get pre-parsed instruction sections
        world_gen_instructions_w_omit_data = get_world_gen_sequence_array()
        
        temp_conversation = {
            'messages': existing_messages.copy(),
            'game_setup_system_prompt': game_setup_system_prompt
        }

        log_with_category(LogCategory.WORLD_GEN, logging.INFO, f"Boot sequence contains {len(world_gen_instructions_w_omit_data)} instructions")
        
        final_messages = []
        
        for i, world_gen_instruction_w_omit_data in enumerate(world_gen_instructions_w_omit_data):
            try:
                log_with_category(LogCategory.WORLD_GEN, logging.INFO, f"Processing boot sequence instruction {i+1}/{len(world_gen_instructions_w_omit_data)}")
                # Convert and add user message with timestamp
                world_gen_instruction = convert_user_text_to_message(world_gen_instruction_w_omit_data['text'])
                world_gen_instruction['timestamp'] = datetime.now().isoformat()
                temp_conversation['messages'].append(world_gen_instruction)
                
                dynamic_cache_index = (len(temp_conversation['messages']) -1) - (len(temp_conversation['messages']) % 8)
                permanent_cache_index = (len(temp_conversation['messages']) -1) - (len(temp_conversation['messages']) % 24)
                
                gm_response, usage_data = get_next_gm_response(temp_conversation['messages'],temp_conversation['game_setup_system_prompt'], temperature=0.84, dynamic_cache_index=dynamic_cache_index, permanent_cache_index=permanent_cache_index)

                gm_response['timestamp'] = datetime.now().isoformat()
                temp_conversation['messages'].append(gm_response)

                
                # Mark the last GM response of the boot sequence
                if i == len(world_gen_instructions_w_omit_data) - 1 - 1: # -1 to reveal the final message to user, -1 to adjust for length vs index
                    logger.debug("Marking last GM response as boot sequence end")
                    gm_response['is_boot_sequence_end'] = True
                    # Add the last message to the final messages, as it will inform several messages to come
                    final_messages.append(world_gen_instruction)
                    


                if not world_gen_instruction_w_omit_data['omit_result']:
                    final_messages.append(gm_response)
                
                
                
                # Handle tool use if requested
                if isToolUseRequest(gm_response):
                    logger.debug("Tool use requested during boot sequence")  
                    tool_result = generate_tool_result(gm_response)
                    logger.debug(f"Tool result: {tool_result}")
                    tool_result['timestamp'] = datetime.now().isoformat()
                    temp_conversation['messages'].append(tool_result)
                    
                    tool_response, _ = get_next_gm_response(temp_conversation['messages'], game_setup_system_prompt, temperature=0.8)
                    tool_response['timestamp'] = datetime.now().isoformat()
                    temp_conversation['messages'].append(tool_response)     
                    
                    if i == len(world_gen_instructions_w_omit_data) - 1:
                        logger.debug("Moving boot sequence end marker to tool response")
                        gm_response.pop('is_boot_sequence_end', None)
                        tool_response['is_boot_sequence_end'] = True
                    
                    if not world_gen_instruction_w_omit_data['omit_result']:
                        final_messages.append(tool_result)
                        final_messages.append(tool_response)
                logger.info(f"...Completed boot sequence instruction {i+1}/{len(world_gen_instructions_w_omit_data)}...")

            except Exception as e:
                logger.error(f"Error in boot sequence at message '{world_gen_instruction_w_omit_data['text']}': {e}")
                raise

        # Find the index of the boot sequence end message
        boot_sequence_end_index = -1
        for i, message in enumerate(final_messages):
            if message.get('is_boot_sequence_end'):
                boot_sequence_end_index = i
                break
        
        logger.debug(f"Boot sequence end found at index {boot_sequence_end_index}")

        # Create and save game seed after boot sequence
        game_seed = {
            'conversation_id': generate_conversation_id(),
            'messages': final_messages,
            'location': "Custom World",  # Use first line as location
            'description': "This is a custom world created by the player at " + datetime.now().isoformat(),
            'boot_sequence_end_index': boot_sequence_end_index,
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'intro_blurb': get_intro_blurb_string(),
            'intro_blurb_date': datetime.now().isoformat(),
            'gameplay_system_prompt': get_gameplay_system_prompt(),
            'gameplay_system_prompt_date': datetime.now().isoformat(),
            'game_setup_system_prompt': game_setup_system_prompt,
            'game_setup_system_prompt_date': datetime.now().isoformat(),
            'summarizer_system_prompt': get_summarizer_system_prompt(),
            'summarizer_system_prompt_date': datetime.now().isoformat(),
            'game_has_begun': False
        }
        
        write_game_seed(game_seed)
        logger.debug(f"Saved game seed with ID: {game_seed['conversation_id']}")

        return final_messages
        
    except Exception as e:
        logger.error(f"Error reading boot sequence messages: {e}")
        raise

def execute_final_startup_instruction(conversation: Dict):
    """
    Execute the final startup instruction after world generation is complete.
    Returns the updated conversation and any new messages.
    """
    logger.debug("Executing final startup instruction")
    try:
        # Get the final instruction content
        final_instruction = get_final_startup_instruction_string()
        
        # Convert the instruction to a user message with timestamp
        user_message = convert_user_text_to_message(final_instruction)
        user_message['timestamp'] = datetime.now().isoformat()
        conversation['messages'].append(user_message)
        
        # Get GM response with timestamp
        gm_response, usage_data = get_next_gm_response(conversation['messages'], conversation['gameplay_system_prompt'], temperature=0.7)
        gm_response['timestamp'] = datetime.now().isoformat()
        conversation['messages'].append(gm_response)
        new_messages = [gm_response]
        
        # Handle any tool use if requested
        if isToolUseRequest(gm_response):
            logger.debug("Tool use requested during final startup instruction")
            tool_result = generate_tool_result(gm_response)
            tool_result['timestamp'] = datetime.now().isoformat()
            conversation['messages'].append(tool_result)
            new_messages.append(tool_result)
            
            tool_response, _ = get_next_gm_response(conversation['messages'], conversation['gameplay_system_prompt'], temperature=0.7)
            tool_response['timestamp'] = datetime.now().isoformat()
            conversation['messages'].append(tool_response)
            new_messages.append(tool_response)
        
        return conversation, new_messages
        
    except Exception as e:
        logger.error(f"Error executing final startup instruction: {e}")
        raise


