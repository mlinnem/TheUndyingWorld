import * as uiManager from './game-dom.js';
import * as server from './game-server-comms.js';

let conversationObjectsToShowOnBeginGame = [];
let weAreWaitingForServerResponse = false;
let activeConversationId = window.conversationId;

async function onPageLoad() {
    try {   

         //Get initial conversation data from server

        weAreWaitingForServerResponse = true;
        uiManager.reactToWaitingForServerResponse();
        const data = await server.getInitialConversationDataFromServer(activeConversationId);
        weAreWaitingForServerResponse = false;
        uiManager.reactToNotWaitingForServerResponse();
       
        if (!data) {
            uiManager.setErrorState("Unable to fetch initial conversation data.");
            return;
        }

        const { name, created_at, intro_blurb, new_conversation_objects, game_has_already_begun } = data;
       
            
        uiManager.setGameTitle(name);
        uiManager.showIntroBlurb(intro_blurb);
        
        //Check if we loaded a game that is fresh, or has already begun
        
        if (game_has_already_begun) {
            //Set up UI for a game that has already begun

            uiManager.renderConversationObjects(new_conversation_objects);

            uiManager.subscribeToUserMessageSubmitted(onMessageSubmitted);
            uiManager.makeItSoUsersCanProvideInput();     
        } else {
            //Set up UI for a game that is fresh

            conversationObjectsToShowOnBeginGame = new_conversation_objects;
            uiManager.subscribeToBeginGameEvent(onGameBeginInitiated);
            uiManager.allowUserToBeginGame();

        }
    } catch (error) {
        uiManager.reactToNotWaitingForServerResponse();
        uiManager.setErrorState("Error initializing page.");
        console.error('Error initializing page:', error);
    }
}

function onGameBeginInitiated() {
    uiManager.reactToBeginGameInitiated();
    uiManager.reactToWaitingForServerResponse();
    const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));
    wait(4500).then(() => {
        uiManager.reactToNotWaitingForServerResponse();
        uiManager.beginGameByShowingInitialConversationObjects(conversationObjectsToShowOnBeginGame);
        uiManager.subscribeToUserMessageSubmitted(onMessageSubmitted);
        uiManager.makeItSoUsersCanProvideInput();
        
    });
}

function onMessageSubmitted(message_text) {
    const user_message = uiManager.getUserMessage();

    uiManager.reactToUserMessageSubmitted();
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

        uiManager.reactToWaitingForServerResponse();
        server.sendMessageAndGetResponseFromServer(user_message, activeConversationId, true)
            .then(conversationObjects => {
                uiManager.reactToNotWaitingForServerResponse();
                uiManager.addNewMessagesFromServer(conversationObjects);
            })
            .catch(error => {
                uiManager.reactToNotWaitingForServerResponse();
                uiManager.setErrorState(error.message);
            });
        return;
    } else {

        //If it's not a boot sequence, send the message to the server

        uiManager.addUserMessage(user_message);    // This is optimistic. It's possible that it wont stick if the server errors out.
        uiManager.reactToWaitingForServerResponse();
        server.sendMessageAndGetResponseFromServer(user_message, activeConversationId)
            .then(conversationObjects => {
                uiManager.reactToNotWaitingForServerResponse();
                uiManager.addNewMessagesFromServer(conversationObjects);
            })
            .catch(error => {
                console.error("error: ", error);
                uiManager.reactToNotWaitingForServerResponse();
                uiManager.setErrorState(error.message);
            });
    }
}



document.addEventListener('DOMContentLoaded', function() {
    onPageLoad();
});

export {
    onMessageSubmitted as on_message_submitted,
    onPageLoad as on_page_load,
};