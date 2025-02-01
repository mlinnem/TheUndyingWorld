// New file for index.html specific functionality
document.addEventListener('DOMContentLoaded', () => {
    const customWorldButton = document.getElementById('custom-world-button');
    const updateStatus = document.getElementById('update-status');

    customWorldButton.addEventListener('click', startNewConversation);

    function startNewConversation() {
        fetch('/create_conversation', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Redirect to the game page with the new conversation
                    window.location.href = `/game/${data.conversation_id}`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                updateStatus.textContent = 'Error starting new conversation';
            });
    }
}); 