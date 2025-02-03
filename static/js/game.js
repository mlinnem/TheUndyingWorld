// Import all exports from client_util.js with a wildcard
import * as util from './game_util.js';

// DOM Elements
const chatContainer = document.getElementById('chat-container');
const chatMessagesWrapper = document.getElementById('chat-messages-wrapper');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const chatTitle = document.getElementById('chat-title');
const inputContainer = document.getElementsByClassName('input-container')[0]; //TODO: unjank this

// Add event listener for begin game button
const beginGameButton = document.getElementById('begin-game-button');

// Get the conversation ID from the window object (set in game.html)
const activeConversationId = window.conversationId;

// Event Listeners
sendButton.addEventListener('click', sendMessage);

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

// Add these variables at the top level, with the other declarations
let dotAnimation;
let loadingDiv;

function get_or_create_difficulty_check_element() {


    const previousElement = chatMessagesWrapper.lastElementChild;
    if (previousElement && previousElement.classList.contains('difficulty_check')) {
        return previousElement;
    } else {

        //This is jank, lol

        // Breadth first (ish)
    
        const difficultyCheckModule = document.createElement('div');
        difficultyCheckModule.classList.add('co','module','difficulty_check', 'left', 'top');
        
        const moduleContents = document.createElement('div');
        moduleContents.classList.add('module_contents', 'has_contents');
        difficultyCheckModule.appendChild(moduleContents);

        const headerContents = document.createElement('div');
        headerContents.classList.add('difficulty_check_contents');
        moduleContents.appendChild(headerContents);

        const bodyContents = document.createElement('div');
        bodyContents.classList.add('difficulty_analysis_contents', 'hidden');
        moduleContents.appendChild(bodyContents);

        const header = document.createElement('span');
        header.classList.add('header');
        header.textContent = "Difficulty Check";
        header.style = "white-space: nowrap;";
        headerContents.appendChild(header);

        const difficultyBar = document.createElement('div');
        difficultyBar.classList.add('difficulty-bar');
        headerContents.appendChild(difficultyBar);

        const difficultyRoll = document.createElement('span');
        difficultyRoll.classList.add('difficulty-roll');
        difficultyRoll.textContent = "";
        headerContents.appendChild(difficultyRoll);

        const separator = document.createElement('span');
        separator.classList.add('separator', 'info-text-style');
        separator.textContent = "-";
        headerContents.appendChild(separator);

        const difficultyTarget = document.createElement('span');
        difficultyTarget.classList.add('difficulty-target');
        difficultyTarget.textContent = "Trivial";
        headerContents.appendChild(difficultyTarget);

        const expandCollapseCaratBox = document.createElement('div');
        expandCollapseCaratBox.classList.add('expand-collapse-carat-box');
        headerContents.append(expandCollapseCaratBox);

        const difficultyBarFilled = document.createElement('div');
        difficultyBarFilled.classList.add('difficulty-bar-filled');
        difficultyBar.appendChild(difficultyBarFilled);

        const targetMarker = document.createElement('div');
        targetMarker.classList.add('target-marker');
        difficultyBar.appendChild(targetMarker);

        const expandCollapseCaratImg = document.createElement('img');
        expandCollapseCaratImg.src = '/static/images/MagPlus.svg';
        expandCollapseCaratImg.classList.add('expand-collapse-carat');
        expandCollapseCaratBox.appendChild(expandCollapseCaratImg);

        expandCollapseCaratBox.addEventListener('click', function() {
            const img = this.querySelector('.expand-collapse-carat');
            const contents = this.closest('.difficulty_check_contents');
            
            if (img.src.includes('MagPlus.svg')) {
                img.src = '/static/images/MagMinus.svg';
                bodyContents.classList.remove('hidden');
            } else {
                img.src = '/static/images/MagPlus.svg';
                bodyContents.classList.add('hidden');
            }
        });

        // Add analysis text container (initially hidden)
        const analysisText = document.createElement('div');
        analysisText.classList.add('analysis-text', 'info-text-style');
        bodyContents.appendChild(analysisText);

        chatMessagesWrapper.appendChild(difficultyCheckModule);
        
        return difficultyCheckModule;
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
    } else if (co.type === 'intro_blurb') {
        console.debug("adding intro blurb");
        coDiv = util.make_module(co);
        util.inject_content_into_element(coDiv, '.module_contents', util.body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding', 'primary-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'map_data' || co.type === 'world_gen_data')  {
        console.debug("adding world gen data");
        coDiv = util.make_module(co);
        util.inject_content_into_element(coDiv, '.module_contents', util.header("World Gen Data") + util.body_text(marked.parse(co.text)));
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
        const difficultyCheckElement = get_or_create_difficulty_check_element();
        const analysisText = difficultyCheckElement.querySelector('.analysis-text');
        if (analysisText) {
            analysisText.innerHTML = marked.parse(co.text);
        }

    } else if (co.type === 'difficulty_target') {
        console.debug("adding difficulty target");
        const difficultyCheckElement = get_or_create_difficulty_check_element();
        if (co.text === "Trivial") {
            util.inject_style_into_element(difficultyCheckElement, '.separator', `display: none;`);
            util.inject_style_into_element(difficultyCheckElement, '.difficulty-roll', `display: none;`);
            util.inject_content_into_element(difficultyCheckElement, '.difficulty-target', util.info_text("Trivial Success"));
            util.inject_style_into_element(difficultyCheckElement, '.difficulty-bar-filled', `background-color: hsl(180, 42%, 18%); width: 100%;`);
            util.inject_style_into_element(difficultyCheckElement, '.difficulty-target', `margin: 0px;`);
            const analysisText = difficultyCheckElement.querySelector('.analysis-text');
            if (analysisText && analysisText.innerHTML) {
                analysisText.innerHTML += "\n\nThus your action is a success.";
            }
        } else {
            util.inject_style_into_element(difficultyCheckElement, '.difficulty-bar', `width: 100%;`);
            util.inject_style_into_element(difficultyCheckElement, '.target-marker', `left: ${co.text}%; display: block;`);
            util.inject_content_into_element(difficultyCheckElement, '.difficulty-target', util.info_text(co.text));
        }
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
        const difficultyCheckElement = get_or_create_difficulty_check_element();
        color = util.determine_difficulty_color(difficultyCheckElement, co.integer);
        util.inject_style_into_element(difficultyCheckElement, '.difficulty-bar', `width: 100%;`);
        if (co.integer == 1 || co.integer == 2) {
            util.inject_style_into_element(difficultyCheckElement, '.difficulty-bar-filled', `width: ${co.integer}%; background-color: ${color}; box-shadow: 0 0 4px 2px hsla(0, 60%, 50%, 0.25);`);
        } else if (co.integer == 99 || co.integer == 100) {
            util.inject_style_into_element(difficultyCheckElement, '.difficulty-bar-filled', `width: ${co.integer}%; background-color: ${color}; box-shadow: 0 0 4px 2px hsla(180, 100%, 35%, 0.25);`);
        } else {
            util.inject_style_into_element(difficultyCheckElement, '.difficulty-bar-filled', `width: ${co.integer}%; background-color: ${color};`);
        }

        util.inject_content_into_element(difficultyCheckElement, '.difficulty-roll', util.info_text(co.integer.toString()));

         //disable the box shadow if the target is within 4 points of the roll, because it makes it hard to see if you're under or over.
         const targetElement = difficultyCheckElement.querySelector('.difficulty-target');
         const targetText = targetElement ? targetElement.textContent.replace('Target', '').trim() : null;
         
         if (!isNaN(parseInt(targetText))) {
             const targetValue = parseInt(targetText);
             if (Math.abs(targetValue - co.integer) <= 6) {
                 util.append_style_to_element(difficultyCheckElement, '.target-marker', 'box-shadow: none;');
             }

             // Adding text to analysis text to completely explain what's up. This is jank though.
             const analysisText = difficultyCheckElement.querySelector('.analysis-text');
             // Huge hack to make the text sit below the difficulty bar with right distance.

             if (analysisText) {
                 analysisText.innerHTML = analysisText.innerHTML + `\n\n You rolled a ${co.integer} on a 100-sided die, `;
                 if (co.integer == targetValue) {
                     analysisText.innerHTML = analysisText.innerHTML + `hitting the difficulty target of ${targetText} exactly, which is (barely) a success.`;
                 } else if (co.integer > targetValue) {
                    let degreeOfSuccess = (co.integer - targetValue) / (100 - targetValue);
                    if (degreeOfSuccess < 0.1) {
                        analysisText.innerHTML = analysisText.innerHTML + `barely exceeding the difficulty target of ${targetText}, resulting in a mild success.`;
                    } else if (degreeOfSuccess < 0.8) {
                        analysisText.innerHTML = analysisText.innerHTML + `exceeding the difficulty target of ${targetText}, resulting in a success.`;
                    } else { // Mega success
                        analysisText.innerHTML = analysisText.innerHTML + `greatly exceeding the difficulty target of ${targetText}, resulting in an exceptional success.`;
                    }
                 } else { // Failure
                    let degreeOfFailure = (targetValue - co.integer) / targetValue;
                    if (degreeOfFailure < 0.1) {
                        analysisText.innerHTML = analysisText.innerHTML + `barely missing the difficulty target of ${targetText}, resulting in a mild failure.`;
                    } else if (degreeOfFailure < 0.8) {
                        analysisText.innerHTML = analysisText.innerHTML + `missing the difficulty target of ${targetText}, resulting in a failure.`;
                    } else { // Serious failure
                        analysisText.innerHTML = analysisText.innerHTML + `dramatically missing the difficulty target of ${targetText}, resulting in a serious failure.`;
                    }
                 }
             }
         }
 
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

// Load initial conversation data
fetch('/get_conversation', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ conversation_id: activeConversationId }),
})
.then(response => response.json())
.then(data => {
    if (data.status === 'success') {
        let location = data.location;
        let created_at = data.created_at;

        addConversationObject({
            "type": "intro_blurb",
            "text": data.intro_blurb
        });

        if (data.game_has_begun) {
            console.debug("game has begun");
            addConversationObjects(data.new_conversation_objects);
        } else {
            console.debug("game has not begun (yet)");
            // Store conversation objects for later use after begin game button is pressed
            const storedConversationObjects = data.new_conversation_objects;
            
            // Show begin game button
            beginGameButton.style.display = 'block';
            
            // Add click handler to display stored objects after button press
            beginGameButton.addEventListener('click', function() {
                beginGameButton.style.display = 'none';
                showThinkingMessage();
                const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                wait(4500).then(() => {
                    clearThinkingMessage();
                    addConversationObjects(storedConversationObjects);
                    inputContainer.classList.remove('hidden');
                });
            });
        }

        
        
        // Format the created_at date
        const formattedCreatedDate = new Date(created_at);
        created_at = formattedCreatedDate.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        }).replace(' PM', 'PM').replace(' AM', 'AM');
        
        chatTitle.textContent = location + ", created on " + created_at;
    }
})
.catch(error => {
    console.error('Error loading conversation:', error);
    addConversationObject({
        "type": "server_error",
        "text": "Error loading conversation. Please try refreshing the page."
    });
});


function showThinkingMessage() {
    // Add loading message with animated dots
    loadingDiv = document.createElement('div');
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
    dotAnimation = setInterval(() => {
        dots.textContent = '.'.repeat(dotCount);
        dotCount = (dotCount % 3) + 1;
    }, 500);

    scrollChatNearBottom();
}

function clearThinkingMessage() {
    if (dotAnimation) {
        clearInterval(dotAnimation);
    }
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

function sendMessage() {
    console.log("sendMessage");
    if (!activeConversationId) {
        addConversationObject({
            "type": "server_error",
            "text": "No active conversation. Please refresh the page."
        });
        return;
    }

    const text = userInput.value.trim();
    if (true) { //TODO: Remove this
        // Check for boot sequence command
        if (text === "run_boot_sequence") {
            fetch('/advance_conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    user_message: text,
                    run_boot_sequence: true,
                    conversation_id: activeConversationId
                }),
            })
            .then(response => response.json())
            .then(data => {
                addConversationObjects(data.new_conversation_objects);
            })
            .catch(error => {
                console.error('Error:', error);
                console.error('Error stack:', error.stack);
                addConversationObject({
                    "type": "server_error",
                    "text": "An error occurred during boot sequence. Please try again."
                });
            });
            userInput.value = '';
            userInput.style.height = '60px';
            return;
        }

        if (text) {
            addConversationObject({
                "type": "user_message",
                "text": text
            });    
        }
    
        
        userInput.value = '';
        userInput.style.height = '60px';

        showThinkingMessage();

        fetch('/advance_conversation', {
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
            clearThinkingMessage();
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
            addConversationObject({
                "type": "server_error",
                "text": "An unhandled error occurred. Refresh this page and try again."
            });
        });
    }
}

function scrollChatNearBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight - chatContainer.clientHeight - 250;
}

// Add scroll event listener to chat container
let hasOverlapped = false;  // Track if overlap has occurred

function checkOverlap() {
    if (hasOverlapped) return;  // Skip checking if overlap has already occurred

    const headerBar = document.querySelector('.header-bar');
    const chatTitle = document.getElementById('chat-title');
    const chatMessagesWrapper = document.getElementById('chat-messages-wrapper');

    // Get all message content elements
    const messageContents = chatMessagesWrapper.querySelectorAll('.module');
    const titleRect = chatTitle.getBoundingClientRect();

    // Check overlap with any message content
    for (const messageContent of messageContents) {
        const messageRect = messageContent.getBoundingClientRect();

        if (
            titleRect.bottom > messageRect.top &&
            titleRect.top < messageRect.bottom &&
            titleRect.right > messageRect.left &&
            titleRect.left < messageRect.right
        ) {
            headerBar.style.backgroundColor = '#002727';
            hasOverlapped = true;  // Set flag to true once overlap occurs
            chatContainer.removeEventListener('scroll', checkOverlap);  // Remove scroll listener
            break;  // Exit loop once overlap is found
        }
    }
}

chatContainer.addEventListener('scroll', checkOverlap);

