import logging
from random import randint
from flask import Flask, render_template, request, jsonify, session

logger = logging.getLogger(__name__)


def isToolUseRequest(response_json):
    return (len(response_json['content']) > 1 and 
            'type' in response_json['content'][1] and 
            response_json['content'][1]['type'] == "tool_use")
def generate_tool_result(gm_response_json):
    logger.info(f"Generating tool result for {gm_response_json}")

    tool_use_id = gm_response_json['content'][1]['id']
    function = gm_response_json['content'][1]['name']

    if function == "roll_skill_and_world_reveal":
        skill_roll, fate_roll = roll_die(), roll_die()
        roll_string = f"* Skill roll: {skill_roll}\n\n * World roll: {fate_roll}.\n\n"
    elif function == "roll_skill_only":
        skill_roll = roll_die()
        roll_string = f"Skill roll: {skill_roll}."
    elif function == "roll_world_reveal_only":
        world_reveal_roll = roll_die()
        roll_string = f"World reveal roll: {world_reveal_roll}."
    else:
        roll_string = "No valid tool use found."


            # add tool result to conversation

    tool_result = {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": roll_string
            }
        ]
    }

    return tool_result

def roll_die():
    return randint(1, 100)
