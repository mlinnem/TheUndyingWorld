// DOM Elements
const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const maxTokensInput = document.getElementById('max-tokens');
const tokenInfo = document.getElementById('token-info');
const costInfo = document.getElementById('cost-info');
const systemPromptInput = document.getElementById('system-prompt');
const updateSystemPromptButton = document.getElementById('update-system-prompt');
const promptNameInput = document.getElementById('prompt-name');
const savePromptButton = document.getElementById('save-prompt');
const loadPromptButton = document.getElementById('load-prompt');
const deletePromptButton = document.getElementById('delete-prompt');
const savedPromptsSelect = document.getElementById('saved-prompts');
const updateStatus = document.getElementById('update-status');
const newConversationBtn = document.getElementById('new-conversation-btn');
const conversationList = document.getElementById('conversation-list');
const chatTitle = document.getElementById('chat-title');

let activeConversationId = null;

// Event Listeners
sendButton.addEventListener('click', sendMessage);
updateSystemPromptButton.addEventListener('click', updateSystemPrompt);
savePromptButton.addEventListener('click', savePrompt);
loadPromptButton.addEventListener('click', loadPrompt);
deletePromptButton.addEventListener('click', deletePrompt);
newConversationBtn.addEventListener('click', startNewConversation);

userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Prevent default form submission
        sendMessage();
    }
});

// Functions
function sendMessage() {
    const message = userInput.value.trim();
    const maxTokens = maxTokensInput.value;
    if (message) {
        addMessage('user', message);
        userInput.value = '';
        userInput.style.height = 'auto'; // Reset height

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
        .then(response => response.json())
        .then(data => {
            for (const item of data.response) {
                if (item.role === 'assistant') {
                    addMessage('assistant', item.content);
                } else {
                    addMessage('user', item.content);
                }
            }
            updateTokenInfo(data);
            updateCostInfo(data);
            updateConversationList();
        })
        .catch(error => {
            console.error('Error:', error);
            addMessage('assistant', 'An error occurred. Please try again.');
        });
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
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function updateTokenInfo(data) {
    tokenInfo.textContent = `Total Input tokens: ${data.input_tokens} | Total Output tokens: ${data.output_tokens}`;
}

function updateCostInfo(data) {
    costInfo.textContent = `Total cost: $${data.total_cost.toFixed(6)}`;
}

function updateSystemPrompt() {
    const systemPrompt = systemPromptInput.value;
    fetch('/system_prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ system_prompt: systemPrompt }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'system prompt updated') {
            updateStatus.textContent = 'System prompt updated successfully';
            setTimeout(() => {
                updateStatus.textContent = '';
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        updateStatus.textContent = 'Error updating system prompt';
    });
}

function savePrompt() {
    const name = promptNameInput.value.trim();
    const prompt = systemPromptInput.value.trim();
    if (name && prompt) {
        fetch('/save_prompt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: name, prompt: prompt }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'prompt saved') {
                updateStatus.textContent = 'Prompt saved successfully';
                loadSavedPrompts();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatus.textContent = 'Error saving prompt';
        });
    } else {
        updateStatus.textContent = 'Please enter both a name and a prompt';
    }
}

function loadPrompt() {
    const name = savedPromptsSelect.value;
    if (name) {
        fetch('/load_prompt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: name }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'prompt loaded') {
                systemPromptInput.value = data.prompt;
                updateStatus.textContent = 'Prompt loaded successfully';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatus.textContent = 'Error loading prompt';
        });
    } else {
        updateStatus.textContent = 'Please select a prompt to load';
    }
}

function deletePrompt() {
    const name = savedPromptsSelect.value;
    if (name) {
        fetch('/delete_prompt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: name }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'prompt deleted') {
                updateStatus.textContent = 'Prompt deleted successfully';
                loadSavedPrompts();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatus.textContent = 'Error deleting prompt';
        });
    } else {
        updateStatus.textContent = 'Please select a prompt to delete';
    }
}

function loadSavedPrompts() {
    fetch('/list_prompts')
        .then(response => response.json())
        .then(data => {
            savedPromptsSelect.innerHTML = '';
            data.prompts.forEach(prompt => {
                const option = document.createElement('option');
                option.value = prompt;
                option.textContent = prompt;
                savedPromptsSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatus.textContent = 'Error loading saved prompts';
        });
}

function startNewConversation() {
    fetch('/new_conversation', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
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
                if (conv.id === activeConversationId) {
                    convDiv.classList.add('active');
                }
                convDiv.textContent = conv.name;
                convDiv.onclick = () => loadConversation(conv.id);
                convDiv.id = conv.id;
                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'X';
                deleteBtn.onclick = (e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
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
            updateTokenInfo(data);
            updateCostInfo(data);
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
    loadSavedPrompts();
    updateConversationList();
    
    // Add auto-resize functionality to the textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
});