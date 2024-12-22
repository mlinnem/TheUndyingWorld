from flask import jsonify

def format_user_message(user_message):
    return {
        "role": "user",
        "content": [{
            "type": "text",
            "text": user_message
        }]
    }

def format_partial_success_response(message):
    return jsonify({
            'success_type': 'partial_success',
            'error_type': 'unknown_error',
            'error_message': str(e),
            'conversation_id': session['current_conversation_id'],
            'conversation_name': conversation['name'],
            'new_messages': new_messages,
    })