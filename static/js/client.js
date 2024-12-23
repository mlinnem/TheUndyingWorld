// DOM Elements
const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const tokenInfo = document.getElementById('token-info');
const costInfo = document.getElementById('cost-info');
const systemPromptInput = document.getElementById('system-prompt');
const promptNameInput = document.getElementById('prompt-name');
const savedPromptsSelect = document.getElementById('saved-prompts');
const updateStatus = document.getElementById('update-status');
const newConversationBtn = document.getElementById('new-conversation-btn');
const conversationList = document.getElementById('conversation-list');
const chatTitle = document.getElementById('chat-title');

let activeConversationId = null;

// Event Listeners
sendButton.addEventListener('click', sendMessage);
newConversationBtn.addEventListener('click', startNewConversation);

userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Prevent default form submission
        sendMessage();
    }
});

// Functions
function scrollChatNearBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight - chatContainer.clientHeight - 1;
}

function turnOnErrorState(errorMessage) {

    //TODO: Work on these more.
    // Hide the send button and user input
    const sendButton = document.getElementById('send-button');
    sendButton.classList.add('hidden');
    const userInput = document.getElementById('user-input');
    userInput.classList.add('hidden');
    const tryAgainBtn = document.getElementById('try-again-btn');
    tryAgainBtn.classList.remove('hidden');
    
    const errorDiv = document.createElement('div');
    errorDiv.classList.add('message', `${sender}-message`);
    chatContainer.appendChild(errorDiv);
}

function turnOffErrorState() {
    const sendButton = document.getElementById('send-button');
    sendButton.classList.remove('hidden');
    const userInput = document.getElementById('user-input');
    userInput.classList.remove('hidden');
    const tryAgainBtn = document.getElementById('try-again-btn');
    tryAgainBtn.classList.add('hidden');
}

function sendMessage() {

    const message = userInput.value.trim();
    if (message) {
        addMessage('user', [{type: 'text', text: message}]);
        userInput.value = '';
        userInput.style.height = 'auto';

        // Add loading message
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'loading-message');
        loadingDiv.textContent = 'Thinking...';
        chatContainer.appendChild(loadingDiv);
        scrollChatNearBottom();

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                user_message: message,
            }),
        })
        .then(response => {
            loadingDiv.remove();
            return response.json();
        })
        .then(data => {
            console.log("data: ", data);
            addMessages(data.new_messages);
            
            if (data.success_type === 'partial_success') {
                let errorMessage;
                switch(data.error_type) {
                    case 'authentication_error':
                        errorMessage = 'Authentication error. Please check your API key and try again.';
                        break;
                    case 'permission_denied_error':
                        errorMessage = 'Permission denied. Please check your API key permissions.';
                        break;
                    case 'rate_limit_error':
                        errorMessage = 'Rate limit exceeded. Please wait a minute before trying again.';
                        break;
                    case 'internal_error':
                        errorMessage = 'An internal error occurred. Please try again later.';
                        break;
                    case 'unknown_error':
                        errorMessage = data.error_message || 'An unknown error occurred.';
                        break;
                    default:
                        errorMessage = 'An unexpected error occurred. Try again later.';
                        
                }

                console.log("errorMessage: ", errorMessage);
                addMessage('assistant', errorMessage);
            
            }
        })
        .catch(error => {
            loadingDiv.remove();
            console.error('Error:', error);
            addMessage('assistant', 'An unhandled error occurred. You may have better luck if you refresh this page and try again.');
        });
    }
}

function addMessages(messages) {
    for (const message of messages) {
        addMessage(message.role, message.content);
    }
}

function addMessage(sender, content) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    
    // Convert array to string if necessary
    console.log("content: ", content);
    // For now we're going to ignore tool use and tool result content
    
    let output = ""

    if (Array.isArray(content)) { 
        for (const item of content) {
            if (item.type === 'text') {
                output += item.text;
            } else if (item.type === 'tool_use') {
                output += ""
                messageDiv.classList.add('tool-use');
            } else if (item.type === 'tool_result') {
                output += item.content; //TODO: Yes indeed, content is the name of the value bearing field in a tool result
                messageDiv.classList.add('tool-result');
            } else if (item.type === 'difficulty_object') {
                output += item.difficulty_object.difficulty_analysis + " (Target: " + item.difficulty_object.difficulty_target + ")\n\n";
            } else if (item.type === 'world_reveal_object') {
                output += item.world_reveal_object.world_reveal_analysis + " (Level: " + item.world_reveal_object.world_reveal_level + ")\n\n";
            } else if (item.type === 'difficulty_and_world_reveal_object') {
                output += item.difficulty_and_world_reveal_object.difficulty.difficulty_analysis + " (Target: " + item.difficulty_and_world_reveal_object.difficulty.difficulty_target + ")\n\n";
                output += item.difficulty_and_world_reveal_object["world reveal"].world_reveal_analysis + " (Level: " + item.difficulty_and_world_reveal_object["world reveal"].world_reveal_level + ")\n\n";
            }
        }
    } else {
        console.error("content is not an array (should always be): ", content);
        output = content;
    }

    if (sender === 'assistant') {
        messageDiv.classList.add('assistant-message');
        messageDiv.innerHTML = marked.parse(output);
    } else if (sender === 'user') {
        messageDiv.classList.add('user-message');
        // For user messages, preserve whitespace
        const preElement = document.createElement('pre');
        preElement.classList.add('user-message-content');
        preElement.textContent = output;
        messageDiv.appendChild(preElement);
    } else {
        console.error("unknown sender: ", sender);
        messageDiv.classList.add(`${sender}-message`);
        messageDiv.innerHTML = marked.parse(output);
    }
    
    chatContainer.appendChild(messageDiv);
}

function updateTokenInfo(data) {
    tokenInfo.textContent = `Total Input tokens: ${data.input_tokens} | Total Output tokens: ${data.output_tokens}`;
}

function updateCostInfo(data) {
    costInfo.textContent = `Total cost: $${data.total_cost.toFixed(6)}`;
}

function startNewConversation() {
    fetch('/new_conversation', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log("data: ", data);
                loadConversation(data.conversation_id);
                updateConversationList();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatus.textContent = 'Error starting new conversation';
        });
}

function updateConversationList() {
    fetch('/list_conversations')
        .then(response => response.json())
        .then(data => {
            conversationList.innerHTML = '';
            console.log("data: ", data);
            data.conversations.forEach(conv => {
                const convDiv = document.createElement('div');
                convDiv.classList.add('conversation-item');
                console.log("conv_id: ", conv.conversation_id, "activeConversationId: ", activeConversationId);
                if (conv.conversation_id === activeConversationId) {
                    convDiv.classList.add('active');
                }
                convDiv.textContent = conv.name;
                convDiv.onclick = () => loadConversation(conv.conversation_id);
                convDiv.id = conv.conversation_id;
                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'X';
                deleteBtn.onclick = (e) => {
                    e.stopPropagation();
                    deleteConversation(conv.conversation_id);
                };
                convDiv.appendChild(deleteBtn);
                conversationList.appendChild(convDiv);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatus.textContent = 'Error loading conversations';
        });
}

function loadConversation(conversationId) {
    fetch('/set_current_conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ conversation_id: conversationId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log("data on loadConversation: ", data);
            console.log("conversationId: ", conversationId);
            activeConversationId = conversationId;
            chatContainer.innerHTML = '';
            //remove active class from all conversation items
            conversationList.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('active');
            });
            //add active class to the selected conversation
            const conversationElement = conversationList.querySelector(`#${CSS.escape(conversationId)}`);
            console.log("conversationElement: ", conversationElement);
            if (conversationElement) {
                conversationElement.classList.add('active');
            }
            chatTitle.textContent = data.conversation.name;
            data.conversation.messages.forEach(msg => {
                console.log("msg: ", msg);
                addMessage(msg.role, msg.content);
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        updateStatus.textContent = 'Error loading conversation';
    });
}

function deleteConversation(conversationId) {
    fetch('/delete_conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ conversation_id: conversationId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateConversationList();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        updateStatus.textContent = 'Error deleting conversation';
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateConversationList();
    
    // Add auto-resize functionality to the textarea
    //userInput.addEventListener('input', function() {
    //    this.style.height = 'auto';
    //    this.style.height = (this.scrollHeight) + 'px';
    //});
});