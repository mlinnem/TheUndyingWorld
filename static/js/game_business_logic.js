


function on_message_submitted() {
    const user_message = getUserMessage();
    _advanceConversationWithThisMessage(user_message);
}

function on_page_load() {
    conversationId = getActiveConversationId();
    _loadConversationIntoPage(conversationId);
    console.info("loaded conversation into page");
}

async function _loadConversationIntoPage(conversation_id) {
    try {   
        const data = await getInitialConversationDataFromServer(conversation_id);
       
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
            setErrorState("Unable to fetch initial conversation data.");
            return;
        }
    } catch (error) {
        setErrorState("Error initializing page.");
        console.error('Error initializing page:', error);
    }
}

function _advanceConversationWithThisMessage(user_message) {
    if (weAreWaitingForServerResponse()) {
        console.info("we are waiting for server response, so we don't do anything");
        return;
    }

    if (user_message === "") {
        console.info("user message is empty, so we don't do anything");
        return;
    }

    if (!getActiveConversationId()) {
        console.info("no active conversation, so we don't do anything");
        setErrorState("No active conversation.");
        return;
    }

    if (user_message === "run_boot_sequence") {
        setWeAreWaitingForServerResponse(true);
        sendMessageAndGetResponseFromServer(user_message, true)
            .then(conversationObjects => {
                console.info("got response from server");
                setWeAreWaitingForServerResponse(false);
                addNewMessagesFromServer(conversationObjects);
            })
            .catch(error => {
                console.info("got an error from the server");
                setWeAreWaitingForServerResponse(false);
                console.error('Error:', error);
                setErrorState(error.message);
            });
        _resetInputStateToEmpty();
        return;
    } else {
        addUserMessage(user_message);    // This is optimistic. It's possible that it wont stick if the server errors out.
        setWeAreWaitingForServerResponse(true);
    
        sendMessageAndGetResponseFromServer(user_message)
            .then(conversationObjects => {
                setWeAreWaitingForServerResponse(false);
                _addConversationObjects(conversationObjects);
            })
            .catch(error => {
                setWeAreWaitingForServerResponse(false);
                console.error('Error:', error);
                _addConversationObject({
                    "type": "server_error",
                    "text": error.message
                });
            });
    }
}