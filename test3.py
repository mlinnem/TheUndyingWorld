import anthropic
from random import randint
client = anthropic.Anthropic()

def roll_die():
    return randint(1, 100)


messages = [{"role": "user", "content": "Evaluate the following scene: I am attempting to juggle two rocks. The difficulty target is 50. The fate level is mundane."}]
tools = [
    {
        "name": "roll_skill_and_fate",
        "description": "A function that obtains the results of a skill roll and a fate roll. This function should be called AFTER the difficulty target and fate level has been established. It should be called BEFORE the resulting scene is described. Each die can have a result of 1-100. The result will be in the form of 'Skill roll: 42. Fate roll: 78.'",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    }
]

response = client.beta.prompt_caching.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=,
    tools = tools,
    messages=messages
)

print("response: ", response)



response_content = response.content
print("response_content: ", response_content)

# Add assistant's response as a properly formatted message
messages.append({"role": "assistant", "content": response_content})

if len(response_content) > 1 and response_content[1].type == "tool_use":
    tool_use_id = response_content[1].id
    function = response_content[1].name

    if function == "roll_skill_and_fate":
        skill_roll, fate_roll = roll_die(), roll_die()
        roll_string = f"* Skill roll: {skill_roll}\n\n * Fate roll: {fate_roll}.\n\n"
    elif function == "roll_skill_only":
        skill_roll = roll_die()
        roll_string = f"Skill roll: {skill_roll}."
    elif function == "roll_world_reveal_only":
        world_reveal_roll = roll_die()
        world_reveal_roll_string = f"World reveal roll: {world_reveal_roll}."


    print(f"roll_string: {roll_string}")
        
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
    messages.append(tool_result)
    print(f"messages: {messages}")

    response = client.beta.prompt_caching.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=MAX_OUTPUT_TOKENS,
        tools = tools,
        messages=messages
    )

    print("response2: ", response)



