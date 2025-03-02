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
    const response = await fetch('/advance_conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
    });
    console.info("...received response from server...");

    // Add error checking for HTTP errors
    if (!response.ok) {
        const errorMessage = await response.text();
        console.error(`HTTP error! status: ${response.status}, message: ${errorMessage}`);
        if (response.status === 403) {
            console.error("This typically happens when the server is not in fact running.")
        }
        throw new Error("We ran into an error contacting the server. This could be a temporary issue. Please try again later.");
    }

    const data = await response.json();
    

    if (data.status === 'error') {
        console.error("Error fetching conversation data");
        throw new Error(data.error_message || 'An unexpected error occurred. Try again later.');
    }

    // Return just the conversation objects on success
    console.info("...received " + data.new_conversation_objects.length + " new conversation objects for conversation id: " + activeConversationId + "...");
    
    return data.new_conversation_objects;
}

export {
    getInitialConversationDataFromServer,
    sendMessageAndGetResponseFromServer
};

