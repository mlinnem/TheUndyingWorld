const ConversationErrorType = Object.freeze({
    GENERIC_HTTP_ERROR: 'GENERIC_HTTP_ERROR',
    SERVER_REPORTED_ERROR: 'SERVER_REPORTED_ERROR',
    SERVER_ERROR: 'SERVER_ERROR',
    SERVER_OFFLINE: 'SERVER_OFFLINE',
    CONNECTION_ERROR: 'CONNECTION_ERROR',
    SERVER_INTERNAL_ERROR: 'SERVER_INTERNAL_ERROR'
});

class ConversationError extends Error {
    constructor(message, type, message_was_persisted, userMessage = null) {
        super(message);
        this.name = 'ConversationError';
        if (!Object.values(ConversationErrorType).includes(type)) {
            throw new Error(`Invalid ConversationError type: ${type}`);
        }
        this.type = type;
        this.userMessage = userMessage;
        this.message_was_persisted = message_was_persisted;
    }
}

async function getInitialConversationDataFromServer(activeConversationId) {
    const response = await fetch('/get_conversation', {
        method: 'POST',
        headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ conversation_id: activeConversationId }),
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {

            if (data.new_conversation_objects && Array.isArray(data.new_conversation_objects)) {
                let messageCount = data.new_conversation_objects.length;
                console.info("received " + messageCount + " messages of initial data for conversation id: " + activeConversationId);
            }
            console.debug("conversation data: " + JSON.stringify(data));
            return {
                name: data.conversation_name,
                created_at: data.created_at,
                intro_blurb: data.intro_blurb,
                new_conversation_objects: data.new_conversation_objects,
                game_has_already_begun: data.game_has_begun
            };
        } else {
            console.error("Error fetching conversation data");
            return null;
        }
}

async function sendMessageAndGetResponseFromServer(text, activeConversationId, isBootSequence = false) {
    const requestBody = {
        user_message: text,
        conversation_id: activeConversationId
    };

    if (isBootSequence) {
        requestBody.run_boot_sequence = true;
    }

    
    console.info("...sending message to server...");
    let response;
    try {
        response = await fetch('/advance_conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody),
        });
    } catch (error) {
        // Network error - definitely not persisted
        console.error("Network error where we weren't even able to get a response from the server: " + error);
        throw new ConversationError(
            "Failed to connect to the server. Please check your internet connection and try again.",
            ConversationErrorType.CONNECTION_ERROR,
            false
        );
    }

    console.info("...received response from server...");

    // For HTTP errors, we need to check the response body for persistence info
    if (!response.ok) {
        let errorData;
        try {
            errorData = await response.json();
        } catch {
            // If we can't parse the JSON, assume message wasn't persisted
            errorData = { user_message_was_persisted: false };
        }

        const wasMessagePersisted = errorData.user_message_was_persisted || false;

        if (response.status === 403) {
            throw new ConversationError(
                `The server appears to be offline. Perhaps try again later.`,
                ConversationErrorType.SERVER_OFFLINE,
                wasMessagePersisted,
                text
            );
        } else {

            throw new ConversationError(
                `There was some sort of server error. Refresh and perhaps try again later.`,
                ConversationErrorType.GENERIC_HTTP_ERROR,
                wasMessagePersisted,
                text
            );

        }
    }

    const data = await response.json();
    

    if (data.status === 'error') {
        const wasMessagePersisted = data.user_message_was_persisted || false;

        throw new ConversationError(
            `The server had some sort of internal error. Refresh and perhaps try again later.`,
            ConversationErrorType.SERVER_INTERNAL_ERROR,
            wasMessagePersisted,
            text
        );
    }

    // Return just the conversation objects on success
    console.info("...received " + data.new_conversation_objects.length + " new conversation objects for conversation id: " + activeConversationId + "...");
    
    return data.new_conversation_objects;
}

export {
    getInitialConversationDataFromServer,
    sendMessageAndGetResponseFromServer,
    ConversationErrorType,
    ConversationError
};

