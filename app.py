from flask import Flask, render_template, request, jsonify, session
import anth
import os
from prompt_routes import prompt_routes
from conversation_routes import conversation_routes
from conversation_utils import save_conversation, load_conversation, generate_conversation_id
from config import MAX_CONTEXT_TOKENS, MAX_OUTPUT_TOKENS, CACHE_POINT_TRIGGER_TOKEN_COUNT
from utils import calculate_cost
from datetime import datetime
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from dotenv import load_dotenv
from random import randint
import logging
import http.client as http_client
import json
import secrets

load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')

client = Anthropic(
    api_key=api_key
)

app = Flask(__name__, template_folder='templates')
app.secret_key = secrets.token_hex(16)
app.register_blueprint(prompt_routes)
app.register_blueprint(conversation_routes)

# SET UP INITIAL PROMPTS

manual_instructions =  ""
with open('instructions.MD', 'r') as file:
    manual_instructions = file.read()

tools = []
with open('tools.json', 'r') as file:
    tools = json.load(file)


zombie_system_prompt = [{
        "type": "text",
        "text": manual_instructions,
        "cache_control": {"type": "ephemeral"}
}]


message_index_for_message_with_cache_point = 0    


MAX_HISTORY_TOKENS = 150000

def roll_die():
    return randint(1, 100)


def clean_cache_point(conversation, message_index_for_message_with_cache_point):
    for i, message in enumerate(conversation['messages']):
        # Skip first 20 messages
        if i < 20:
            continue
            
        content_block_to_clean = message['content'][0]
        print(f"content_block_to_clean (before): {content_block_to_clean}")

        if content_block_to_clean['type'] == "text":
            content_block_to_clean = {
                "type": "text",
                "text": content_block_to_clean['text']
                #no cache control
            }
        elif content_block_to_clean['type'] == "tool_use":
            content_block_to_clean = {
                "type": "tool_use",
                "id": content_block_to_clean['id'],
                "name": content_block_to_clean['name'],
                "input": content_block_to_clean['input']
                #no cache control
            }
        elif content_block_to_clean['type'] == "tool_result":
            content_block_to_clean = {
                "type": "tool_result",
                "tool_use_id": content_block_to_clean['tool_use_id'],
                "content": content_block_to_clean['content']
                #no cache control
            }
        else:
            raise Exception(f"Unknown message type: {content_block_to_clean['type']}")
    
        conversation['messages'][i]['content'][0] = content_block_to_clean
        print(f"content_block_to_clean (after): {content_block_to_clean}")

    return conversation

def inject_cache_point(conversation, message_index_for_message_with_cache_point):

    content_block_to_add_cache_point = conversation['messages'][message_index_for_message_with_cache_point]['content'][0]
    print(f"content_block_to_add_cache_point (before): {content_block_to_add_cache_point}")

    if content_block_to_add_cache_point['type'] == "text":
        content_block_to_add_cache_point = {
            "type": "text",
            "text": content_block_to_add_cache_point['text'],
            "cache_control": {"type": "ephemeral"}
                }
    elif content_block_to_add_cache_point['type'] == "tool_use":
        content_block_to_add_cache_point = {
            "type": "tool_use",
            "id": content_block_to_add_cache_point['id'],
            "name": content_block_to_add_cache_point['name'],
            "input": content_block_to_add_cache_point['input'],
            "cache_control": {"type": "ephemeral"}
        }
    elif content_block_to_add_cache_point['type'] == "tool_result":
        content_block_to_add_cache_point = {
            "type": "tool_result",
            "tool_use_id": content_block_to_add_cache_point['tool_use_id'],
            "content": content_block_to_add_cache_point['content'],
            "cache_control": {"type": "ephemeral"}
        }
    else:
        raise Exception(f"Unknown message type: {content_block_to_add_cache_point['type']}")
    
    conversation['messages'][message_index_for_message_with_cache_point]['content'][0] = content_block_to_add_cache_point
    print(f"content_block_to_add_cache_point (after): {content_block_to_add_cache_point}")
    return conversation

def handle_caching_and_summarization(conversation, response, message_index_for_message_with_cache_point):
    
        # handle usage bookkeeping
        print(f"response.usage: {response.usage}")

        output_tokens = response.usage.output_tokens
        cache_read_input_tokens = response.usage.cache_read_input_tokens
        uncached_input_tokens = response.usage.input_tokens
        cache_creation_input_tokens = response.usage.cache_creation_input_tokens
        context_window_utilization = uncached_input_tokens + cache_read_input_tokens + cache_creation_input_tokens
        cache_creation_input_tokens = response.usage.cache_creation_input_tokens
        print(f"cache_creation_input_tokens: {cache_creation_input_tokens}")
        
        print(f"cache_read_input_tokens: {cache_read_input_tokens}")

        # Handle updating cache point
        
        if (uncached_input_tokens > CACHE_POINT_TRIGGER_TOKEN_COUNT):
            print("Triggered cache point adding and removing")

            # clean existing cache point if it exists
            conversation = clean_cache_point(conversation, message_index_for_message_with_cache_point)
           
            # update cache point index to current message
            print(f"cache point before update: {message_index_for_message_with_cache_point}")
            message_index_for_message_with_cache_point = len(conversation['messages']) - 1
            print(f"cache point after update: {message_index_for_message_with_cache_point}")

            # (re) inject cache point    
            conversation = inject_cache_point(conversation, message_index_for_message_with_cache_point)
    
        # handle summarization

        if context_window_utilization >= MAX_HISTORY_TOKENS:  # Only summarize if we have enough messages
            
            print("Summarizing conversation...")

            

            quarter_point = len(conversation['messages']) // 4
            
            # Skip first 20 messages and take the rest up to halfway point
            messages_to_summarize = conversation['messages'][20:quarter_point] # will return empty list if quarter_point is less than 20
            last_three_quarters_of_messages = conversation['messages'][quarter_point:]
            
            if len(messages_to_summarize) > 0:
                # clean existing cache point if it exists
                conversation = clean_cache_point(conversation, message_index_for_message_with_cache_point)
                message_index_for_message_with_cache_point = 0

                # Generate summary of first half of messages
                print(f"first_half_of_messages: {messages_to_summarize}")
                summary = generate_summary(messages_to_summarize)
                print(f"summary: {summary}")
                
                if summary:
                    # Replace summarized messages with the summary
                    conversation['messages'] = [{
                        "role": "assistant",
                    "content": [{
                        "type": "text",
                        "text": f"[SUMMARY OF PREVIOUS CONVERSATION]\n\n{summary}\n\n[END SUMMARY]"
                    }]
                }] + last_three_quarters_of_messages
            else:
                print("No messages to summarize")
            
            # Reset the cache point index since we've modified the message history
            

        return conversation, message_index_for_message_with_cache_point

def generate_summary(messages):
    """Generate a summary of a sequence of messages using Claude."""
    
    # Load summarizer instructions from file
    with open('summarizer_instructions.MD', 'r') as file:
        summarizer_instructions = file.read()
    
    # Prepare the messages for summarization

    formatted_messages = "\n\n".join([
        f"{msg['role'].upper()}: {msg['content'][0]['text'] if isinstance(msg['content'], list) else msg['content']}"
        for msg in messages
    ])

    system_prompt = [{
        "type": "text",
        "text": summarizer_instructions
    }]
    
    try:
        response = client.beta.prompt_caching.messages.create(
            model="claude-3-5-sonnet-20241022",
            tools = tools,
            messages=[{
                "role": "user",
                "content": [{"type": "text", "text": f":{formatted_messages}"}]
            }],
            system=system_prompt,
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.35,
        )
        
        return response.content[0].text
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global message_index_for_message_with_cache_point, zombie_system_prompt
    
    data = request.get_json()
    user_message = data['user_message']
    max_tokens = min(int(data.get('max_tokens', MAX_CONTEXT_TOKENS)), MAX_CONTEXT_TOKENS)

    if 'current_conversation_id' not in session:
        conversation_id = generate_conversation_id()
        session['current_conversation_id'] = conversation_id
        conversation = {
            'messages': [],
            'last_updated': datetime.now().isoformat(),
            'name': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        total_input_tokens = 0
        total_output_tokens = 0
    else:
        conversation, total_input_tokens, total_output_tokens = load_conversation(session['current_conversation_id'])
        
        if conversation is None:
            conversation_id = generate_conversation_id()
            session['current_conversation_id'] = conversation_id
            conversation = {
                'messages': [],
                'last_updated': datetime.now().isoformat(),
                'name': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            total_input_tokens = 0
            total_output_tokens = 0

    # add user message to conversation
    user_message_json = {
        "role": "user",
        "content": [{"type": "text", "text": user_message}]
    }
    conversation['messages'].append(user_message_json)
    print(f"user_message_json: {user_message_json}")
    
    # handle sending message to GM and handling GM response

    additional_conversation_elements = []

    try:
        # Send user message to the GM

        print("sending message to GM...")

        response = client.beta.prompt_caching.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=conversation['messages'],
            system=zombie_system_prompt,  
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.7,
            tools = tools,
        )

        # check if response is a tool use request or not
        print(f"response: {response}")

        print("checking if response is a tool use request...")

        if len(response.content) > 1 and response.content[1].type == "tool_use":
            #response is a tool use request
            print("response is a tool use request")

            response_json = {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": response.content[0].text},
                    {"type": "tool_use", "id": response.content[1].id, "name": response.content[1].name, "input": {}}
                ]
            }
            print(f"response_json: {response_json}")
            conversation['messages'].append(response_json)
            additional_conversation_elements.append(response_json)
            

            # execute tool

            tool_use_id = response.content[1].id
            function = response.content[1].name

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

            print(f"roll_string: {roll_string}")

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
            print(f"tool_result: {tool_result}")
            conversation['messages'].append(tool_result)
            additional_conversation_elements.append(tool_result)

            # send tool result to GM

            print("sending tool result to GM...")

            response = client.beta.prompt_caching.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=conversation['messages'],
            system=zombie_system_prompt, 
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.7,
            tools = tools,
            )

            print(f"response: {response}")

            # add GM response to conversation
            response_json = {
                "role": "assistant",
                "content": [{"type": "text", "text": response.content[0].text}]
            }
            print(f"response_json: {response_json}")
            conversation['messages'].append(response_json)
            additional_conversation_elements.append(response_json)

        else:
            # response wasn't a tool use request
            print("response wasn't a tool use request")
            response_json = {
                "role": "assistant",
                "content": [{"type": "text", "text": response.content[0].text}]
            }
            print(f"response_json: {response_json}")
            conversation['messages'].append(response_json)
            additional_conversation_elements.append(response_json)
        
    
    except Exception as e:
        print(f"Error generating response: {e}")
        return jsonify({'error': str(e)}), 500
    
    
     
    conversation, message_index_for_message_with_cache_point = handle_caching_and_summarization(conversation, response, message_index_for_message_with_cache_point)
    
    # Generate conversation name if it's a new conversation

    conversation['last_updated'] = datetime.now().isoformat()
    log_conversation_messages(conversation['messages'])
    save_conversation(session['current_conversation_id'], conversation, total_input_tokens, total_output_tokens)

    return jsonify({
        'conversation_id': session['current_conversation_id'],
        'conversation_name': conversation['name'],
        'response': additional_conversation_elements,
        'input_tokens': 0,
        'output_tokens': 0,
        'total_cost': 0
    })

@app.route('/set_current_conversation', methods=['POST'])
def set_current_conversation():
    data = request.get_json()
    conversation_id = data['conversation_id']
    conversation, input_tokens, output_tokens = load_conversation(conversation_id)
    if conversation:
        session['current_conversation_id'] = conversation_id
        total_cost = calculate_cost(input_tokens, output_tokens)
        print(f"conversation: {conversation}")
        return jsonify({
            'status': 'success', 
            'conversation': conversation, 
            'input_tokens': input_tokens, 
            'output_tokens': output_tokens,
            'total_cost': total_cost
        })
    else:
        return jsonify({'status': 'error', 'message': 'Conversation not found'}), 404

@app.route('/system_prompt', methods=['GET', 'POST'])
def system_prompt():
    if request.method == 'POST':
        data = request.get_json()
        app.config['current_system_prompt'] = data['system_prompt']
        print(f"System prompt updated to: {app.config['current_system_prompt']}")  # Debug print
        return jsonify({'status': 'system prompt updated'})
    else:
        return jsonify({'system_prompt': app.config['current_system_prompt']})

def log_conversation_messages(messages):
    """Log conversation messages to a file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_dir = "conversation_logs"
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_file = os.path.join(log_dir, "conversation_logs.txt")
    
    with open(log_file, "a", encoding='utf-8') as f:
        f.write(f"\n\n=== Conversation Log {timestamp} ===\n")
        for msg in messages:
            role = msg['role']
            
            # Handle different message content types
            if isinstance(msg['content'], list):
                # Process each content item
                for content_item in msg['content']:
                    if content_item['type'] == 'text':
                        f.write(f"\n{role.upper()}: {content_item['text']}\n")
                    elif content_item['type'] == 'tool_use':
                        f.write(f"\n{role.upper()} TOOL REQUEST: {content_item['name']}\n")
                    elif content_item['type'] == 'tool_result':
                        f.write(f"\n{role.upper()} TOOL RESULT: {content_item['content']}\n")
            else:
                # Handle legacy format
                f.write(f"\n{role.upper()}: {msg['content']}\n")
                
        f.write("\n" + "="*50)

if __name__ == '__main__':
    app.run(debug=True)