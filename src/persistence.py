import os
import json
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

CONVERSATIONS_DIR = "conversations"
LLM_INSTRUCTIONS_DIR = "LLM_instructions"

if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)


# Conversation functions

def read_conversation(conversation_id):
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            conversation_data = json.load(f)
            if 'location' not in conversation_data:
                conversation_data['location'] = 'Untitled location'
            if 'created_at' not in conversation_data:
                # Use 1970-01-01 as the "beginning of time" default date
                conversation_data['created_at'] = '1970-01-01T00:00:00'
            return conversation_data
    return None

def write_conversation(conversation):
    logger.info(f"Saving conversation {conversation['conversation_id']}")
    conversation_id = conversation['conversation_id']
    conversation['last_updated'] = datetime.now().isoformat()
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    with open(file_path, 'w') as f:
        json.dump(conversation, f, indent=2)

def delete_conversation(conversation_id):
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def read_all_conversation_ids():
    conversation_ids = []
    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.endswith(".json"):
            conversation_id = filename[:-5]  # Remove .json extension
            conversation_ids.append(conversation_id)
    return conversation_ids
  
# LLM instructions functions

def get_game_setup_system_prompt():
    """
    Returns the combined core lore and generative primer instructions as a formatted system prompt.
    """
    core_lore = _get_llm_instructions('core_lore')
    generative_primer = _get_llm_instructions('generative_primer')
    return [{
        "type": "text",
        "text": core_lore + "\n\n" + generative_primer,
        "cache_control": {"type": "ephemeral"}
    }]
    
def get_gameplay_system_prompt():
    """
    Returns the combined core lore and game manual instructions as a formatted system prompt.
    """
    core_lore = _get_llm_instructions('core_lore')
    game_manual = _get_llm_instructions('game_manual')
    return [{
        "type": "text",
        "text": core_lore + "\n\n" + game_manual,
        "cache_control": {"type": "ephemeral"}
    }]

def get_summarizer_system_prompt():
    """
    Returns the summarizer instructions as a formatted system prompt.
    """
    summarizer = _get_llm_instructions('summarizer')
    return [{
        "type": "text",
        "text": summarizer,
        "cache_control": {"type": "ephemeral"}
    }]

def get_world_gen_sequence_array():
    """
    Returns the world gen sequence as an array of instructions, with metadata about which
    instructions should be omitted from the final conversation.
    
    Returns:
        List of dicts, each containing:
            - instruction: str - The instruction text
            - omit_result: bool - Whether this instruction's result should be omitted
    """
    import re
    content = _get_llm_instructions('world_gen_sequence')
    
    import random
    # Split content into sections and parse metadata
    sections = []
    raw_sections = content.split("# Instruction")
    
    for section in raw_sections[1:]:  # Skip first empty section
        section = section.strip()
        omit_result = False
        
        if section.startswith("(omit result later)"):
            omit_result = True
            # Remove the marker
            section = section.replace("(omit result later)", "", 1).strip()
            
        if section:  # Skip empty sections
            sections.append({
                "instruction": section,
                "omit_result": omit_result
            })

    world_gen_instructions_w_omit_data = []
    for world_gen_instruction in sections:
        processed_section = re.sub(
            r'<<<(\d+)>>>', 
            lambda m: str(random.randint(1, int(m.group(1)))), 
            world_gen_instruction['instruction']
        )
        world_gen_instructions_w_omit_data.append({
            "text": processed_section,
            "omit_result": world_gen_instruction['omit_result']
        })
    
    return world_gen_instructions_w_omit_data

def get_intro_blurb_string():
    """
    Returns the intro blurb.
    """
    intro_blurb = _get_llm_instructions('intro_blurb')
    return intro_blurb

def get_final_startup_instruction_string():
    """
    Returns the final startup instruction.
    """
    final_startup_instruction = _get_llm_instructions('final_startup_instruction')
    return final_startup_instruction

def _get_llm_instructions(name):
    file_path = os.path.join(LLM_INSTRUCTIONS_DIR, f"{name}.md")
    with open(file_path, 'r') as f:
        return f.read()