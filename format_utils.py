def format_user_message(user_message):
    return {
        "role": "user",
        "content": [{
            "type": "text",
            "text": user_message
        }]
    }