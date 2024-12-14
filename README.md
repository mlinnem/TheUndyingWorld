# Simple Claude Chat

Simple Claude Chat is a lightweight, single-user, local chat application for interacting with Claude 3.5 Sonnet, an AI language model by Anthropic. This project provides a basic foundation for developers who want to build their own Claude-powered chat applications.

## Features

- Web-based interface for chatting with Claude 3.5 Sonnet
- Configurable chat history to control API costs
- Customizable system prompts with save/load functionality
- Multiple conversation support
- Token usage and cost tracking

## Prerequisites

- Python 3.7+
- Flask
- Anthropic API key

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/fox4snce/simple-claude-chat.git
   cd simple-claude-chat
   ```

2. Install the required dependencies:
   ```
   pip install flask anthropic
   ```

3. Set your Anthropic API key as an environment variable:
   ```
   export ANTHROPIC_API_KEY='your_api_key_here'
   ```

## Usage

1. Run the Flask application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to `http://localhost:5000`

3. Start chatting with Claude!

## Customization

- Modify the system prompt in the web interface to change Claude's behavior
- Adjust the max tokens in the UI to control the length of the conversation history
- Edit the CSS files in the `static/css` directory to customize the appearance

## Contributing

This project is meant to be a simple starting point for developers to build their own Claude-powered chat applications. Feel free to fork, modify, and share your improvements.  I will not be taking pull requests, feature requests, bug reports etc.  For a more feature-full chat client, visit https://github.com/fox4snce/bitbrainchat.git.

## Disclaimer

This is a basic implementation and may lack features found in more robust chat applications. Use it as a learning tool or a foundation for building more complex systems.

## License

This project is open-source and available under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

**Note**: This project is not officially affiliated with or endorsed by Anthropic. Use of the Claude API is subject to Anthropic's terms of service.
