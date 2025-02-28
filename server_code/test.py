import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Anthropic client
client = Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

def get_claude_response(user_message, system_prompt="You are a helpful AI assistant.", temperature=0.7):
    """
    Send a message to Claude and get a response.
    
    Args:
        user_message (str): The message to send to Claude
        system_prompt (str): The system prompt to set Claude's behavior
        temperature (float): Controls randomness in the response (0.0 to 1.0)
    
    Returns:
        str: Claude's response text
    """
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        messages=[{
            "role": "assistant",
            "content": user_message
        }],
        system=system_prompt,
        temperature=temperature,
        max_tokens=1000  # Adjust this as needed
    )
    
    return response.content[0].text

def main():
    # Example usage
    system_prompt = "You are a friendly and concise AI assistant."
    
    while True:
        user_input = input("\nEnter your message (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
            
        try:
            response = get_claude_response(user_input, system_prompt)
            print("\nClaude:", response)
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
