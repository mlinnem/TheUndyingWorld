from flask import jsonify, session


import json
import traceback

import logging
logger = logging.getLogger(__name__)



def produce_user_message_for_server(user_message):
    return {
        "role": "user",
        "content": [{
            "type": "text",
            "text": user_message
        }]
    }

# TODO: This is a bit messy, and could be cleaned up.

def _format_user_message(user_message):
    user_block = user_message['content'][0]['text']

    return [{
        "source": "client",
        "type": "user_message",
        "user_message": user_block
    }]

def _format_analysis(analysis_message):
    analysis_block = analysis_message['content'][0]['text']
    analysis_sections = analysis_block.split('#')[1:]

    analysis_objects = []
    
    # Process components in pairs
    for i in range(0, len(analysis_sections), 2):
        analysis = analysis_sections[i]
        analysis_type = analysis.split("\n")[0].strip().lower()
        analysis_content = "\n".join(analysis.split("\n")[1:])

        analysis_value_string = analysis_sections[i + 1].split('\n')[1].strip()
        if "difficulty" in analysis_type:
            analysis_value = int(analysis_value_string)

            analysis_object = {
                "source": "llm",
                "type": "difficulty_analysis",
                "difficulty_analysis": analysis_content,
                "difficulty_target": analysis_value
            }
            analysis_objects.append(analysis_object)
        elif "world" in analysis_type:
            analysis_value = analysis_value_string
            analysis_object = {
                "source": "llm",
                "type": "world_analysis",
                "world_analysis": analysis_content,
                "world_level": analysis_value
            }
            analysis_objects.append(analysis_object)
        else:
            logger.error(f"Unknown analysis type: {analysis_type}")

    return analysis_objects

def _format_rolls(roll_message):
    logger.debug(f"Formatting rolls: {roll_message}")
    roll_block = roll_message['content'][0]['content']
    logger.debug(f"roll_block: {roll_block}")
    roll_sections = roll_block.split('#')[1:]
    logger.debug(f"roll_sections: {roll_sections}")

    roll_objects = []
    for roll_section in roll_sections:
        logger.debug(f"roll_section: {roll_section}")
        if _header_contains(roll_section, ['difficulty', 'skill']):
            roll_object = {
                "source": "server",
                "type": "difficulty_roll",
                "difficulty_roll": int(roll_section.split('\n')[1].strip())
            }
            roll_objects.append(roll_object)
        elif _header_contains(roll_section, ['world', 'reveal']):
            roll_object = {
                "source": "server",
                "type": "world_roll",
                "world_roll": int(roll_section.split('\n')[1].strip())
            }
            roll_objects.append(roll_object)
        else:
            logger.error(f"Unknown roll message: {roll_section}")
            # Don't add this to the roll_messages
    return roll_objects

def _format_result(result_message):
    # Check if the message has the expected structure
    if not result_message.get('content') or not result_message['content'][0].get('text'):
        logger.error("Result message missing expected content structure")
        return []

    result_block = result_message['content'][0]['text']
    result_sections = result_block.split('#')[1:]
    result_objects = []
    for result_section in result_sections:
        # Skip empty sections
        if not result_section.strip():
            continue
            
        # Safely get the content after the header
        lines = result_section.split('\n')
        if len(lines) < 2:
            logger.error(f"Result section missing content: {result_section}")
            continue
            
        content = '\n'.join(lines[1:]).strip()
        
        if _header_contains(result_section, ['scene']): 
            resulting_scene_description_object = {
                "source": "server",
                "type": "resulting_scene_description",
                "resulting_scene_description": content
            }
            result_objects.append(resulting_scene_description_object)
        elif _header_contains(result_section, ['tracked']):
            tracked_operations_object = {
                "source": "server",
                "type": "tracked_operations",
                "tracked_operations": content
            }
            result_objects.append(tracked_operations_object)
        elif _header_contains(result_section, ['condition', 'table', 'player', 'data']):
            condition_table_object = {
                "source": "server",
                "type": "condition_table",
                "condition_table": content
            }
            result_objects.append(condition_table_object)
        else:
            logger.error(f"Unknown result message: {result_section}")
    return result_objects


# TODO: Make this and related functions smarter about map, quadrants, zones, etc.
def _format_map_data(map_data_message):
    map_data_block = map_data_message['content'][0]['text']
    data = _all_but_header(map_data_block)
    
    return [{
        "source": "llm",
        "type": "map_data",
        "map_data": data
    }]

def _format_ooc_message(ooc_message):
    ooc_block = ooc_message['content'][0]['text']
    if "#" in ooc_block:
        # Split by '#' and take sections after the first '#'
        sections = ooc_block.split('#')[1:]
        # For each section, remove the first line (header) and join remaining lines
        text = _all_but_header(sections[0])
    else:
        text = ooc_block

    return [{
        "source": "llm",
        "type": "ooc_message",
        "ooc_message": text
    }]

def _all_but_header(text):
    return '\n'.join(text.split('\n')[1:])

def format_error_object(error_type, error_message, original_message=None):
    return [{
        "source": "server",
        "type": "error",
        "error_type": error_type,
        "error_message": error_message,
        "original_message": original_message
    }]

def _split_message_sections(text):
    """Split a message into sections based on # headers, preserving any text before the first #"""
    parts = text.split('#')
    sections = []
    
    # If there's content before the first #, treat it as OOC
    if parts[0].strip():
        sections.append(('ooc', parts[0].strip()))
    
    # Process the rest of the sections
    for section in parts[1:]:
        if not section.strip():
            continue
        lines = section.split('\n')
        header = lines[0].strip().lower()
        content = '\n'.join(lines[1:])
        sections.append((header, content))
    
    return sections

def _process_mixed_content(message):
    """Process a message that might contain multiple types of content"""
    objects = []
    text = message['content'][0]['text']
    sections = _split_message_sections(text)
    
    for header_type, content in sections:
        if not header_type or not content:
            continue
            
        if header_type == 'ooc':
            objects.extend([{
                "source": "llm",
                "type": "ooc_message",
                "ooc_message": content
            }])
        else:
            # Reconstruct the section with its header for existing processors
            reconstructed = f"#{header_type}\n{content}"
            if any(term in header_type for term in ['difficulty', 'world']):
                objects.extend(_format_analysis({'content': [{'text': reconstructed}]}))
            elif 'result' in header_type:
                objects.extend(_format_result({'content': [{'text': reconstructed}]}))
            elif any(term in header_type for term in ['map', 'zone', 'quadrant']):
                objects.extend(_format_map_data({'content': [{'text': reconstructed}]}))

    return objects

def _is_mixed_content(message):
    """Check if the message contains multiple types of content"""
    if message['role'] == 'assistant' and message['content'][0]['type'] == 'text':
        text = message['content'][0]['text']
        sections = _split_message_sections(text)
        return len(sections) > 1
    return False

def produce_conversation_objects_for_client(messages):
    objects_for_client = []
    parsing_errors = []
    for index, message in enumerate(messages):
        
        try:
            if _is_user_message(message):
                logger.debug(f"Formatting user message: {message}")
                objects_for_client.extend(_format_user_message(message))
            elif _is_analysis(message):
                logger.debug(f"Formatting analysis: {message}")
                objects_for_client.extend(_format_analysis(message))
            elif _is_rolls(message):
                logger.debug(f"Formatting rolls: {message}")
                objects_for_client.extend(_format_rolls(message))
            elif _is_result(message):
                logger.debug(f"Formatting result: {message}")
                objects_for_client.extend(_format_result(message))
            elif is_map_data(message):
                logger.debug(f"Formatting map data: {message}")
                objects_for_client.extend(_format_map_data(message))
            elif _is_ooc_message(message):
                logger.debug(f"Formatting OOC message: {message}")
                objects_for_client.extend(_format_ooc_message(message))
            else:
                error_msg = f"Unable to identify a block type for message: {message}"
                logger.error(error_msg)
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
                objects_for_client.extend(format_error_object("parsing_message_error", error_msg))
                parsing_errors.append(f"Message of unknown type at index {index}: {error_msg}")
        except Exception as e:
            error_msg = f"Error formatting message at index {index}: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            logger.error(f"Problem message: {message}")
            objects_for_client.extend(format_error_object("parsing_message_error", "Failed to format message", message))
            parsing_errors.append(error_msg)

    return objects_for_client, parsing_errors

def _is_user_message(message):
    logger.debug(f"Checking if message is user: {message}")
    try:
        # Check if message is a dict and has required keys
        if not isinstance(message, dict) or 'role' not in message or 'content' not in message:
            return False
            
        # Check if content is a non-empty list
        if not isinstance(message['content'], list) or not message['content']:
            return False
            
        # Check if first content item has required structure
        if not isinstance(message['content'][0], dict) or 'type' not in message['content'][0]:
            return False
            
        return message['role'] == 'user' and message['content'][0]['type'] == 'text'
    except Exception as e:
        logger.error(f"Error in _is_user_message: {str(e)}")
        return False

def _is_analysis(message):
    logger.debug(f"Checking if message is analysis: {message}")
    if message['role'] == 'assistant':
        if len(message['content']) >= 2 and message['content'][1]['type'] == 'tool_use':
            return True
        else:
            if message['content'][0]['type'] == 'text':
                return _header_contains(message['content'][0]['text'], ['difficulty', 'world reveal'])
    else:
        return False
    
def _is_rolls(message):
    logger.debug(f"Checking if message is rolls: {message}")
    if message['role'] == 'user':
        if message['content'][0]['type'] == 'tool_result':
            if _header_contains(message['content'][0]['content'], ['difficulty', 'world reveal', 'roll']):
                return True
    return False
    
def _is_result(message):
    logger.debug(f"Checking if message is result: {message}")
    # This check should occur after is_analysis or else it will catch the analysis as a result
    if message['role'] == 'assistant':
        if message['content'][0]['type'] == 'text':
            if _header_contains(message['content'][0]['text'], ['result']):
                return True
    return False

def _is_ooc_message(message):
    logger.debug(f"Checking if message is OOC: {message}")
    if message['role'] == 'assistant':
        if message['content'][0]['type'] == 'text':
            if _header_contains(message['content'][0]['text'], ['ooc']):
                return True
            elif '#' not in message['content'][0]['text']:
                return True
    return False

def is_map_data(message):
    logger.debug(f"Checking if message is map data: {message}")
    if message['role'] == 'assistant':
        if message['content'][0]['type'] == 'text':
            if _header_contains(message['content'][0]['text'], ['map', 'zone', 'quadrant']):
                return True
    return False

def _header_contains(text_in_message, has_one_of_these_array):
    # Get first line and normalize it
    header = text_in_message.split("\n")[0].strip().lower()
    # Convert all search terms to lowercase and check if any are in the header
    return any(term.lower() in header for term in has_one_of_these_array)
