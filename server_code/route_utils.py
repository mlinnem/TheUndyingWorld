import logging
import traceback

logger = logging.getLogger(__name__)

def convert_user_text_to_message(user_text):
    return {
        "role": "user",
        "content": [{
            "type": "text",
            "text": user_text
        }]
    }

def convert_messages_to_cos(messages):

    if not isinstance(messages, (list, tuple)):
        logger.error(f"Invalid messages format: expected list or tuple, got {type(messages)}")
        return []

    cos = []
    try:
        for message in messages:
            if not isinstance(message, dict) or 'role' not in message or 'content' not in message:
                logger.warning(f"Skipping invalid message format: {message}")
                continue

            if message['role'] == 'user':
                content = message['content']
                if not isinstance(content, list):
                    logger.warning(f"Skipping invalid user content format: {content}")
                    continue

                for item in content:
                    try:
                        if not isinstance(item, dict) or 'type' not in item:
                            continue
                        
                        item_type = item['type']
                        if item_type == 'text':
                            text = item['text']
                            cos.append({'type': 'user_message', 'text': text})
                        elif item_type == 'tool_result':
                            tool_result_content = item['content']
                            sections = tool_result_content.split('#')
                            del tool_result_content  # Free up memory after splitting
                            
                            for i, section in enumerate(sections):
                                try:
                                    header, _, body = section.partition('\n')
                                    c_header = header.strip().lower()
                                    body = body.strip()

                                    if i == 0:
                                        continue # discard first section, which should be empty string
                                    if 'difficulty roll' in c_header:
                                        try:
                                            integer = int(body)
                                            if integer < 1 or integer > 100:
                                                logger.warning(f"Invalid negative difficulty target: {integer}")
                                                continue
                                            cos.append({'type': 'difficulty_roll', 'integer': integer})
                                        except ValueError:
                                            logger.error(f"Invalid difficulty roll value: {body}")
                                            continue
                                    elif 'world roll' in c_header or 'reveal' in c_header:
                                        try:
                                            integer = int(body)
                                            if integer < 1 or integer > 100:
                                                logger.warning(f"Invalid negative world roll: {integer}")
                                                continue
                                            cos.append({'type': 'world_reveal_roll', 'integer': integer})
                                        except ValueError:
                                            logger.error(f"Invalid world reveal roll value: {body}")
                                            continue
                                    else:
                                        logger.warning(f"Unrecognized tool use section: {header}")
                                        continue
                                except Exception as e:
                                    logger.error(f"Error processing tool use section: {str(e)}")
                                    continue
                        else:
                            logger.warning(f"Unrecognized item type: {item_type}")
                            continue
                    except KeyError as e:
                        logger.error(f"Missing required field {e} in item: {item}")
                        continue

            elif message['role'] == 'assistant':
                content = message['content']
                if not isinstance(content, list):
                    logger.warning(f"Skipping invalid assistant content format: {content}")
                    continue

                for item in content:
                    try:
                        if not isinstance(item, dict) or 'type' not in item:
                            continue

                        item_type = item['type']
                        if item_type == 'text':
                            text = item['text']
                            sections = text.split('#')
                            del text  # Free up memory after splitting
                            
                            for i, section in enumerate(sections):
                                try:
                                    header, _, body = section.partition('\n')
                                    c_header = header.strip().lower()
                                    body = body.strip()

                                    if i == 0:
                                        if section.strip():
                                            logger.warning(f"Out of section text: {body[:50]}...")
                                            cos.append({'type': 'out_of_section_text', 'text': body})
                                    else:
                                        if 'ooc message' in c_header:
                                            logger.debug(f"OOC message: {body}")
                                            cos.append({'type': 'ooc_message', 'text': body})
                                        elif 'map' in c_header or 'zone' in c_header or 'quad' in c_header or 'world gen data' in c_header:
                                            logger.debug(f"header: {c_header}")
                                            logger.debug(f"Map data: {body}")
                                            cos.append({'type': 'world_gen_data', 'text': body})
                                        elif 'difficulty analysis' in c_header:
                                            logger.debug(f"Difficulty analysis: {body}")
                                            cos.append({'type': 'difficulty_analysis', 'text': body})
                                        elif 'difficulty target' in c_header:
                                            try:
                                                integer = int(body)
                                                if integer < 1 or integer > 100:
                                                    logger.warning(f"Invalid negative difficulty target: {integer}")
                                                    continue
                                                cos.append({'type': 'difficulty_target', 'text': integer})
                                            except ValueError:
                                                # This is to handle the case when it is 'Trivial' but we might want to validate more here.
                                                cos.append({'type': 'difficulty_target', 'text': body})
                                        elif 'reveal analysis' in c_header:
                                            logger.debug(f"reveal analysis: {body}")
                                            cos.append({'type': 'world_reveal_analysis', 'text': body})
                                        elif 'reveal level' in c_header:
                                            logger.debug(f"reveal level: {body}")
                                            cos.append({'type': 'world_reveal_level', 'text': body})
                                        elif 'resulting scene' in c_header:
                                            logger.debug(f"Resulting scene description: {body}")
                                            cos.append({'type': 'resulting_scene_description', 'text': body})
                                        elif 'tracked operations' in c_header:
                                            logger.debug(f"Tracked operations: {body}")
                                            cos.append({'type': 'tracked_operations', 'text': body})
                                        elif 'condition' in c_header:
                                            logger.debug(f"Condition table: {body}")
                                            cos.append({'type': 'condition_table', 'text': body})
                                        else:
                                            logger.warning(f"Unrecognized section: {header}")
                                            cos.append({'type': 'unrecognized_section', 'header_text': header.strip(), 'body_text': body})
                                except Exception as e:
                                    logger.error(f"Error processing section '{header[:50]}...': {str(e)}\n{traceback.format_exc()}")
                                    continue
                        elif item_type == 'tool_use':
                            name = item['name']
                            cos.append({'type': 'tool_use', 'function_name': name})
                        else:
                            logger.warning(f"Unrecognized item type: {item_type}")
                            continue
                    except Exception as e:
                        logger.error(f"Error processing assistant content item: {str(e)}")
                        continue
            else:
                logger.warning(f"Message has invalid format: role is neither 'user' nor 'assistant'. message: {message}")

            # Check for boot sequence end
            if message.get('is_boot_sequence_end'):
                cos.append({'type': 'boot_sequence_end'})

    except Exception as e:
        logger.error(f"Error in convert_messages_to_cos: {str(e)}\n{traceback.format_exc()}")
    
    logger.debug(f"First cleaned message: {cos[0] if cos else 'No messages'}")
    return cos

def filter_conversation_objects(conversation_objects):
    logger.info("Filtering conversation objects: " + str(len(conversation_objects)))
    """
    Filter out specific conversation objects that should not be sent to the user.
    
    Args:
        conversation_objects (list): List of conversation objects to filter
        
    Returns:
        list: Filtered list of conversation objects
    """
    if not conversation_objects:
        return []
        
    filtered_types = {
        'world_gen_data',  # Filter out map generation data
        'world_reveal_roll',  # Filter out world reveal roll
        'world_reveal_analysis',  # Filter out world reveal analysis
        'world_reveal_level',  # Filter out world reveal level
        'tracked_operations',  # Filter out tracked operations
    }
    
    # Find the index of boot_sequence_end if it exists
    boot_end_index = next(
        (i for i, obj in enumerate(conversation_objects) 
         if obj.get('type') == 'boot_sequence_end'),
        -1
    )
    logger.debug("boot_end_index: " + str(boot_end_index))
    
    # If boot_sequence_end was found, only keep objects after it
    start_index = (boot_end_index + 1) - 1 if boot_end_index >= 0 else 0
    
    # Create filtered list and log filtered objects
    result = []
    for obj in conversation_objects[start_index:]:
        if obj.get('type') in filtered_types:
            logger.debug(f"Filtering out object of type: {obj.get('type')}")
            logger.debug(f"Object: {obj}")
        else:
            result.append(obj)
            
    logger.info("conversation objects after filtering: " + str(len(result)))
    return result