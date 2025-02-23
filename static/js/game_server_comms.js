async function getInitialConversationDataFromServer(activeConversationId) {
    try {
        const response = await fetch('/get_conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ conversation_id: activeConversationId }),
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            console.info("conversation data fetched");
            console.debug("conversation data: " + JSON.stringify(data));
            return {
                name: data.conversation_name,
                created_at: data.created_at,
                intro_blurb: data.intro_blurb,
                new_conversation_objects: data.new_conversation_objects,
                game_has_begun: data.game_has_begun
            };
        } else {
            console.error("Error fetching conversation data");
            return null;
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
        _addConversationObject({
            "type": "server_error",
            "text": "Error loading conversation. Please try refreshing the page."
        });
        return null;
    }
}

async function sendMessageAndGetResponseFromServer(text,activeConversationId, isBootSequence = false) {
    const requestBody = {
        user_message: text,
        conversation_id: activeConversationId
    };

    if (isBootSequence) {
        requestBody.run_boot_sequence = true;
    }

    const response = await fetch('/advance_conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
    });

    const data = await response.json();
    
    // If there's any kind of error, throw it with relevant details
    if (data.success_type === 'partial_success') {
        const errorMessages = {
            'authentication_error': 'Authentication error. Please check your API key and try again.',
            'permission_denied_error': 'Permission denied. Please check your API key permissions.',
            'rate_limit_error': 'Rate limit exceeded. Please wait a minute before trying again.',
            'internal_error': 'An internal error occurred. Please try again later.',
            'unknown_error': data.error_message || 'An unknown error occurred.'
        };
        
        throw new Error(errorMessages[data.error_type] || 'An unexpected error occurred. Try again later.');
    }

    // Return just the conversation objects on success
    return data.new_conversation_objects;
}

export {
    getInitialConversationDataFromServer,
    sendMessageAndGetResponseFromServer
};

