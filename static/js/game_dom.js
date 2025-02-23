// DOM Elements
const headerBar = document.querySelector('.page-title-bar');
const chatContainer = document.getElementById('chat-container');
const chatMessagesWrapper = document.getElementById('chat-messages-wrapper');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const chatTitle = document.getElementById('chat-title');
const inputContainer = document.getElementsByClassName('input-container')[0];
const beginGameButton = document.getElementById('begin-game-button');

let dotAnimation;
let loadingDiv;

let activeConversationId = window.conversationId;
let v_isWaitingForResponse;

// Wait for DOM to be loaded before adding event listeners
document.addEventListener('DOMContentLoaded', function() {
    sendButton.addEventListener('click', function() {
        const user_message = userInput.value.trim();
        on_message_submitted(user_message);
    });

    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const user_message = userInput.value.trim();
            on_message_submitted(user_message);
        }
    });

    userInput.addEventListener('input', function() {
        if (this.scrollHeight > this.clientHeight) {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        }
    });

    chatContainer.addEventListener('scroll', _checkOverlap);

    on_page_load();
});

function setupWhenGameAlreadyBegun(name, intro_blurb, conversation_objects) {
    _add_intro_blurb(intro_blurb);
    console.debug("conversation objects: " + conversation_objects);
    _addConversationObjects(conversation_objects);
    inputContainer.classList.remove('hidden');
    _set_chat_title(name);
}

function setupWhenGameNotYetBegun(name, intro_blurb, new_conversation_objects) {
    _add_intro_blurb(intro_blurb);
    console.info("game has not begun (yet)");
    // Store conversation objects for later use after begin game button is pressed
    console.debug("storing " + new_conversation_objects.length + " conversation objects for later use");
    const storedConversationObjects = new_conversation_objects;
    
    // Show begin game button
    beginGameButton.classList.remove('hidden');
    
    // Add click handler to display stored objects after button press
    beginGameButton.addEventListener('click', function() {
        console.info("begin game button clicked");
        beginGameButton.classList.add('hidden');
        _showThinkingMessage();
        const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));
        wait(4500).then(() => {
            _clearThinkingMessage();
            console.debug("adding first message after button press");
            _addConversationObjects(storedConversationObjects);
            inputContainer.classList.remove('hidden');
        });
    });
    _set_chat_title(name);
}

function getUserMessage() {
    return userInput.value.trim();
}

function getActiveConversationId() {
    return activeConversationId;
}

function weAreWaitingForServerResponse() {
    return v_isWaitingForResponse;
}


function addUserMessage(user_message) {
    _addConversationObject({
        "type": "user_message",
        "text": user_message
    }); 
    _resetInputStateToEmpty();
}

function addNewMessagesFromServer(conversation_objects) {
    _addConversationObjects(conversation_objects);
    v_isWaitingForResponse = false;
}

function setWeAreWaitingForServerResponse(status) {
    if (status) {
        _showThinkingMessage();
        sendButton.classList.add('disabled');
        userInput.placeholder = "Waiting for response...";
    } else {
        _clearThinkingMessage();
        sendButton.classList.remove('disabled');
        userInput.placeholder = "Propose an action...";
    }
    v_isWaitingForResponse = status;
}

function setErrorState(error_message) {
    _addConversationObject({
        "type": "error",
        "text": error_message
    });
}

function _resetInputStateToEmpty() {
    userInput.value = '';
    userInput.style.height = '60px';
}

function _set_chat_title(name) {
    chatTitle.textContent = name;
}


function _add_intro_blurb(intro_blurb) {
    _addConversationObject({
        "type": "intro_blurb",
        "text": intro_blurb
    });
}

function _showThinkingMessage() {
    // Add loading message with animated dots
    loadingDiv = document.createElement('div');
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
    dotAnimation = setInterval(() => {
        dots.textContent = '.'.repeat(dotCount);
        dotCount = (dotCount % 3) + 1;
    }, 500);

    _scrollChatNearBottom();
}

function _clearThinkingMessage() {
    if (dotAnimation) {
        clearInterval(dotAnimation);
    }
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

function _get_or_create_difficulty_check_element() {
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


function _scrollChatNearBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight - chatContainer.clientHeight - 250;
}

let hasOverlapped = false;  // Track if overlap has occurred

function _checkOverlap() {
    if (hasOverlapped) return;

    
    const chatTitle = document.getElementById('chat-title');
    const chatMessagesWrapper = document.getElementById('chat-messages-wrapper');

    const messageContents = chatMessagesWrapper.querySelectorAll('.module');
    const titleRect = chatTitle.getBoundingClientRect();

    for (const messageContent of messageContents) {
        const messageRect = messageContent.getBoundingClientRect();

        if (
            titleRect.bottom > messageRect.top &&
            titleRect.top < messageRect.bottom &&
            titleRect.right > messageRect.left &&
            titleRect.left < messageRect.right
        ) {
            _setHeaderBarToSolid();
            hasOverlapped = true;
            chatContainer.removeEventListener('scroll', _checkOverlap);
            break;
        }
    }
}

function _setHeaderBarToSolid() {
    headerBar.style.backgroundColor = '#132020';
}

// Conversation processing functions
function _addConversationObjects(conversation_objects) {
    console.info("adding " + conversation_objects.length + " conversation objects");
    conversation_objects.forEach(conversation_object => {
        _addConversationObject(conversation_object);
    });
}

function _addConversationObject(co) {
    let coDiv;
    let color;

    if (co.type === 'user_message') {
        console.debug("adding user message");
        coDiv = make_module(co);
        inject_content_into_element(coDiv, '.module_contents', body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding', 'primary-text-style', 'right');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'intro_blurb') {
        console.debug("adding intro blurb");
        coDiv = make_module(co);
        inject_content_into_element(coDiv, '.module_contents', body_text(marked.parse(co.text)));
        coDiv.classList.add('freestanding', 'primary-text-style', 'left');
        chatMessagesWrapper.appendChild(coDiv);
    } else if (co.type === 'map_data' || co.type === 'world_gen_data')  {
        console.debug("adding world gen data");
        coDiv = make_module(co);
        inject_content_into_element(coDiv, '.module_contents', header("World Gen Data") + body_text(marked.parse(co.text)));
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
        const difficultyCheckElement = _get_or_create_difficulty_check_element();
        const analysisText = difficultyCheckElement.querySelector('.analysis-text');
        if (analysisText) {
            analysisText.innerHTML = marked.parse(co.text);
        }
    } else if (co.type === 'difficulty_target') {
        console.debug("adding difficulty target");
        const difficultyCheckElement = _get_or_create_difficulty_check_element();
        if (co.text === "Trivial") {
            inject_style_into_element(difficultyCheckElement, '.separator', `display: none;`);
            inject_style_into_element(difficultyCheckElement, '.difficulty-roll', `display: none;`);
            inject_content_into_element(difficultyCheckElement, '.difficulty-target', info_text("Trivial Success"));
            inject_style_into_element(difficultyCheckElement, '.difficulty-bar-filled', `background-color: hsl(180, 42%, 18%); width: 100%;`);
            inject_style_into_element(difficultyCheckElement, '.difficulty-target', `margin: 0px;`);
            const analysisText = difficultyCheckElement.querySelector('.analysis-text');
            if (analysisText && analysisText.innerHTML) {
                analysisText.innerHTML += "\n\nThus your action is a success.";
            }
        } else {
            inject_style_into_element(difficultyCheckElement, '.difficulty-bar', `width: 100%;`);
            inject_style_into_element(difficultyCheckElement, '.target-marker', `left: ${co.text}%; display: block;`);
            inject_content_into_element(difficultyCheckElement, '.difficulty-target', info_text(co.text));
        }
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
        const difficultyCheckElement = _get_or_create_difficulty_check_element();
        color = determine_difficulty_color(difficultyCheckElement, co.integer);
        inject_style_into_element(difficultyCheckElement, '.difficulty-bar', `width: 100%;`);
        if (co.integer == 1 || co.integer == 2) {
            inject_style_into_element(difficultyCheckElement, '.difficulty-bar-filled', `width: ${co.integer}%; background-color: ${color}; box-shadow: 0 0 4px 2px hsla(0, 60%, 50%, 0.25);`);
        } else if (co.integer == 99 || co.integer == 100) {
            inject_style_into_element(difficultyCheckElement, '.difficulty-bar-filled', `width: ${co.integer}%; background-color: ${color}; box-shadow: 0 0 4px 2px hsla(180, 100%, 35%, 0.25);`);
        } else {
            inject_style_into_element(difficultyCheckElement, '.difficulty-bar-filled', `width: ${co.integer}%; background-color: ${color};`);
        }

        inject_content_into_element(difficultyCheckElement, '.difficulty-roll', info_text(co.integer.toString()));

         //disable the box shadow if the target is within 4 points of the roll, because it makes it hard to see if you're under or over.
         const targetElement = difficultyCheckElement.querySelector('.difficulty-target');
         const targetText = targetElement ? targetElement.textContent.replace('Target', '').trim() : null;
         
         if (!isNaN(parseInt(targetText))) {
             const targetValue = parseInt(targetText);
             if (Math.abs(targetValue - co.integer) <= 6) {
                 append_style_to_element(difficultyCheckElement, '.target-marker', 'box-shadow: none;');
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
        const worldRevealElement = get_or_create_world_reveal_element(presceneDiv);
        color = determine_world_reveal_color(worldRevealElement, co.integer);
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
    } else if (co.type === 'tool_use') {
        console.debug("ignoring tool use"); 
        return;
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
    } else if (co.type === 'boot_sequence_end') {
        console.debug("ignoring boot sequence end co");
        return;
    } else {
        console.warn("unknown conversation object type: ", co.type);
    }
}