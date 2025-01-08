// DOM Elements
const chatContainer = document.getElementById('chat-container');
const chatMessagesWrapper = document.getElementById('chat-messages-wrapper');
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

let activeConversationId = localStorage.getItem('activeConversationId') || null;

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
    chatContainer.scrollTop = chatContainer.scrollHeight - chatContainer.clientHeight - 250;
}



function sendMessage() {
    console.info("sending message");

    const text = userInput.value.trim();
    if (text) {
        addConversationObject({
            "type": "user_message",
            "text": text
        });
        userInput.value = '';
        userInput.style.height = 'auto';

        // Add loading message with animated dots
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('co', 'loading_message', 'module', 'left', 'primary-text-style');
        const loadingText = document.createElement('div');
        loadingText.classList.add('module_contents', 'has_contents');
        loadingText.innerHTML = body_text('Thinking');
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
            }),
        })
        .then(response => {
            return response.json();
        })
        .then(data => {
            clearInterval(dotAnimation); // Stop the animation
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
            loadingDiv.remove();
        })
        .catch(error => {
            clearInterval(dotAnimation); // Add this line
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

function header(label) {
    return "<span class='header'>" + label + "</span>";
}

function body_text(contents) {
    return "<div class='conversation-body-text'>" + contents + "</div>";
}

function data_text(contents) {
    return "<div class='conversation-data-text info-text-style'>" + contents + "</div>";
}

function make_module(co) {
    const coDiv = document.createElement('div');
    coDiv.classList.add('co');
    coDiv.classList.add('module');
    coDiv.classList.add(co.type);
    coDiv.innerHTML = "<div class='module_contents no_contents'></div>";
    return coDiv;
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

function get_or_create_difficulty_element(analysisDiv) {
    const difficultyElement = analysisDiv.querySelector('.difficulty_element');
    if (difficultyElement) {
        return difficultyElement;
    } else {
        const difficultyElement = document.createElement('div');
        difficultyElement.classList.add('difficulty_element', 'prescene_contents');
        difficultyElement.innerHTML = header("Difficulty") + "<div class='difficulty_analysis info-text-style no_contents'></div><div class='prescene_footer'><span class='difficulty_target info-text-style no_contents'></span><span class='difficulty_roll info-text-style no_contents'></span></div>";
        analysisDiv.appendChild(difficultyElement); //TODO: Should probable be injecting so order doesn't matter
        return difficultyElement;
    }
}

function get_or_create_world_reveal_element(analysisDiv) {
    const difficultyElement = analysisDiv.querySelector('.world_reveal_element');
    if (difficultyElement) {
        return difficultyElement;
    } else {
        const difficultyElement = document.createElement('div');
        difficultyElement.classList.add('world_reveal_element', 'prescene_contents');
        difficultyElement.innerHTML = header("World Reveal") + "<div class='world_reveal_analysis info-text-style no_contents'></div><div class='prescene_footer'><span class='world_reveal_level info-text-style no_contents'></span><span class='world_reveal_roll info-text-style no_contents'></span></div>";
        analysisDiv.appendChild(difficultyElement);
        return difficultyElement;
    }
}

function determine_difficulty_color(difficultyElement,rolledValue) {
    const targetElement = difficultyElement.querySelector('.difficulty_target');
        const targetText = targetElement ? targetElement.textContent.replace('Target', '').trim() : null;
        if (!isNaN(parseInt(targetText))) {
            console.debug("targetText is a number");
            targetValue = parseInt(targetText);
            if (rolledValue >= targetValue) {
                degreeOfSuccess = (rolledValue - targetValue) / (100 - targetValue);
                l = degreeOfSuccess * 43;
                return 'hsl(140,' + l + '%, 10%)';
            } else {
                degreeOfFailure = (targetValue - rolledValue) / targetValue;
                l = degreeOfFailure * 43;
                return 'hsl(359,' + l + '%, 10%)';
            }
        } else {
            console.debug("targetText is not a number");
            return 'hsl(180, 43%, 10%)';
        }
}

function determine_world_reveal_color(worldRevealElement, rolledValue) {
    console.debug("determining world reveal color");
    console.debug("rolledValue: ", rolledValue);
    console.debug("worldRevealElement: ", worldRevealElement);
    const targetElement = worldRevealElement.querySelector('.world_reveal_level');
    const targetText = targetElement ? targetElement.textContent.replace('Level', '').trim() : null;
    targetValue = targetText;
    console.debug("targetValue: ", targetValue);
        if (targetValue.toLowerCase().trim() === "n/a") {
            return 'hsl(0, 0%, 10%)';
        } else if (targetValue.toLowerCase().trim() === "light") {
            if (rolledValue >= 95) {
                console.debug("light success");
                return 'hsl(140, 21%, 10%)';
            } else if (rolledValue <= 5) {
                console.debug("light failure");
                return 'hsl(359, 21%, 10%)';
            } else {
                console.debug("light neutral");
                return 'hsl(0, 0%, 10%)';  
            }
        } else if (targetValue.toLowerCase().trim() === "moderate") {
            if (rolledValue >= 66) {
                degreeOfSuccess = (rolledValue - 66) / (100 - 66);
                l = degreeOfSuccess * 43;
                console.debug("l in moderate success: ", l);
                return 'hsl(140,' + l + '%, 10%)';
            } else if (rolledValue <= 33) {
                degreeOfFailure = (66 - rolledValue) / 66;
                console.debug("degreeOfFailure: ", degreeOfFailure);
                l = degreeOfFailure * 43;
                console.debug("l in moderate failure: ", l);
                return 'hsl(359,' + l + '%, 10%)';
            } else {
                return 'hsl(0, 0%, 10%)';
            }
        } else if (targetValue.toLowerCase().trim() === "strong") {
            if (rolledValue > 50) {
                degreeOfSuccess = (rolledValue - 50) / (100 - 50);
                l = degreeOfSuccess * 43;
                console.debug("l in strong success: ", l);
                return 'hsl(140,' + l + '%, 10%)';
            } else if (rolledValue < 50) {
                degreeOfFailure = (50 - rolledValue) / 50;
                l = degreeOfFailure * 43;
                console.debug("l in strong failure: ", l);
                return 'hsl(359,' + l + '%, 10%)';
            }
        }
}

function addConversationObject(co) {

    if (co.type === 'user_message') {
        console.debug("adding user message");
        coDiv = make_module(co);
        inject_content_into_element(coDiv, '.module_contents', body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding');
        coDiv.classList.add('primary-text-style');
        coDiv.classList.add('right')
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'map_data') {
        console.debug("adding map data");
        coDiv = make_module(co);
        inject_content_into_element(coDiv, '.module_contents', header("Map Data") + body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding', 'info-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'ooc_message') {
        console.debug("adding ooc message");
        coDiv = make_module(co);
        inject_content_into_element(coDiv, '.module_contents', body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding' , 'primary-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'difficulty_analysis') {
        console.debug("adding difficulty analysis");
        const presceneDiv = get_or_create_prescene();
        const difficultyElement = get_or_create_difficulty_element(presceneDiv);
        inject_content_into_element(difficultyElement, '.difficulty_analysis', body_text(marked.parse(co.text)));
    } else if (co.type === 'difficulty_target') {
        console.debug("adding difficulty target");
        const presceneDiv = get_or_create_prescene();
        const difficultyElement = get_or_create_difficulty_element(presceneDiv);
        inject_content_into_element(difficultyElement, '.difficulty_target', header("Target") + data_text(co.text));
    } else if (co.type === 'world_reveal_analysis') {
        console.debug("adding world reveal analysis");
        const presceneDiv = get_or_create_prescene();
        const worldRevealElement = get_or_create_world_reveal_element(presceneDiv);
        inject_content_into_element(worldRevealElement, '.world_reveal_analysis', body_text(marked.parse(co.text)));
    } else if (co.type === 'world_reveal_level') {
        console.debug("adding world reveal level");
        const presceneDiv = get_or_create_prescene();
        const worldRevealElement = get_or_create_world_reveal_element(presceneDiv);
        inject_content_into_element(worldRevealElement, '.world_reveal_level', header("Level") + data_text(co.text));
    } else if (co.type === 'difficulty_roll') {
        console.debug("adding difficulty roll");
        const presceneDiv = get_or_create_prescene();
        const difficultyElement = get_or_create_difficulty_element(presceneDiv);
        color = determine_difficulty_color(difficultyElement,co.integer);
        difficultyElement.style.backgroundColor = color;
        inject_content_into_element(difficultyElement, '.difficulty_roll', header("Roll") + data_text(co.integer.toString()));
    } else if (co.type === 'world_reveal_roll') {
        console.debug("adding world reveal roll");
        const presceneDiv = get_or_create_prescene();
        const worldRevealElement = get_or_create_world_reveal_element(presceneDiv);
        color = determine_world_reveal_color(worldRevealElement,co.integer);
        worldRevealElement.style.backgroundColor = color;
        inject_content_into_element(worldRevealElement, '.world_reveal_roll', header("Roll") + data_text(co.integer.toString()));
    } else if (co.type === 'resulting_scene_description') {
        console.debug("adding resulting scene description");
        coDiv = make_module(co);
        inject_content_into_element(coDiv, '.module_contents', body_text(marked.parse(co.text)));
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
        coDiv = make_module(co);
        inject_content_into_element(coDiv, '.module_contents', header("Tracked Operations") + body_text(marked.parse(co.text)));
        coDiv.classList.add('middle', 'info-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'condition_table') {
        console.debug("adding condition table");
        coDiv = make_module(co);
        inject_content_into_element(coDiv, '.module_contents', header("Character Condition") + body_text(marked.parse(co.text)));
        coDiv.classList.add('bottom', 'info-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'out_of_section_text') {
        console.debug("adding out of section text");
        coDiv = make_module(co);
        inject_content_into_element(coDiv, '.module_contents', body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding', "left");
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'unrecognized_section') {
        console.debug("adding unrecognized section");
        coDiv = make_module(co);
        inject_content_into_element(coDiv, '.module_contents', header(co.header_text) + body_text(marked.parse(co.body_text)));
        coDiv.classList.add('freestanding', 'primary-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'server_error') {
        console.debug("adding server error");
        coDiv = make_module(co);
        inject_content_into_element(coDiv, '.module_contents', body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding', 'info-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
        console.error("server error: ", co.text);
    } else {
        console.error("unknown conversation object type: ", co.type);
    }
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
                loadConversation(data.conversation_id);
                updateConversationList();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            console.error('Error starting new conversation:', error);
            if (error.stack) {
                console.error('Stack trace:', error.stack);
            }
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
                const span = document.createElement('span');
                span.classList.add('conversation-item-text');
                
                // Format the date to show only month, day, hour, and minutes
                const date = new Date(conv.name);
                const formattedDate = date.toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                });
                
                span.innerHTML = formattedDate;
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
            localStorage.setItem('activeConversationId', conversationId);
            chatMessagesWrapper.innerHTML = '';
            //remove active class from all conversation items
            conversationList.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('active');
            });
            //add active class to the selected conversation
            const conversationElement = conversationList.querySelector(`#${CSS.escape(conversationId)}`);
            if (conversationElement) {
                conversationElement.classList.add('active');
            }
            chatTitle.textContent = data.conversation_name;
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
                chatTitle.textContent = 'Current Campaign';
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

function inject_content_into_element(element, content_container_class, content) {
    let contentContainer = element.querySelector(content_container_class);
    contentContainer.innerHTML = content;
    contentContainer.classList.add('has_contents');
    contentContainer.classList.remove('no_contents');
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    updateConversationList();
    userInput.focus();
    
    // Load the active conversation if one exists
    if (activeConversationId) {
        loadConversation(activeConversationId);
    }
});