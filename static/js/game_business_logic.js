import * as uiManager from './game_dom.js';
import * as server from './game_server_comms.js';

function on_message_submitted() {
    const user_message = uiManager.getUserMessage();
    _advanceConversationWithThisMessage(user_message);
}

function on_page_load() {

    uiManager.subscribeToUserMessageSubmitted(on_message_submitted);

    conversationId = uiManager.getActiveConversationId();
    _loadConversationIntoPage(conversationId);
    console.info("loaded conversation into page");
}

on_page_load();

function setupWhenGameAlreadyBegun(name, intro_blurb, conversation_objects) {

    uiManager.showIntroBlurb(intro_blurb);
    console.debug("conversation objects: " + conversation_objects);
    uiManager.renderConversationObjects(conversation_objects);
    uiManager.makeItSoUsersCanProvideInput();
    uiManager.setGameTitle(name);
}

function setupWhenGameNotYetBegun(name, intro_blurb, new_conversation_objects) {
    uiManager.showIntroBlurb(intro_blurb);
    console.info("game has not begun (yet)");
    // Store conversation objects for later use after begin game button is pressed
    console.debug("storing " + new_conversation_objects.length + " conversation objects for later use");
    const storedConversationObjects = new_conversation_objects;
    
    
    // Add click handler to display stored objects after button press
    beginGameButton.addEventListener('click', function() {
        console.info("begin game button clicked");
        uiManager.allowUserToBeginGame();
        uiManager.showServerIsThinking();
        const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));
        wait(4500).then(() => {
            uiManager.showServerIsNoLongerThinking();
            console.debug("adding first message after button press");
            uiManager.renderConversationObjects(storedConversationObjects);
            uiManager.makeItSoUsersCanProvideInput();
        });
    });
    uiManager.setGameTitle(name);
}




async function _loadConversationIntoPage(conversation_id) {
    try {   
        const data = await server.getInitialConversationDataFromServer(conversation_id);
       
        if (data) {
            const { name, created_at, intro_blurb, new_conversation_objects, game_has_begun } = data;
            
            if (game_has_begun) {
                setupWhenGameAlreadyBegun(name, intro_blurb, new_conversation_objects);
            } else {
                console.info("game name: " + name);
                setupWhenGameNotYetBegun(name, intro_blurb, new_conversation_objects);
            }
            console.info("page initialized");
        } else {
            uiManager.setErrorState("Unable to fetch initial conversation data.");
            return;
        }
    } catch (error) {
        uiManager.setErrorState("Error initializing page.");
        console.error('Error initializing page:', error);
    }
}

function _advanceConversationWithThisMessage(user_message) {
    if (uiManager.weAreWaitingForServerResponse()) {
        console.info("we are waiting for server response, so we don't do anything");
        return;
    }

    if (user_message === "") {
        console.info("user message is empty, so we don't do anything");
        return;
    }

    if (!uiManager.getActiveConversationId()) {
        console.info("no active conversation, so we don't do anything");
        uiManager.setErrorState("No active conversation.");
        return;
    }

    if (user_message === "run_boot_sequence") {
        uiManager.setWeAreWaitingForServerResponse(true);
        server.sendMessageAndGetResponseFromServer(user_message, uiManager.getActiveConversationId(), true)
            .then(conversationObjects => {
                console.info("got response from server");
                uiManager.setWeAreWaitingForServerResponse(false);
                uiManager.addNewMessagesFromServer(conversationObjects);
            })
            .catch(error => {
                console.info("got an error from the server");
                uiManager.setWeAreWaitingForServerResponse(false);
                console.error('Error:', error);
                uiManager.setErrorState(error.message);
            });
        return;
    } else {
        uiManager.addUserMessage(user_message);    // This is optimistic. It's possible that it wont stick if the server errors out.
        uiManager.setWeAreWaitingForServerResponse(true);
    
        server.sendMessageAndGetResponseFromServer(user_message, uiManager.getActiveConversationId())
            .then(conversationObjects => {
                uiManager.setWeAreWaitingForServerResponse(false);
                uiManager.addNewMessagesFromServer(conversationObjects);
            })
            .catch(error => {
                uiManager.setWeAreWaitingForServerResponse(false);
                console.error('Error:', error);
                uiManager.setErrorState(error.message);
            });
    }
}

export {
    on_message_submitted,
    on_page_load
};