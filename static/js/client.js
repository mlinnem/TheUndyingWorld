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



function sendMessage() {

    const text = userInput.value.trim();
    if (text) {
        addConversationObject({
            "type": "user_message",
            "text": text
        });
        userInput.value = '';
        userInput.style.height = 'auto';

        // Add loading message
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('co', 'loading_message', 'module', 'left');
        loadingDiv.innerHTML = body_text('Thinking...');
        chatContainer.appendChild(loadingDiv);
        scrollChatNearBottom();

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                user_message: text,
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
                    "type": "server_error",
                    "text": errorMessage
                });
            
            }
        })
        .catch(error => {
            loadingDiv.remove();
            console.error('Error:', error);
            addConversationObject({
                "type": "server_error",
                "text": "An unhandled error occurred. Refresh this page and try again."
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
    conversation_objects.forEach(conversation_object => {
        addConversationObject(conversation_object);
    });
}

function module_header(label) {
    return "<span class='module_header'>" + label + "</span>";
}

function body_text(contents) {
    return "<span class='conversation-body-text'>" + contents + "</span>";
}

function addConversationObject(co) {
    const coDiv = document.createElement('div');
    coDiv.classList.add('co');
    coDiv.classList.add('module');
    coDiv.classList.add(co.type);
    
    if (co.type === 'user_message') {
        coDiv.classList.add('right')
    } else {
        coDiv.classList.add('left');
    }

    if (co.type === 'user_message') {
        coDiv.innerHTML = body_text(marked.parse(co.text));
        coDiv.classList.add('freestanding');
    } else if (co.type === 'map_data') {
        coDiv.innerHTML = module_header("Map Data") + body_text(marked.parse(co.text));
        coDiv.classList.add('freestanding');
        coDiv.classList.add('info-text-style');
    } else if (co.type === 'ooc_message') {
        coDiv.innerHTML = body_text(marked.parse(co.text));
        coDiv.classList.add('freestanding');
    } else if (co.type === 'difficulty_analysis') {
        coDiv.innerHTML = module_header("Difficulty Analysis") + body_text(marked.parse(co.text));
        coDiv.classList.add('top');
        coDiv.classList.add('info-text-style');
    } else if (co.type === 'difficulty_target') {
        coDiv.innerHTML = module_header("Difficulty Target") +  body_text(co.integer);
        coDiv.classList.add('middle');
        coDiv.classList.add('info-text-style');
    } else if (co.type === 'world_reveal_analysis') {
        coDiv.innerHTML = module_header("World Reveal Analysis") + body_text(marked.parse(co.text));
        coDiv.classList.add('middle');
        coDiv.classList.add('info-text-style');
    } else if (co.type === 'world_reveal_level') {
        coDiv.innerHTML = module_header("World Reveal Level") + body_text(marked.parse(co.text));
        coDiv.classList.add('middle');
        coDiv.classList.add('info-text-style');
    } else if (co.type === 'difficulty_roll') {
        coDiv.innerHTML = module_header("Difficulty Roll") + body_text(co.integer);
        coDiv.classList.add('middle');
        coDiv.classList.add('info-text-style');
    } else if (co.type === 'world_reveal_roll') {
        coDiv.innerHTML = module_header("World Reveal Roll") + body_text(co.integer);
        coDiv.classList.add('middle');
        coDiv.classList.add('info-text-style');
    } else if (co.type === 'resulting_scene_description') {
        coDiv.innerHTML = body_text(marked.parse(co.text));
        const previousElement = chatContainer.lastElementChild;
        if (previousElement && 
            (previousElement.classList.contains('bottom') || 
             previousElement.classList.contains('freestanding'))) {
            coDiv.classList.add('top');
        } else {
            coDiv.classList.add('middle');
        }
    } else if (co.type === 'tracked_operations') {
        coDiv.innerHTML = module_header("Tracked Operations") + body_text(marked.parse(co.text));
        coDiv.classList.add('middle');
        coDiv.classList.add('info-text-style');
    } else if (co.type === 'condition_table') {
        coDiv.innerHTML = module_header("Character Condition") + body_text(marked.parse(co.text));
        coDiv.classList.add('bottom');
        coDiv.classList.add('info-text-style');
    } else if (co.type === 'out_of_section_text') {
        coDiv.innerHTML = body_text(marked.parse(co.text));
        coDiv.classList.add('freestanding');
    } else if (co.type === 'unrecognized_section') {
        coDiv.innerHTML = module_header(co.header_text) + body_text(marked.parse(co.body_text));
        coDiv.classList.add('freestanding');
    } else if (co.type === 'server_error') {
        coDiv.innerHTML = body_text(marked.parse(co.text));
        coDiv.classList.add('freestanding');
        coDiv.classList.add('info-text-style');
        console.error("server error: ", co.text);
    } else {
        console.error("unknown conversation object type: ", co.type);
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
            addConversationObjects(data.new_conversation_objects);
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