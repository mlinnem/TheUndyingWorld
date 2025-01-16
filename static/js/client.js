// Import all exports from client_util.js with a wildcard
import * as util from './client_util.js';

// DOM Elements
const chatContainer = document.getElementById('chat-container');
const chatMessagesWrapper = document.getElementById('chat-messages-wrapper');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const updateStatus = document.getElementById('update-status');
const newConversationBtn = document.getElementById('new-conversation-btn');
const conversationList = document.getElementById('conversation-list');
const chatTitle = document.getElementById('chat-title');

let activeConversationId = localStorage.getItem('activeConversationId') || null;
let conversationObjectCounts = {};

// Event Listeners
sendButton.addEventListener('click', sendMessage);
newConversationBtn.addEventListener('click', startNewConversation);

userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Prevent default form submission
        sendMessage();
    }
});

userInput.addEventListener('input', function() {
    if (this.scrollHeight > this.clientHeight) {
        // Only adjust height if content exceeds current height
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
    }
});

// Functions


function sendMessage() {
    console.info("sending message for conversation: ", activeConversationId);

    if (!activeConversationId) {
        addConversationObject({
            "type": "server_error",
            "text": "No active conversation. Please start a new conversation first."
        });
        return;
    }

    const text = userInput.value.trim();
    if (text) {
        // Check for boot sequence command
        if (text === "run_boot_sequence") {
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    user_message: text,
                    run_boot_sequence: true
                }),
            })
            .then(response => response.json())
            .then(data => {
                console.info("received boot sequence data");
                addConversationObjects(data.new_conversation_objects);
            })
            .catch(error => {
                console.error('Error:', error);
                if (error.stack) {
                    console.error('Stack trace:', error.stack);
                }
                addConversationObject({
                    "type": "server_error",
                    "text": "An error occurred during boot sequence. Please try again."
                });
            });
            userInput.value = '';
            userInput.style.height = '60px';
            return;
        }

        // Regular message handling
        conversationObjectCounts[activeConversationId] = (conversationObjectCounts[activeConversationId] || 0) + 1;
        updateConversationList();
        
        addConversationObject({
            "type": "user_message",
            "text": text
        });
        userInput.value = '';
        userInput.style.height = '60px';

        // Add loading message with animated dots
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('co', 'loading_message', 'module', 'left', 'primary-text-style');
        const loadingText = document.createElement('div');
        loadingText.classList.add('module_contents', 'has_contents');
        loadingText.innerHTML = util.body_text('Thinking');
        const dots = document.createElement('span');
        dots.textContent = '...';
        loadingText.querySelector('.conversation-body-text').appendChild(dots);
        loadingDiv.appendChild(loadingText);
        chatMessagesWrapper.appendChild(loadingDiv);
        
        // Animate the dots
        let dotCount = 3;
        const dotAnimation = setInterval(() => {
            dots.textContent = '.'.repeat(dotCount);
            dotCount = (dotCount % 3) + 1;
        }, 500);

        scrollChatNearBottom();

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                user_message: text,
                conversation_id: activeConversationId
            }),
        })
        .then(response => response.json())
        .then(data => {
            clearInterval(dotAnimation);
            loadingDiv.remove();
            console.info("received data");
            console.info("adding " + (data.new_conversation_objects.length) + " conversation objects");
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
            clearInterval(dotAnimation);
            loadingDiv.remove();
            console.error('Error:', error);
            if (error.stack) {
                console.error('Stack trace:', error.stack);
            }
            addConversationObject({
                "type": "server_error",
                "text": "An unhandled error occurred. Refresh this page and try again."
            });
        });
    }
}

function get_or_create_prescene() {
    const previousElement = chatMessagesWrapper.lastElementChild;
    if (previousElement && previousElement.classList.contains('pre_scene')) {
        return previousElement;
    } else {
        const analysisDiv = document.createElement('div');
        analysisDiv.classList.add('co','module','pre_scene', 'left', 'top');
        chatMessagesWrapper.appendChild(analysisDiv);
        return analysisDiv;
    }
}




function addConversationObjects(conversation_objects) {
    conversation_objects.forEach(conversation_object => {
        addConversationObject(conversation_object);
    });
}

function addConversationObject(co) {
    let coDiv;
    let color;  // Used in difficulty_roll and world_reveal_roll cases

    if (co.type === 'user_message') {
        console.debug("adding user message");
        coDiv = util.make_module(co);
        util.inject_content_into_element(coDiv, '.module_contents', util.body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding');
        coDiv.classList.add('primary-text-style');
        coDiv.classList.add('right')
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'map_data') {
        console.debug("adding map data");
        coDiv = util.make_module(co);
        util.inject_content_into_element(coDiv, '.module_contents', util.header("Map Data") + util.body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding', 'info-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'ooc_message') {
        console.debug("adding ooc message");
        coDiv = util.make_module(co);
        util.inject_content_into_element(coDiv, '.module_contents', util.body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding' , 'primary-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'difficulty_analysis') {
        console.debug("adding difficulty analysis");
        const presceneDiv = get_or_create_prescene();
        const difficultyElement = util.get_or_create_difficulty_element(presceneDiv);
        util.inject_content_into_element(difficultyElement, '.difficulty_analysis', util.body_text(marked.parse(co.text)));
    } else if (co.type === 'difficulty_target') {
        console.debug("adding difficulty target");
        const presceneDiv = get_or_create_prescene();
        const difficultyElement = util.get_or_create_difficulty_element(presceneDiv);
        util.inject_content_into_element(difficultyElement, '.difficulty_target', util.header("Target") + util.data_text(co.text));
    } else if (co.type === 'world_reveal_analysis') {
        console.debug("adding world reveal analysis");
        const presceneDiv = get_or_create_prescene();
        const worldRevealElement = util.get_or_create_world_reveal_element(presceneDiv);
        util.inject_content_into_element(worldRevealElement, '.world_reveal_analysis', util.body_text(marked.parse(co.text)));
    } else if (co.type === 'world_reveal_level') {
        console.debug("adding world reveal level");
        const presceneDiv = get_or_create_prescene();
        const worldRevealElement = util.get_or_create_world_reveal_element(presceneDiv);
        util.inject_content_into_element(worldRevealElement, '.world_reveal_level', util.header("Level") + util.data_text(co.text));
    } else if (co.type === 'difficulty_roll') {
        console.debug("adding difficulty roll");
        const presceneDiv = get_or_create_prescene();
        const difficultyElement = util.get_or_create_difficulty_element(presceneDiv);
        color = util.determine_difficulty_color(difficultyElement, co.integer);
        difficultyElement.style.backgroundColor = color;
        util.inject_content_into_element(difficultyElement, '.difficulty_roll', util.header("Roll") + util.data_text(co.integer.toString()));
    } else if (co.type === 'world_reveal_roll') {
        console.debug("adding world reveal roll");
        const presceneDiv = get_or_create_prescene();
        const worldRevealElement = util.get_or_create_world_reveal_element(presceneDiv);
        color = util.determine_world_reveal_color(worldRevealElement, co.integer);
        worldRevealElement.style.backgroundColor = color;
        util.inject_content_into_element(worldRevealElement, '.world_reveal_roll', util.header("Roll") + util.data_text(co.integer.toString()));
    } else if (co.type === 'resulting_scene_description') {
        console.debug("adding resulting scene description");
        coDiv = util.make_module(co);
        util.inject_content_into_element(coDiv, '.module_contents', util.body_text(marked.parse(co.text)));
        const previousElement = chatMessagesWrapper.lastElementChild;
        if (previousElement && 
            (previousElement.classList.contains('bottom') || 
             previousElement.classList.contains('freestanding') ||
             previousElement.classList.contains('right'))) {
            coDiv.classList.add('top');
        } else {
            coDiv.classList.add('middle');
        }
        coDiv.classList.add('primary-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'tracked_operations') {
        console.debug("adding tracked operations");
        coDiv = util.make_module(co);
        util.inject_content_into_element(coDiv, '.module_contents', util.header("Tracked Operations") + util.body_text(marked.parse(co.text)));
        coDiv.classList.add('middle', 'info-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'condition_table') {
        console.debug("adding condition table");
        coDiv = util.make_module(co);
        util.inject_content_into_element(coDiv, '.module_contents', util.header("Character Condition") + util.body_text(marked.parse(co.text)));
        coDiv.classList.add('bottom', 'info-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'tool_use') {
        console.debug("ignoring tool use"); 
        return;
    } else if (co.type === 'out_of_section_text') {
        console.debug("adding out of section text");
        coDiv = util.make_module(co);
        util.inject_content_into_element(coDiv, '.module_contents', util.body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding', "left");
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'unrecognized_section') {
        console.debug("adding unrecognized section");
        coDiv = util.make_module(co);
        util.inject_content_into_element(coDiv, '.module_contents', util.header(co.header_text) + util.body_text(marked.parse(co.body_text)));
        coDiv.classList.add('freestanding', 'primary-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'server_error') {
        console.debug("adding server error");
        coDiv = util.make_module(co);
        util.inject_content_into_element(coDiv, '.module_contents', util.body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding', 'info-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
        console.error("server error: ", co.text);
    } else {
        console.error("unknown conversation object type: ", co.type);
    }
}

function startNewConversation() {
    console.log("starting new conversation");
    fetch('/create_conversation', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log("New conversation response:", data);  // Debug log
            if (data.status === 'success') {
                console.log("New conversation data:", data);  // Debug log
                activeConversationId = data.conversation_id;
                localStorage.setItem('activeConversationId', data.conversation_id);
                chatMessagesWrapper.innerHTML = '';
                
                // Store the count of conversation objects
                conversationObjectCounts[data.conversation_id] = data.new_conversation_objects.length;
                console.log("New conversation objects:", data.new_conversation_objects);  // Debug log
                
                // Format the chat title
                const date = new Date(data.conversation_name);
                const formattedDate = date.toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                });
                chatTitle.textContent = "Game created on " + formattedDate;
                
                // Display the intro message
                console.log("new_conversation_objects: ", data.new_conversation_objects);
                addConversationObjects(data.new_conversation_objects);
                updateConversationList();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (error.stack) {
                console.error('Stack trace:', error.stack);
            }
            updateStatus.textContent = 'Error starting new conversation';
        });
}

function updateConversationList() {
    console.log("updating conversation list");
    fetch('/list_conversations')
        .then(response => response.json())
        .then(data => {
            conversationList.innerHTML = '';
            
            // Sort conversations by last_updated timestamp, message count, and creation date
            const sortedConversations = data.conversations.sort((a, b) => {
                // If neither has last_updated, compare message counts
                if (!a.last_updated && !b.last_updated) {
                    const countA = conversationObjectCounts[a.conversation_id] || 0;
                    const countB = conversationObjectCounts[b.conversation_id] || 0;
                    if (countA !== countB) {
                        return countB - countA; // Higher message count first
                    }
                    // If message counts are equal, sort by creation date
                    return new Date(b.name) - new Date(a.name);
                }
                
                // If only one has last_updated, put the updated one first
                if (!a.last_updated) return 1;
                if (!b.last_updated) return -1;
                
                // If both have last_updated, normal date comparison
                return new Date(b.last_updated) - new Date(a.last_updated);
            });

            sortedConversations.forEach(conv => {
                const convDiv = document.createElement('div');
                convDiv.classList.add('conversation-item');
                if (conv.conversation_id === activeConversationId) {
                    convDiv.classList.add('active');
                }
                const span = document.createElement('span');
                span.classList.add('conversation-item-text');
                
                const date = new Date(conv.name);
                const formattedDate = date.toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                });
                
                // Add object count on a new line
                const objectCount = conversationObjectCounts[conv.conversation_id] || 0;
                if (objectCount > 0) {
                    span.innerHTML = `${formattedDate}<br>${objectCount} messages`;
                } else {
                    span.innerHTML = `${formattedDate}`;
                }
                
                convDiv.appendChild(span);
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
            if (error.stack) {
                console.error('Stack trace:', error.stack);
            }
            updateStatus.textContent = 'Error loading conversations';
        });
}

function loadConversation(conversationId) {
    console.log("loading conversation: ", conversationId);
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
            console.log("data received from loading conversation: ", data);
            activeConversationId = conversationId;
            localStorage.setItem('activeConversationId', conversationId);
            chatMessagesWrapper.innerHTML = '';
            
            // Store the count of conversation objects
            conversationObjectCounts[conversationId] = data.new_conversation_objects.length;
            updateConversationList(); // Update the list to show new count
            
            //remove active class from all conversation items
            conversationList.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('active');
            });
            //add active class to the selected conversation
            const conversationElement = conversationList.querySelector(`#${CSS.escape(conversationId)}`);
            if (conversationElement) {
                conversationElement.classList.add('active');
            }
            
            // Format the chat title using the same date formatting
            const date_created = new Date(data.conversation_name);
            const formattedDate_created = date_created.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
            
            const date_updated = new Date(data.last_updated);
            const formattedDate_updated = date_updated.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
            
            console.log("formattedDate_created: ", data.conversation_name);
            console.log("formattedDate_updated: ", data.last_updated);


            chatTitle.textContent = "Game created on " + formattedDate_created + " (last updated " + formattedDate_updated + ")";
            
            addConversationObjects(data.new_conversation_objects);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (error.stack) {
            console.error('Stack trace:', error.stack);
        }
        updateStatus.textContent = 'Error loading conversation';
    });
}

function deleteConversation(conversationId) {
    if (!confirm('Are you sure you want to delete this conversation? This cannot be undone.')) {
        return;
    }

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
            if (conversationId === activeConversationId) {
                localStorage.removeItem('activeConversationId');
                activeConversationId = null;
                chatMessagesWrapper.innerHTML = '';
                chatTitle.textContent = 'Current World';
            }
            updateConversationList();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (error.stack) {
            console.error('Stack trace:', error.stack);
        }
        updateStatus.textContent = 'Error deleting conversation';
    });
}

function scrollChatNearBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight - chatContainer.clientHeight - 250;
}

// Initialize

document.addEventListener('DOMContentLoaded', () => {
    updateConversationList();
    userInput.focus();
    
    // Load the active conversation if one exists
    const savedConversationId = localStorage.getItem('activeConversationId');
    if (savedConversationId) {
        // First check if the conversation exists in the list
        fetch('/list_conversations')
            .then(response => response.json())
            .then(data => {
                const conversationExists = data.conversations.some(
                    conv => conv.conversation_id === savedConversationId
                );
                if (conversationExists) {
                    loadConversation(savedConversationId);
                } else {
                    // If conversation doesn't exist, clear storage and start fresh
                    localStorage.removeItem('activeConversationId');
                    activeConversationId = null;
                }
            })
            .catch(error => {
                console.error('Error checking conversation existence:', error);
                // On error, clear storage to be safe
                localStorage.removeItem('activeConversationId');
                activeConversationId = null;
            });
    }
});