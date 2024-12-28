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
        addConversationObject({
            "source": "client",
            "type": "user_message",
            "user_message": message
        });
        userInput.value = '';
        userInput.style.height = 'auto';

        // Add loading message
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'loading-message', 'module', 'left');
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
            console.log("data:", JSON.stringify(data, null, 2));
            addConversationObjects(data.new_conversation_objects);
            
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
                addConversationObject({
                    "source": "client",
                    "type": "error",
                    "error_message": errorMessage,
                    "original_message": data.original_message
                });
            
            }
        })
        .catch(error => {
            loadingDiv.remove();
            console.error('Error:', error);
            addConversationObject({
                "source": "client",
                "type": "error",
                "error_message": "An unhandled error occurred. You may have better luck if you refresh this page and try again.",
            });
        });
    }
}

function render_difficulty_and_world_reveal_object(difficulty_and_world_reveal_object) {   

    rendered_world_reveal_object = difficulty_and_world_reveal_object.difficulty.difficulty_analysis + "\n\n" + difficulty_and_world_reveal_object["world reveal"].world_reveal_analysis + "\n\n";
    rendered_world_reveal_object += "Difficulty Target: " + difficulty_and_world_reveal_object.difficulty.difficulty_target + "\n\n" + "World Reveal Level: " + difficulty_and_world_reveal_object["world reveal"].world_reveal_level + "\n\n";
    //rendered_world_reveal_object = difficulty_and_world_reveal_object.difficulty.difficulty_analysis + " (Target: " + difficulty_and_world_reveal_object.difficulty.difficulty_target + ")\n\n";
    //rendered_world_reveal_object += difficulty_and_world_reveal_object["world reveal"].world_reveal_analysis + " (Level: " + difficulty_and_world_reveal_object["world reveal"].world_reveal_level + ")\n\n";
    return rendered_world_reveal_object;
}

function addConversationObjects(conversation_objects) {
    for (const conversation_object of conversation_objects) {
        addConversationObject(conversation_object);
    }
}

function module_header(label) {
    return "<span class='module_header'>" + label + "</span>";
}

function conversation_body_text(contents) {
    return "<span class='conversation-body-text'>" + contents + "</span>";
}

function addConversationObject(conversation_object) {
    const coDiv = document.createElement('div');
    coDiv.classList.add('conversation-object');
    coDiv.classList.add(conversation_object.type);
    coDiv.classList.add('module');
    
    // Add handling for error messages
    if (conversation_object.type === 'error') {
        coDiv.innerHTML = conversation_body_text(marked.parse(conversation_object.error_message) + "\n\n<pre>" + JSON.stringify(conversation_object.original_message, null, 2) + "</pre>");
        coDiv.classList.add('error-message');
        coDiv.classList.add('left');
    } else if (conversation_object.type === 'user_message') {
        coDiv.innerHTML = conversation_body_text(marked.parse(conversation_object.user_message));
        coDiv.classList.add('right');
    } else if (conversation_object.type === 'difficulty_analysis') {
        coDiv.innerHTML = conversation_body_text(marked.parse(conversation_object.difficulty_analysis));
        coDiv.classList.add('left');
    } else if (conversation_object.type === 'world_analysis') {
        coDiv.innerHTML = conversation_body_text(marked.parse(conversation_object.world_analysis));
        coDiv.classList.add('left');
    } else if (conversation_object.type === 'world_roll') {
        coDiv.innerHTML = conversation_body_text(marked.parse(conversation_object.world_roll));
        coDiv.classList.add('left');
    } else if (conversation_object.type === 'difficulty_roll') {
        coDiv.innerHTML = conversation_body_text(marked.parse(conversation_object.difficulty_roll));
        coDiv.classList.add('left');
    } else if (conversation_object.type === 'resulting_scene_description') {
        coDiv.innerHTML = conversation_body_text(marked.parse(conversation_object.resulting_scene_description));
        coDiv.classList.add('left');
    } else if (conversation_object.type === 'tracked_operations') {
        coDiv.innerHTML = conversation_body_text(marked.parse(conversation_object.tracked_operations));
        coDiv.classList.add('left');
    } else if (conversation_object.type === 'condition_table') {
        coDiv.innerHTML = conversation_body_text(marked.parse(conversation_object.condition_table));
        coDiv.classList.add('left');
    } else if (conversation_object.type === 'map_data') {
        coDiv.innerHTML = module_header("Map Data") + conversation_body_text(marked.parse(conversation_object.map_data));
        coDiv.classList.add('left');
    } else if (conversation_object.type === 'ooc_message') {
        coDiv.innerHTML = conversation_body_text(marked.parse(conversation_object.ooc_message));
        coDiv.classList.add('left');
    } else {
        console.error("unknown conversation object type: ", conversation_object.type);
    }

    chatContainer.appendChild(coDiv);
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
            chatTitle.textContent = data.conversation_name;
            data.new_conversation_objects.forEach(msg => {
                console.log("msg: ", msg);
                addConversationObject(msg);
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