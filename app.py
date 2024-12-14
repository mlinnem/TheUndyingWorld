from flask import Flask, render_template, request, jsonify
import anth
import os
from prompt_routes import prompt_routes
from conversation_routes import conversation_routes
from conversation_utils import save_conversation, load_conversation, generate_conversation_id
from config import MAX_CONTEXT_TOKENS, MAX_OUTPUT_TOKENS
from utils import calculate_cost
from datetime import datetime
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from dotenv import load_dotenv
from random import randint
import logging
import http.client as http_client

load_dotenv()
api_key = os.getenv('ANTHROPIC_API_KEY')

client = Anthropic(
    api_key=api_key
)

#Set up HTTP request logging
http_client.HTTPConnection.debuglevel = 1

#Configure logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

app = Flask(__name__, template_folder='templates')
app.register_blueprint(prompt_routes)
app.register_blueprint(conversation_routes)

current_conversation_id = None

manual_instructions =  ""
with open('instructions.MD', 'r') as file:
    manual_instructions = file.read()

message_index_for_message_with_cache_point = 0    

zombie_system_prompt = [{
        "type": "text",
        "text": manual_instructions,
        "cache_control": {"type": "ephemeral"}
}]


def roll_two_dice():
    return randint(1, 100), randint(1, 100)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    global current_system_prompt, current_conversation_id, message_index_for_message_with_cache_point, zombie_system_prompt
    
    data = request.get_json()
    user_message = data['user_message']
    max_tokens = min(int(data.get('max_tokens', MAX_CONTEXT_TOKENS)), MAX_CONTEXT_TOKENS)

    if current_conversation_id is None:
        current_conversation_id = generate_conversation_id()
        conversation = {
            'name': 'New Conversation',
            'messages': [],
            'last_updated': datetime.now().isoformat()
        }
        total_input_tokens = 0
        total_output_tokens = 0
 
    else:
        conversation, total_input_tokens, total_output_tokens = load_conversation(current_conversation_id)
        if conversation is None:
            # If the loaded conversation is None, create a new one
            current_conversation_id = generate_conversation_id()
            conversation = {
                'name': 'New Conversation',
                'messages': [],
                'last_updated': datetime.now().isoformat()
            }
            total_input_tokens = 0
            total_output_tokens = 0


    dice_rolls = roll_two_dice()
    roll_string = f"Skill roll: {dice_rolls[0]}. Fate roll: {dice_rolls[1]}."
    user_message_with_rolls = user_message + "\n\n" + roll_string
    conversation['messages'].append({"role": "user", "content": [{"type": "text", "text": user_message_with_rolls}]})
    
    full_message = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation['messages']])
   
    # Count tokens only after messages are populated

    # clean cache point if it exists
    message_to_clean = conversation['messages'][message_index_for_message_with_cache_point]
    message_to_clean['content'] = [
        {
        "type": "text",
        "text": message_to_clean['content'][0]['text'],
        }
    ]

    uncached_input_tokens = client.beta.messages.count_tokens(messages=conversation['messages'][message_index_for_message_with_cache_point:], model="claude-3-5-sonnet-20241022").input_tokens

    if (uncached_input_tokens > 5000):
        print("Triggered cache point adding and removing")
        message_index_for_message_with_cache_point = len(conversation['messages']) - 1


    print(f"message_index_for_message_with_cache_point: {message_index_for_message_with_cache_point}")
    # (re) inject cache point    
    current_message = conversation['messages'][message_index_for_message_with_cache_point]
    current_message['content'][0] = {
        "type": "text",
        "text": current_message['content'][0]['text'],
        "cache_control": {"type": "ephemeral"}
    }
    
    try:
        # Use the Messages API to generate response with system parameter
        response = client.beta.prompt_caching.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=conversation['messages'],
            system=zombie_system_prompt,  # Call the function and get the system prompt value
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.7,
        )
        #print(f"response: {response}")

        
        
        response_text = roll_string + "\n\n" + response.content[0].text

        #print("We workin boyzzz!")

        print(f"response.usage: {response.usage}")

        output_tokens = response.usage.output_tokens
        input_tokens = response.usage.input_tokens
        cache_creation_input_tokens = response.usage.cache_creation_input_tokens
        print(f"cache_creation_input_tokens: {cache_creation_input_tokens}")
        cache_read_input_tokens = response.usage.cache_read_input_tokens
        print(f"cache_read_input_tokens: {cache_read_input_tokens}")

    except Exception as e:
        print(f"Error generating response: {e}")
        return jsonify({'error': str(e)}), 500

    total_input_tokens += input_tokens
    total_output_tokens += output_tokens

    conversation['messages'].append({"role": "assistant", "content": response_text})
    conversation['last_updated'] = datetime.now().isoformat()

    # Generate conversation name if it's a new conversation
    if conversation['name'] == 'New Conversation':
        name_prompt = f"""Based on the following conversation, suggest an extremely short (1-5 words) but descriptive name for it. The name should capture the essence of the conversation.

        RETURN ONLY the name without punctuation or intermediate steps.

    Examples:
    Conversation: "How do I bake chocolate chip cookies from scratch?"
    Name: "Baking Chocolate Chip Cookies"

    Conversation: "What are the best places to visit in Paris for a first-time traveler?"
    Name: "Paris Travel Tips"

    Conversation: "Can you explain the basics of quantum computing?"
    Name: "Quantum Computing Basics"

    Now, here's the conversation to name:

    {full_message}

    Suggested name:"""

        conversation_name = anth.generate_response(
            system="You are an expert at creating concise, relevant titles for conversations. Your task is to generate extremely short (1-5 words) but descriptive names based on the conversation content. Focus on the main topic or theme.",
            user_message=name_prompt,
            max_tokens=10,
            temperature=0.5
        ).strip()
        conversation['name'] = conversation_name

    save_conversation(current_conversation_id, conversation, total_input_tokens, total_output_tokens)

    total_cost = calculate_cost(total_input_tokens, total_output_tokens)

    return jsonify({
        'conversation_id': current_conversation_id,
        'conversation_name': conversation['name'],
        'response': response_text,
        'input_tokens': total_input_tokens,
        'output_tokens': total_output_tokens,
        'total_cost': total_cost
    })

@app.route('/set_current_conversation', methods=['POST'])
def set_current_conversation():
    global current_conversation_id
    data = request.get_json()
    conversation_id = data['conversation_id']
    conversation, input_tokens, output_tokens = load_conversation(conversation_id)
    if conversation:
        current_conversation_id = conversation_id
        total_cost = calculate_cost(input_tokens, output_tokens)
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

if __name__ == '__main__':
    app.run(debug=True)