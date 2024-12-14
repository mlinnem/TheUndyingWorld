# anth.py

from anthropic import Anthropic
from config import MAX_OUTPUT_TOKENS

client = Anthropic()

def generate_response(system="", user_message="", max_tokens=MAX_OUTPUT_TOKENS, temperature=0.7):
    messages = []
    
    messages.append({
        "role": "user",
        "content": user_message
    })

    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error in generate_response: {e}")
        return f"Error: {str(e)}"

def generate_text_response(system=None, user_message=None, max_tokens=4096, temperature=0.8):
    response = generate_response(system, user_message, max_tokens, temperature)
    return response.content[0].text

def generate_json_response(system=None, user_message=None, max_tokens=4096, temperature=0.8):
    if user_message is None:
        user_message = "Please provide your response in valid JSON format."
    else:
        user_message += "\nPlease provide your response in valid JSON format."
    response = generate_response(system, user_message, max_tokens, temperature)
    try:
        json_response = json.loads(response.content[0].text)
    except json.JSONDecodeError:
        return response.content[0].text
    return json_response