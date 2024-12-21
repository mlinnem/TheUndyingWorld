// DOM Elements
const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const maxTokensInput = document.getElementById('max-tokens');
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

function sendMessage() {
    const message = userInput.value.trim();
    const maxTokens = maxTokensInput.value;
    if (message) {
        addMessage('user', message);
        userInput.value = '';
        userInput.style.height = 'auto';

        // Add loading message
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'loading-message');
        loadingDiv.textContent = 'Thinking...';
        chatContainer.appendChild(loadingDiv);
        scrollChatNearBottom(); // Keep this scroll as it's after user input

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                user_message: message,
                max_tokens: maxTokens
            }),
        })
        .then(response => {
            // Remove loading message
            loadingDiv.remove();
            
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw errorData;
                });
            }
            return response.json();
        })
        .then(data => {
            addMessages(data.new_messages);
            if (data.success_type === 'partial_success') {
                if (data.error_type === 'unknown_error') {
                    addMessage('assistant', data.error_message);
                }
            } 
        })
        .catch(error => {
            // Remove loading message if still present
            loadingDiv.remove();
            
            console.error('Error:', error);
            let errorMessage = 'An unhandled error occurred. You may have better luck if you refresh this page and try again.';
            
            addMessage('assistant', errorMessage);
        });
    }
}

function addMessages(messages) {
    for (const message of messages) {
        addMessage(message.role, message.content);
    }
}

function addMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    
    // Convert array to string if necessary
    console.log("text: ", text);
    // For now we're going to ignore tool use and tool result content
    
    let content = ""

    if (Array.isArray(text)) { 
        for (const item of text) {
            if (item.type === 'text') {
                content += item.text;
            } else if (item.type === 'tool_use') {
                content += "" //Don't note tool use for now
            } else if (item.type === 'tool_result') {
                content += item.content;
                messageDiv.classList.add('tool-result');
            } else {
                console.log("unknown item type: ", item);
            }
        }
    } else {
        content = text;
    }
    
    console.log("sender: ", sender, "content: ", content);
    
    console.log("sender: ", sender, "content: ", content);
    if (sender === 'assistant') {
        messageDiv.innerHTML = marked.parse(content);
    } else {
        // For user messages, preserve whitespace
        const preElement = document.createElement('pre');
        preElement.classList.add('user-message-content');
        preElement.textContent = content;
        messageDiv.appendChild(preElement);
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
            data.conversations.forEach(conv => {
                const convDiv = document.createElement('div');
                convDiv.classList.add('conversation-item');
                if (conv.conversation_id === activeConversationId) {
                    convDiv.classList.add('active');
                }
                convDiv.textContent = conv.name;
                convDiv.onclick = () => loadConversation(conv.conversation_id);
                convDiv.conversation_id = conv.conversation_id;
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
            activeConversationId = conversationId;
            chatContainer.innerHTML = '';
            //remove active class from all conversation items
            conversationList.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('active');
            });
            //add active class to the selected conversation
            const conversationElement = conversationList.querySelector(`#${CSS.escape(conversationId)}`);
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
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
});