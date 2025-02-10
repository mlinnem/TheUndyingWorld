import os

from datetime import datetime
from .config import *
from .persistence import *
from .route_utils import *
from .llm_communication import *
from .format_utils import *

import logging
logger = logging.getLogger(__name__)

# Update the logger configuration
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)

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




# Conversation functions


def save_conversation(conversation):
    logger.info(f"Saving conversation {conversation['conversation_id']}")
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
    logger.info("Creating new conversation from scratch")
    
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

    logger.info(f"Created conversation with ID: {conversation['conversation_id']}")
    
    # Save the updated conversation

    save_conversation(conversation)
    logger.info("Saved conversation")

    logger.info(f"Conversation created:" + conversation_id)
    
    return conversation

def create_conversation_from_seed(seed_id):
    logger.info("Creating new conversation based on seed: " + seed_id)

    seed = read_game_seed(seed_id)

    # Filter out user messages from seed, keeping only assistant messages

    logger.debug("Filtering out user messages from seed")
    logger.debug("Pre-filtering messages: " + str(len(seed['messages'])))

    # No user messages in initial conversation (if we haven't already filtered out elsewhere)

    seed['messages'] = [msg for msg in seed['messages'] if msg['role'] == 'assistant']
 
    logger.debug("Post-filtering messages: " + str(len(seed['messages'])))
    
    conversation_id = generate_conversation_id()
    # Create short date string for conversation name
    short_date = datetime.now().strftime("%b %d")

    conversation = {
        'conversation_id': conversation_id,
        'name': seed['location'] + " (" + short_date +")",
        'location': seed['location'],
        'messages': seed['messages'],
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

    logger.info(f"Created conversation based on seed with new ID: {conversation['conversation_id']}")
    
    # Save the updated conversation

    logger.info("Saved conversation")

    logger.info(f"Conversation created:" + conversation_id)
    
    return conversation

def update_conversation_cache_points(conversation):
    logger.info(f"Updating cache points for conversation {conversation['conversation_id']}")
    
    # Add a metadata field to track cache point types
    def add_cache_control(content_block, cache_purpose):
        # Create a deep copy of the original block to preserve all fields
        modified_block = content_block.copy()
        
        # Add/update cache control and metadata while preserving existing data
        modified_block["cache_control"] = {"type": "ephemeral"}  # Required by API
        modified_block["cache_metadata"] = {
            "purpose": cache_purpose,  # 'permanent' or 'conversation'
            "timestamp": datetime.now().isoformat()
        }

        if content_block['type'] == "text":
            return modified_block
        elif content_block['type'] == "tool_use":
            return modified_block
        elif content_block['type'] == "tool_result":
            return modified_block
        else:
            raise Exception(f"Unknown message type: {content_block['type']}")

    # Helper function to remove cache control from a content block
    def remove_cache_control(content_block):
        if content_block['type'] == "text":
            return {"type": "text", "text": content_block['text']}
        elif content_block['type'] == "tool_use":
            return {
                "type": "tool_use",
                "id": content_block['id'],
                "name": content_block['name'],
                "input": content_block['input']
            }
        elif content_block['type'] == "tool_result":
            return {
                "type": "tool_result",
                "tool_use_id": content_block['tool_use_id'],
                "content": content_block['content']
            }
        else:
            raise Exception(f"Unknown message type: {content_block['type']}")

    # First, remove all cache points
    logger.info("Removing all existing cache points")
    for message in conversation['messages']:
        message['content'][0] = remove_cache_control(message['content'][0])

    # Determine the boot sequence length
    boot_sequence_length = next(
        (i for i, msg in enumerate(conversation['messages']) 
         if msg.get('is_boot_sequence_end', False)),
        0
    )
    logger.info(f"Boot sequence length detected: {boot_sequence_length}")

    total_messages = len(conversation['messages'])
    logger.info(f"Total messages in conversation: {total_messages}")
    
    # Handle permanent cache point
    if total_messages <= boot_sequence_length + 50:
        # Set permanent cache at end of boot sequence
        if boot_sequence_length > 0:
            logger.info(f"Setting permanent cache point at boot sequence end (message {boot_sequence_length - 1})")
            conversation['messages'][boot_sequence_length - 1]['content'][0] = \
                add_cache_control(conversation['messages'][boot_sequence_length - 1]['content'][0], "ephemeral")
    else:
        # Set permanent cache at message 50 after boot sequence
        permanent_cache_index = boot_sequence_length + 49
        logger.info(f"Setting permanent cache point at message 50 after boot (message {permanent_cache_index})")
        conversation['messages'][permanent_cache_index]['content'][0] = \
            add_cache_control(conversation['messages'][permanent_cache_index]['content'][0], "ephemeral")

    # Handle conversation cache point
    messages_after_initial = total_messages - (boot_sequence_length + 50)
    if messages_after_initial > 0:
        conversation_cache_index = total_messages - (messages_after_initial % 20) - 1
        if conversation_cache_index > boot_sequence_length + 49:
            logger.info(f"Setting conversation cache point at message {conversation_cache_index}")
            conversation['messages'][conversation_cache_index]['content'][0] = \
                add_cache_control(conversation['messages'][conversation_cache_index]['content'][0], "ephemeral")
    else:
        logger.info("No conversation cache point needed yet (fewer than 50 messages after boot)")

    return conversation

def advance_conversation(user_message, conversation, should_create_generated_plot_info):
    new_messages = []

    if should_create_generated_plot_info:
        logger.info("Creating generated plot info")
        # First create the generated plot info
        plot_messages = create_dynamic_world_gen_data_messages(conversation['messages'], conversation['game_setup_system_prompt'])
        conversation['messages'].extend(plot_messages)
        new_messages.extend(plot_messages)
        
        # Then execute the final startup instruction
        logger.info("Executing final startup instruction")
        conversation, final_messages = execute_final_startup_instruction(conversation)
        new_messages.extend(final_messages)
        
        # Update cache points after boot sequence is complete
        logger.info("Boot sequence completed, updating cache points")
        conversation = update_conversation_cache_points(conversation)
        
        logger.info("Boot sequence and cache point setup completed successfully")
        return conversation, new_messages
        # Check if we need to inject the begin game message
      
   
    else:
        conversation['messages'].append(user_message)
        
        # get and save gm response
        gm_response_json, usage_data = get_next_gm_response(conversation['messages'], conversation['gameplay_system_prompt'], temperature=0.5)
        conversation['messages'].append(gm_response_json)
        new_messages = [gm_response_json]

        # if gm requested tool use
        if (isToolUseRequest(gm_response_json)):
            logger.info("tool use request detected")
            # generate and save tool result
            tool_result_json = generate_tool_result(gm_response_json)
            conversation['messages'].append(tool_result_json)
            new_messages.append(tool_result_json)

            # get and save gm response to tool result
            tool_use_response_json, usage_data = get_next_gm_response(conversation['messages'], conversation['gameplay_system_prompt'], temperature=0.8)
            conversation['messages'].append(tool_use_response_json)
            new_messages.append(tool_use_response_json)
        else:
            logger.info("no tool use request detected")
        
        # update caching or perform summarization if necessary
        if usage_data['total_input_tokens'] >= MAX_TOTAL_INPUT_TOKENS:
            conversation = summarize_with_gm(conversation)
            update_conversation_cache_points(conversation)
        elif usage_data['uncached_input_tokens'] >= MAX_UNCACHED_INPUT_TOKENS:
            conversation = update_conversation_cache_points(conversation)

        conversation['game_has_begun'] = True

        return conversation, new_messages

def create_dynamic_world_gen_data_messages(existing_messages, game_setup_system_prompt):
    logger.info("Creating dynamic world gen data messages")
    try:
        import random
        import re   

        # Get pre-parsed instruction sections
        world_gen_instructions_w_omit_data = get_world_gen_sequence_array()
        
        temp_conversation = {
            'messages': existing_messages.copy(),
            'game_setup_system_prompt': game_setup_system_prompt
        }

        logger.info(f"Starting boot sequence with {len(world_gen_instructions_w_omit_data)} messages")
        
        final_messages = []
        
        for i, world_gen_instruction_w_omit_data in enumerate(world_gen_instructions_w_omit_data):
            logger.info(f"Processing boot sequence message {i+1}/{len(world_gen_instructions_w_omit_data)}")
            try:
                # Convert and add user message
                world_gen_instruction = convert_user_text_to_message(world_gen_instruction_w_omit_data['text'])
                temp_conversation['messages'].append(world_gen_instruction)
                
                # Get GM response
                gm_response, usage_data = get_next_gm_response(temp_conversation['messages'],temp_conversation['game_setup_system_prompt'], temperature=0.84)
                temp_conversation['messages'].append(gm_response)

                if not world_gen_instruction_w_omit_data['omit_result']:
                    final_messages.append(gm_response)
                
                # Mark the last GM response of the boot sequence
                if i == len(world_gen_instructions_w_omit_data) - 1:
                    logger.info("Marking last GM response as boot sequence end")
                    gm_response['is_boot_sequence_end'] = True
                
                # Handle tool use if requested
                if isToolUseRequest(gm_response):
                    logger.info("Tool use requested during boot sequence")  
                    tool_result = generate_tool_result(gm_response)
                    temp_conversation['messages'].append(tool_result)
                    
                    tool_response, _ = get_next_gm_response(temp_conversation['messages'], game_setup_system_prompt, temperature=0.8)
                    temp_conversation['messages'].append(tool_response)     
                    
                    if i == len(world_gen_instructions_w_omit_data) - 1:
                        logger.info("Moving boot sequence end marker to tool response")
                        gm_response.pop('is_boot_sequence_end', None)
                        tool_response['is_boot_sequence_end'] = True
                    
                    if not world_gen_instruction_w_omit_data['omit_result']:
                        final_messages.append(tool_result)
                        final_messages.append(tool_response)
                
            except Exception as e:
                logger.error(f"Error in boot sequence at message '{world_gen_instruction_w_omit_data['text']}': {e}")
                raise

        # Create and save game seed after boot sequence
        game_seed = {
            'conversation_id': generate_conversation_id(),
            'messages': final_messages,
            'location': "Custom World",  # Use first line as location
            'description': "This is a custom world created by the player at " + datetime.now().isoformat(),
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
        logger.info(f"Saved game seed with ID: {game_seed['conversation_id']}")

        return final_messages
        
    except Exception as e:
        logger.error(f"Error reading boot sequence messages: {e}")
        raise

def execute_final_startup_instruction(conversation: Dict):
    """
    Execute the final startup instruction after world generation is complete.
    Returns the updated conversation and any new messages.
    """
    logger.info("Executing final startup instruction")
    try:
        # Get the final instruction content
        final_instruction = get_final_startup_instruction_string()
        
        # Convert the instruction to a user message
        user_message = convert_user_text_to_message(final_instruction)
        conversation['messages'].append(user_message)
        
        # Get GM response
        gm_response, usage_data = get_next_gm_response(conversation['messages'], conversation['gameplay_system_prompt'], temperature=0.7)
        conversation['messages'].append(gm_response)
        new_messages = [gm_response]
        
        # Handle any tool use if requested
        if isToolUseRequest(gm_response):
            logger.info("Tool use requested during final startup instruction")
            tool_result = generate_tool_result(gm_response)
            conversation['messages'].append(tool_result)
            new_messages.append(tool_result)
            
            tool_response, _ = get_next_gm_response(conversation['messages'], conversation['gameplay_system_prompt'], temperature=0.7)
            conversation['messages'].append(tool_response)
            new_messages.append(tool_response)
        
        return conversation, new_messages
        
    except Exception as e:
        logger.error(f"Error executing final startup instruction: {e}")
        raise


