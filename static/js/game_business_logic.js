import * as uiManager from './game_dom.js';
import * as server from './game_server_comms.js';

let storedConversationObjects = [];
let weAreWaitingForServerResponse = false;
let activeConversationId = window.conversationId;

function on_message_submitted() {
    const user_message = uiManager.getUserMessage();

    //Validate message

    if (weAreWaitingForServerResponse) {
        console.info("we are waiting for server response, so we don't do anything");
        return;
    }

    if (user_message === "") {
        console.info("user message is empty, so we don't do anything");
        return;
    }

    if (activeConversationId === null) {
        console.info("no active conversation, so we don't do anything");
        uiManager.setErrorState("No active conversation.");
        return;
    }


    if (user_message === "run_boot_sequence") {
        
        //If it's a boot sequence, initiate boot sequence on server
        weAreWaitingForServerResponse = true;
        uiManager.setWeAreWaitingForServerResponse(true);
        server.sendMessageAndGetResponseFromServer(user_message, activeConversationId, true)
            .then(conversationObjects => {
                console.info("got response from server");
                weAreWaitingForServerResponse = false;
                uiManager.addNewMessagesFromServer(conversationObjects);
            })
            .catch(error => {
                console.info("got an error from the server");
                weAreWaitingForServerResponse = false;
                console.error('Error:', error);
                uiManager.setErrorState(error.message);
            });
        return;
    } else {
        //If it's not a boot sequence, send the message to the server

        uiManager.addUserMessage(user_message);    // This is optimistic. It's possible that it wont stick if the server errors out.
        weAreWaitingForServerResponse = true;
        uiManager.setWeAreWaitingForServerResponse(true);
    
        server.sendMessageAndGetResponseFromServer(user_message, activeConversationId)
            .then(conversationObjects => {
                weAreWaitingForServerResponse = false;
                uiManager.setWeAreWaitingForServerResponse(false);
                uiManager.addNewMessagesFromServer(conversationObjects);
            })
            .catch(error => {
                weAreWaitingForServerResponse = false;
                uiManager.setWeAreWaitingForServerResponse(false);
                console.error('Error:', error);
                uiManager.setErrorState(error.message);
            });
    }

    //_advanceConversationWithThisMessage(user_message);
}

async function on_page_load() {

    //Listen to various UI events

    uiManager.subscribeToUserMessageSubmitted(on_message_submitted);
    uiManager.subscribeToBeginGameButton(on_begin_game_button_clicked);
    
    //Get and put initial conversation data into the page

    try {   
        const data = await server.getInitialConversationDataFromServer(activeConversationId);
        
       
        if (data) {
            const { name, created_at, intro_blurb, new_conversation_objects, game_has_begun } = data;
            
            if (game_has_begun) {
                //Set up UI for a game that has already begun
                uiManager.showIntroBlurb(intro_blurb);
                console.debug("conversation objects: " + new_conversation_objects);
                uiManager.renderConversationObjects(new_conversation_objects);
                uiManager.makeItSoUsersCanProvideInput();
                uiManager.setGameTitle(name);
            } else {
                //Set up UI for a game that has not yet begun

                console.info("game name: " + name);
                uiManager.showIntroBlurb(intro_blurb);
                console.info("game has not begun (yet)");
                console.debug("storing " + new_conversation_objects.length + " conversation objects for later use");
                storedConversationObjects = new_conversation_objects;
                
                uiManager.setGameTitle(name);
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

    //_loadConversationIntoPage(conversationId);
    console.info("loaded conversation into page");
}

document.addEventListener('DOMContentLoaded', function() {
    on_page_load();
});






function on_begin_game_button_clicked() {
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
    console.debug("storing " + new_conversation_objects.length + " conversation objects for later use");
    storedConversationObjects = new_conversation_objects;
    
    uiManager.setGameTitle(name);
}

function _advanceConversationWithThisMessage(user_message) {

    //Validate message

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
        //If it's a boot sequence, initiate boot sequence on server

        uiManager.setWeAreWaitingForServerResponse(true);
        server.sendMessageAndGetResponseFromServer(user_message, activeConversationId, true)
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
        //If it's not a boot sequence, send the message to the server

        uiManager.addUserMessage(user_message);    // This is optimistic. It's possible that it wont stick if the server errors out.
        uiManager.setWeAreWaitingForServerResponse(true);
    
        server.sendMessageAndGetResponseFromServer(user_message, activeConversationId)
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