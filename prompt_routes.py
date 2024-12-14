from flask import Blueprint, request, jsonify, current_app
import json
from datetime import datetime

prompt_routes = Blueprint('prompt_routes', __name__)

PROMPTS_FILE = "prompts.json"

def load_prompts():
    try:
        with open(PROMPTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_prompts(prompts):
    with open(PROMPTS_FILE, 'w') as f:
        json.dump(prompts, f, indent=2)



@prompt_routes.route('/save_prompt', methods=['POST'])
def save_prompt():
    data = request.get_json()
    name = data['name']
    prompt = data['prompt']
    prompts = load_prompts()
    prompts[name] = {
        'content': prompt,
        'created_at': datetime.now().isoformat()
    }
    save_prompts(prompts)
    return jsonify({'status': 'prompt saved'})

@prompt_routes.route('/load_prompt', methods=['POST'])
def load_prompt():
    data = request.get_json()
    name = data['name']
    prompts = load_prompts()
    if name in prompts:
        prompt_content = prompts[name]['content']
        # Update the global current_system_prompt
        current_app.config['current_system_prompt'] = prompt_content
        return jsonify({'status': 'prompt loaded', 'prompt': prompt_content})
    else:
        return jsonify({'status': 'prompt not found'}, 404)

@prompt_routes.route('/delete_prompt', methods=['POST'])
def delete_prompt():
    data = request.get_json()
    name = data['name']
    prompts = load_prompts()
    if name in prompts:
        del prompts[name]
        save_prompts(prompts)
        return jsonify({'status': 'prompt deleted'})
    else:
        return jsonify({'status': 'prompt not found'}, 404)

@prompt_routes.route('/list_prompts', methods=['GET'])
def list_prompts():
    prompts = load_prompts()
    return jsonify({'prompts': list(prompts.keys())})