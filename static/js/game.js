uimanager = null;
server = null;

document.addEventListener('DOMContentLoaded', function() {
    on_page_load();
});

function on_page_load() {
    uimanager = new UIManager();
    server = new ServerCommunicationService();

    conversationId = window.conversationId;

    try {
        const data = getInitialConversationDataFromServer(conversationId);
        conversationService = new ConversationService(uimanager, data);
    } catch (error) {
        setErrorState("Error initializing page.");
        console.error('Error initializing page:', error);
    }
    console.info("loaded conversation into page");
}

function submitMessageToServer(user_message) {
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
                on_message_received(conversationObjects);
            })
            .catch(error => {
                on_failed_to_send_message();
            });
        return;
    } else {
        addUserMessage(user_message);    // This is optimistic. It's possible that it wont stick if the server errors out.
        setWeAreWaitingForServerResponse(true);
    
        sendMessageAndGetResponseFromServer(user_message)
            .then(conversationObjects => {
                on_message_received(conversationObjects);
            })
            .catch(error => {
                on_failed_to_send_message();
            });
    }
}

class GameController {
    constructor() {
        this.uiManager = new UIManager();
        this.serverComm = new ServerCommunicationService();
        this.gameState = new GameStateManager();
        this.conversationService = new ConversationService(
            this.uiManager,
            this.serverComm,
            this.gameState
        );

        // Bind message submission to conversation service
        this.uiManager.bindMessageSubmission(async (message) => {
            if (this.gameState.isWaitingForResponse) {
                console.info("Waiting for response, ignoring message");
                return;
            }

            if (!message) {
                console.info("Empty message, ignoring");
                return;
            }

            try {
                this.gameState.isWaitingForResponse = true;
                this.uiManager.setInputStateToWaitingForResponse();
                this.uiManager.showThinkingMessage();

                // Handle special boot sequence case
                const isBootSequence = message === "run_boot_sequence";
                if (!isBootSequence) {
                    this.uiManager.renderUserMessage(message);
                }

                const conversationObjects = await this.serverComm.sendMessage(
                    this.conversationService.getActiveConversationId(),
                    message,
                    isBootSequence
                );

                this.uiManager.clearThinkingMessage();
                this.conversationService.on_message_received(conversationObjects);
                this.uiManager.setInputStateToReady();
                this.gameState.isWaitingForResponse = false;

            } catch (error) {
                console.error("Failed to send message:", error);
                this.uiManager.clearThinkingMessage();
                this.uiManager.setInputStateToReady();
                this.gameState.isWaitingForResponse = false;
                this.uiManager.renderServerError("Failed to send message: " + error.message);
            }
        });
    }

    async initialize() {
        try {
            const conversationId = window.conversationId;
            const data = await this.serverComm.getInitialConversationData(conversationId);
            
            if (data.game_has_begun) {
                await this.conversationService.setupWhenGameAlreadyBegun(
                    data.name,
                    data.intro_blurb,
                    data.new_conversation_objects
                );
            } else {
                await this.conversationService.setupWhenGameNotYetBegun(
                    data.name,
                    data.intro_blurb,
                    data.new_conversation_objects
                );
            }

            console.info("Game initialized successfully");
        } catch (error) {
            console.error("Failed to initialize game:", error);
            this.uiManager.setErrorState("Failed to initialize game");
        }
    }
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    const game = new GameController();
    game.initialize().catch(error => {
        console.error("Critical initialization error:", error);
    });
});