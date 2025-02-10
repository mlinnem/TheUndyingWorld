import os
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Turn on debug logging
logging.basicConfig(level=logging.DEBUG)

CONVERSATIONS_DIR = "persistent/conversations"
LLM_INSTRUCTIONS_DIR = "LLM_instructions"
GAME_SEEDS_DIR = "persistent/game_seeds"

if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)


# Conversation functions

def read_conversation(conversation_id):
    logger.info(f"Reading conversation {conversation_id}")
    file_path = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            conversation_data = json.load(f)
            if 'location' not in conversation_data:
                conversation_data['location'] = 'Untitled location'
            if 'created_at' not in conversation_data:
                # Use 1970-01-01 as the "beginning of time" default date
                conversation_data['created_at'] = '1970-01-01T00:00:00'
            if 'intro_blurb' not in conversation_data:
                conversation_data['intro_blurb'] = get_intro_blurb_string()
                conversation_data['intro_blurb_date'] = datetime.now().isoformat()
            if 'gameplay_system_prompt' not in conversation_data:
                logger.warning("No gameplay_system_prompt found in file. Setting gameplay_system_prompt to default: " + conversation_id)
                conversation_data['gameplay_system_prompt'] = get_gameplay_system_prompt()
                conversation_data['gameplay_system_prompt_date'] = datetime.now().isoformat()
            if 'game_setup_system_prompt' not in conversation_data:
                logger.warning("No game_setup_system_prompt found in file. Setting game_setup_system_prompt to default: " + conversation_id)
                conversation_data['game_setup_system_prompt'] = get_game_setup_system_prompt()
                conversation_data['game_setup_system_prompt_date'] = datetime.now().isoformat()
            if 'summarizer_system_prompt' not in conversation_data:
                logger.warning("No summarizer_system_prompt found in file. Setting summarizer_system_prompt to default: " + conversation_id)
                conversation_data['summarizer_system_prompt'] = get_summarizer_system_prompt()
                conversation_data['summarizer_system_prompt_date'] = datetime.now().isoformat()
            if 'game_setup_system_prompt_date' not in conversation_data:
                logger.warning("No game_setup_system_prompt_date found in file. Setting game_setup_system_prompt_date to now: " + conversation_id)
                conversation_data['game_setup_system_prompt_date'] = datetime.now().isoformat()
            if 'gameplay_system_prompt_date' not in conversation_data:
                logger.warning("No gameplay_system_prompt_date found in file. Setting gameplay_system_prompt_date to now: " + conversation_id)
                conversation_data['gameplay_system_prompt_date'] = datetime.now().isoformat()
            if 'intro_blurb_date' not in conversation_data:
                logger.warning("No intro_blurb_date found in file. Setting intro_blurb_date to now: " + conversation_id)
                conversation_data['intro_blurb_date'] = datetime.now().isoformat()
            if 'summarizer_system_prompt_date' not in conversation_data:
                logger.warning("No summarizer_system_prompt_date found in file. Setting summarizer_system_prompt_date to now: " + conversation_id)
                conversation_data['summarizer_system_prompt_date'] = datetime.now().isoformat()
            if 'intro_blurb' not in conversation_data:
                logger.warning("No intro_blurb found in file. Setting intro_blurb to default: " + conversation_id)
                conversation_data['intro_blurb'] = get_intro_blurb_string()
                conversation_data['intro_blurb_date'] = datetime.now().isoformat()
            if 'intro_blurb_date' not in conversation_data:
                logger.warning("No intro_blurb_date found in file. Setting intro_blurb_date to now: " + conversation_id)
                conversation_data['intro_blurb_date'] = datetime.now().isoformat()
            if 'game_has_begun' not in conversation_data:
                logger.warning("No game_has_begun found in file. Setting game_has_begun to False: " + conversation_id)
                conversation_data['game_has_begun'] = True
                conversation_data['game_has_begun_date'] = datetime.now().isoformat()
            if 'game_has_begun_date' not in conversation_data and conversation_data['game_has_begun']:
                logger.warning("No game_has_begun_date found in file, even though game_has_begun is True. Setting game_has_begun_date to now: " + conversation_id)
                conversation_data['game_has_begun_date'] = datetime.now().isoformat()
            logger.info(f"Conversation {conversation_id} loaded successfully")
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
  
# Game seed functions

def read_game_seed(conversation_id):
    logger.info("Reading game seed: " + conversation_id)
    file_path = os.path.join(GAME_SEEDS_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            conversation_data = json.load(f)
            if 'id' not in conversation_data:
                logger.warning("No ID found in file. Setting game seed id: " + conversation_id)
                conversation_data['id'] = conversation_id
            if 'location' not in conversation_data:
                logger.warning("No location found in file. Setting location to 'No location': " + conversation_id)
                conversation_data['location'] = 'No location'
            if 'description' not in conversation_data:
                logger.warning("No description found in file. Setting description to 'No description': " + conversation_id)
                conversation_data['description'] = 'No description'
            if 'created_at' not in conversation_data:
                logger.warning("No created_at found in file. Setting created_at to '1970-01-01T00:00:00': " + conversation_id)
                # Use 1970-01-01 as the "beginning of time" default date
                conversation_data['created_at'] = '1970-01-01T00:00:00'
            if 'intro_blurb' not in conversation_data:
                conversation_data['intro_blurb'] = get_intro_blurb_string()
                conversation_data['intro_blurb_date'] = datetime.now().isoformat()
            if 'gameplay_system_prompt' not in conversation_data:
                logger.warning("No gameplay_system_prompt found in file. Setting gameplay_system_prompt to default: " + conversation_id)
                conversation_data['gameplay_system_prompt'] = get_gameplay_system_prompt()
                conversation_data['gameplay_system_prompt_date'] = datetime.now().isoformat()
            if 'game_setup_system_prompt' not in conversation_data:
                logger.warning("No game_setup_system_prompt found in file. Setting game_setup_system_prompt to default: " + conversation_id)
                conversation_data['game_setup_system_prompt'] = get_game_setup_system_prompt()
                conversation_data['game_setup_system_prompt_date'] = datetime.now().isoformat()
            if 'summarizer_system_prompt' not in conversation_data:
                logger.warning("No summarizer_system_prompt found in file. Setting summarizer_system_prompt to default: " + conversation_id)
                conversation_data['summarizer_system_prompt'] = get_summarizer_system_prompt()
                conversation_data['summarizer_system_prompt_date'] = datetime.now().isoformat()
            if 'game_setup_system_prompt_date' not in conversation_data:
                logger.warning("No game_setup_system_prompt_date found in file. Setting game_setup_system_prompt_date to now: " + conversation_id)
                conversation_data['game_setup_system_prompt_date'] = datetime.now().isoformat()
            if 'gameplay_system_prompt_date' not in conversation_data:
                logger.warning("No gameplay_system_prompt_date found in file. Setting gameplay_system_prompt_date to now: " + conversation_id)
                conversation_data['gameplay_system_prompt_date'] = datetime.now().isoformat()
            if 'intro_blurb_date' not in conversation_data:
                logger.warning("No intro_blurb_date found in file. Setting intro_blurb_date to now: " + conversation_id)
                conversation_data['intro_blurb_date'] = datetime.now().isoformat()
            if 'summarizer_system_prompt_date' not in conversation_data:
                logger.warning("No summarizer_system_prompt_date found in file. Setting summarizer_system_prompt_date to now: " + conversation_id)
                conversation_data['summarizer_system_prompt_date'] = datetime.now().isoformat()
            if 'intro_blurb' not in conversation_data:
                logger.warning("No intro_blurb found in file. Setting intro_blurb to default: " + conversation_id)
                conversation_data['intro_blurb'] = get_intro_blurb_string()
                conversation_data['intro_blurb_date'] = datetime.now().isoformat()
            if 'intro_blurb_date' not in conversation_data:
                logger.warning("No intro_blurb_date found in file. Setting intro_blurb_date to now: " + conversation_id)
                conversation_data['intro_blurb_date'] = datetime.now().isoformat()
            if 'game_has_begun' not in conversation_data:
                logger.warning("No game_has_begun found in file. Setting game_has_begun to False: " + conversation_id)
                conversation_data['game_has_begun'] = False
                conversation_data['game_has_begun_date'] = datetime.now().isoformat()        
            return conversation_data
    logger.warning("Game seed not found: " + conversation_id)
    return None


def write_game_seed(game_seed):
    logger.info(f"Saving game seed {game_seed['conversation_id']}")
    conversation_id = game_seed['conversation_id']
    game_seed['last_updated'] = datetime.now().isoformat()
    file_path = os.path.join(GAME_SEEDS_DIR, f"{conversation_id}.json")
    with open(file_path, 'w') as f:
        json.dump(game_seed, f, indent=2)

def delete_game_seed(conversation_id):
    file_path = os.path.join(GAME_SEEDS_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def read_all_game_seed_ids():
    conversation_ids = []
    for filename in os.listdir(GAME_SEEDS_DIR):
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
    logger.info(f"Getting LLM instructions for {name}")
    # Print the current working directory
    logger.debug(f"Current working directory: {os.getcwd()}")
    # Get the absolute path of the 'LLM_instructions' directory
    llm_instructions_dir = os.path.abspath('LLM_instructions')
    # Print the list of files in the 'LLM_instructions' directory
    logger.debug(f"Files in LLM_instructions directory: {os.listdir(llm_instructions_dir)}")
    file_path = os.path.join(llm_instructions_dir, f"{name}.MD")
    logger.debug(f"LLM instructions directory: {llm_instructions_dir}")
    with open(file_path, 'r') as f:
        logger.info(f"LLM instructions for {name} found")
        return f.read()