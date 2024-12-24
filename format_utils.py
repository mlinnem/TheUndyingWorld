from flask import jsonify, session

import logging
import json
import traceback

logger = logging.getLogger(__name__)


def format_user_message(user_message):
    return {
        "role": "user",
        "content": [{
            "type": "text",
            "text": user_message
        }]
    }

def _parse_scene_analysis(scene_text):
    """Parse scene analysis text into structured data."""
    if not scene_text.startswith('#'):
        logger.error("Scene analysis block doesn't start with #")
        return None, None
        
    components = scene_text.split('#')[1:]
    if len(components) not in [2, 4]:
        logger.error("Scene analysis block has unexpected number of components")
        return None, None
        
    analysis_data = {}
    object_type = []
    
    # Process components in pairs
    for i in range(0, len(components), 2):
        analysis_type = components[i].strip().lower()
        
        all_but_title = components[i].split('\n')[1:]
        analysis = "\n".join(all_but_title).strip()
        
        if "difficulty" in analysis_type:
            value = components[i + 1].split('\n')[1].strip()
            analysis_data["difficulty"] = {
                "difficulty_analysis": analysis,
                "difficulty_target": int(value) if value.isdigit() else value
            }
            object_type.append("difficulty")
            
        elif "world reveal" in analysis_type:
            value = components[i + 1].split('\n')[1].strip()
        
            analysis_data["world reveal"] = {
                "world_reveal_analysis": analysis,
                "world_reveal_level": value
            }
            object_type.append("world_reveal")
            
    object_type = "_and_".join(sorted(object_type)) + "_object" if object_type else None
    return analysis_data, object_type

def format_messages_for_client(messages):
    try:
        formatted_messages = []
        
        for message in messages:
            if message['role'] not in ['user', 'assistant']:
                logger.warning(f"Unknown message role: {message['role']}")
                formatted_messages.append(message)
                continue
                
            if message['role'] == 'user':
                formatted_messages.append(message)
                continue
                
            # Handle assistant messages
            logger.debug(f"here comes message: {message}")
            if len(message['content']) >= 2 and message['content'][1]['type'] == 'tool_use':
                try:
                    logger.debug(f"message is a tool use: {message}")
                    scene_analysis_object, object_type = _parse_scene_analysis(message['content'][0]['text'])
                    if scene_analysis_object:
                        new_message = message.copy()
                        new_message['content'][0] = {
                            "type": object_type,
                            object_type: scene_analysis_object
                        }
                        formatted_messages.append(new_message)
                    else:
                        formatted_messages.append(message)
                except Exception as e:
                    logger.error(f"Error parsing scene analysis: {e}", exc_info=True)
                    formatted_messages.append(message)
                
            else:
                formatted_messages.append(message)
                
        return formatted_messages
        
    except Exception as e:
        logger.error(f"Error formatting messages for client: {e}", exc_info=True)
        return messages