from flask import session
import json
import traceback
import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from pydantic import ValidationError

from .message_models import (
    UserMessage, AssistantMessage, ErrorMessage, 
    TextContent, ToolUseContent, ToolResultContent,
    create_user_message, create_error_message, base_message_to_client_format
)

import logging
logger = logging.getLogger(__name__)




# TODO: This is a bit messy, and could be cleaned up.

def _format_user_message(user_message: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Formats a user message into a standardized structure using the Pydantic models.
    
    Args:
        user_message (Dict): The user message to format
        
    Returns:
        List[Dict]: Formatted message object
    """
    try:
        # Try to create a validated UserMessage using our model
        if 'role' not in user_message:
            user_message['role'] = 'user'  # Ensure role is set
            
        # Convert to our model for validation
        validated_message = UserMessage.model_validate(user_message)
        
        # Get the text content
        text_content = next((c for c in validated_message.content if c.type == "text"), None)
        if not text_content:
            raise ValueError("User message must contain text content")
            
        # Convert to client format
        return [{
            "source": "client",
            "type": "user_message",
            "user_message": text_content.text,
            "timestamp": datetime.datetime.now().isoformat()
        }]
        
    except (ValidationError, ValueError, StopIteration) as e:
        logger.error(f"Error validating user message: {type(e).__name__}: {str(e)}")
        logger.debug(f"Problematic message structure: {user_message}")
        
        # Try a more direct approach if the validation fails
        try:
            if isinstance(user_message, dict) and 'content' in user_message:
                content = user_message['content']
                if isinstance(content, list) and content and 'text' in content[0]:
                    user_text = content[0]['text']
                    logger.info(f"Recovered user message text using fallback method")
                    
                    return [{
                        "source": "client",
                        "type": "user_message",
                        "user_message": user_text,
                        "timestamp": datetime.datetime.now().isoformat()
                    }]
        except Exception as fallback_error:
            logger.error(f"Fallback extraction also failed: {str(fallback_error)}")
        
        # Return an error object if all extraction methods fail
        return format_error_object(
            error_type="user_message_format_error",
            error_message=f"Invalid user message format: {str(e)}",
            original_message=user_message,
            error_code="USER_MSG_FMT_001"
        )

def _format_analysis(analysis_message):
    analysis_block = analysis_message['content'][0]['text']
    analysis_sections = analysis_block.split('#')[1:]

    analysis_objects = []
    
    # Process components in pairs
    for i in range(0, len(analysis_sections), 2):
        analysis = analysis_sections[i]
        analysis_type = analysis.split("\n")[0].strip().lower()
        analysis_content = "\n".join(analysis.split("\n")[1:])

        # Check if there's a paired section before accessing it
        if i + 1 < len(analysis_sections):
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
        else:
            logger.error(f"Missing paired section for analysis type: {analysis_type}")

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
        try:
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
        except Exception as e:
            logger.error(f"Error processing roll section: {str(e)}")
            logger.error(f"Problematic roll section: {roll_section}")
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
def _format_world_gen_data(world_gen_data_message):
    world_gen_data_block = world_gen_data_message['content'][0]['text']
    data = _all_but_header(world_gen_data_block)
    
    return [{
        "source": "llm",
        "type": "world_gen_data",
        "world_gen_data": data
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

def format_error_object(error_type: str, error_message: str, 
                     original_message: Optional[Any] = None, 
                     error_context: Optional[Dict[str, Any]] = None, 
                     error_code: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Creates a standardized error object for client consumption.
    
    Args:
        error_type (str): Category of error (e.g., 'parsing_error', 'validation_error')
        error_message (str): Human-readable error description
        original_message (dict, optional): The original message that caused the error
        error_context (dict, optional): Additional context about where/why the error occurred
        error_code (str, optional): Machine-readable error code for client handling
    
    Returns:
        list: A list containing a single error object dictionary
    """
    try:
        # Create a validated error message using our model
        error_obj = create_error_message(
            error_type=error_type,
            error_message=error_message,
            original_message=original_message,
            error_context=error_context,
            error_code=error_code
        )
        
        # Convert to dictionary and return as a list to maintain compatibility
        return [error_obj.model_dump(exclude_none=True)]
        
    except ValidationError as e:
        # Log validation errors but still return something useful
        logger.error(f"Error creating error object: {str(e)}")
        
        # Fall back to manual construction if validation fails
        fallback_error = {
            "source": "server",
            "type": "error",
            "error_type": "internal_error",
            "error_message": f"Failed to create error object: {error_message}",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        return [fallback_error]

def _is_begin_game(message):
    logger.debug(f"Checking if message is begin game: {message}")
    if message['role'] == 'assistant':
        if message['content'][0]['type'] == 'text':
            if _header_contains(message['content'][0]['text'], ['begin game']):
                return True
    return False

def _format_begin_game(message):
    begin_game_block = message['content'][0]['text']
    text = _all_but_header(begin_game_block)
    
    return [{
        "source": "llm",
        "type": "begin_game",
        "begin_game_message": text
    }]

def produce_conversation_objects_for_client(messages: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[str]]:
    """
    Processes a list of messages and converts them to client-friendly objects.
    
    Args:
        messages (List[Dict]): List of messages to process
        
    Returns:
        Tuple[List[Dict], List[str]]: Processed objects and any parsing errors
    """
    objects_for_client = []
    parsing_errors = []
    
    if not isinstance(messages, list):
        error_msg = f"Expected messages to be a list, got {type(messages).__name__}"
        logger.error(error_msg)
        return format_error_object("invalid_input", error_msg, error_code="INVALID_MSGS_001"), [error_msg]
    
    for index, message in enumerate(messages):
        message_context = {"index": index, "message_type": message.get('role', 'unknown')}
        
        try:
            # Log message type identification - but in debug mode to avoid log spam
            logger.debug(f"Processing message at index {index}, role: {message.get('role')}")
            
            # Process the message based on its type
            if _is_user_message(message):
                logger.debug(f"Identified as user message: {message}")
                objects_for_client.extend(_format_user_message(message))
            elif _is_begin_game(message):
                logger.debug(f"Identified as begin game message")
                objects_for_client.extend(_format_begin_game(message))
            elif _is_analysis(message):
                logger.debug(f"Identified as analysis message")
                objects_for_client.extend(_format_analysis(message))
            elif _is_rolls(message):
                logger.debug(f"Identified as rolls message")
                objects_for_client.extend(_format_rolls(message))
            elif _is_result(message):
                logger.debug(f"Identified as result message")
                objects_for_client.extend(_format_result(message))
            elif _is_world_gen_data(message):
                logger.debug(f"Identified as world gen data message")
                objects_for_client.extend(_format_world_gen_data(message))
            elif _is_ooc_message(message):
                logger.debug(f"Identified as OOC message")
                objects_for_client.extend(_format_ooc_message(message))
            else:
                # Unknown message type - capture detailed information
                error_msg = f"Unable to identify message type at index {index}"
                error_context = {
                    "message_index": index,
                    "role": message.get('role', 'unknown'),
                    "content_type": (message.get('content', [{}])[0].get('type') 
                                    if isinstance(message.get('content'), list) and message.get('content') 
                                    else "unknown")
                }
                
                logger.error(f"{error_msg}: {error_context}")
                logger.error(f"Full message: {message}")
                
                objects_for_client.extend(format_error_object(
                    error_type="unknown_message_type", 
                    error_message=error_msg,
                    original_message=message,
                    error_context=error_context,
                    error_code="UNKNOWN_MSG_001"
                ))
                parsing_errors.append(f"Message of unknown type at index {index}")
                
        except Exception as e:
            # Handle any errors that occurred during formatting
            error_msg = f"Error processing message at index {index}: {str(e)}"
            error_context = {
                "message_index": index,
                "error_type": type(e).__name__,
                "message_role": message.get('role', 'unknown')
            }
            
            logger.error(error_msg, exc_info=True)
            logger.error(f"Problematic message: {message}")
            
            objects_for_client.extend(format_error_object(
                error_type="message_processing_error", 
                error_message=f"Failed to process message: {str(e)}",
                original_message=message,
                error_context=error_context,
                error_code="PROCESS_ERROR_001"
            ))
            parsing_errors.append(error_msg)

    return objects_for_client, parsing_errors

def _is_user_message(message: Dict[str, Any]) -> bool:
    """
    Determines if a message is a valid user message using our Pydantic model for validation.
    
    Args:
        message: The message to check
        
    Returns:
        bool: True if message is a valid user message, False otherwise
    """
    try:
        # Only log at debug level to prevent log spam
        logger.debug("Checking if message is user message")
        
        # Quick preliminary checks before trying Pydantic validation
        if not isinstance(message, dict):
            logger.debug("Message is not a dictionary")
            return False
            
        if 'role' not in message or message['role'] != 'user':
            logger.debug(f"Message role is not 'user': {message.get('role')}")
            return False
            
        if 'content' not in message or not isinstance(message['content'], list) or not message['content']:
            logger.debug("Message has invalid or missing content")
            return False
        
        # Try to validate with our Pydantic model
        UserMessage.model_validate(message)
        
        # If we got here, validation passed
        return True
        
    except ValidationError as e:
        # Don't log the full error at ERROR level to prevent log spam
        logger.debug(f"Message failed UserMessage validation: {str(e)}")
        return False
        
    except Exception as e:
        # Log other errors with the specific exception type for better debugging
        logger.error(f"Error in _is_user_message: {type(e).__name__}: {str(e)}")
        logger.debug(f"Problematic message structure: {message}")
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

def _is_world_gen_data(message):
    logger.debug(f"Checking if message is map data: {message}")
    if message['role'] == 'assistant':
        if message['content'][0]['type'] == 'text':
            if _header_contains(message['content'][0]['text'], ['map', 'zone', 'quadrant', 'world gen data']):
                return True
    return False

def _header_contains(text_in_message, has_one_of_these_array):
    # Get first line and normalize it
    header = text_in_message.split("\n")[0].strip().lower()
    # Convert all search terms to lowercase and check if any are in the header
    return any(term.lower() in header for term in has_one_of_these_array)

def produce_whisper_dummy_message():
    return {
        "role": "user",
        "content": [{
            "type": "text",
            "text": "[Ignore this message. This is only included to solicit an additional response from the LLM, after we have injected the prior additional context into the assistant chat history. This message will be removed from the transcript afterwards.]"
        }]
    }
