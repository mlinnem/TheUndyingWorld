// New file for index.html specific functionality
document.addEventListener('DOMContentLoaded', () => {
    const conversationList = document.getElementById('saved-game-picker');
    const updateStatus = document.getElementById('update-status');
    updateConversationList();

    function updateConversationList() {
        fetch('/get_conversation_listings')
            .then(response => response.json())
            .then(data => {
                conversationList.innerHTML = '';
                
                const sortedConversations = data.conversation_listings.sort((a, b) => {
                    if (!a.last_updated && !b.last_updated) {
                        return new Date(b.name) - new Date(a.name);
                    }
                    if (!a.last_updated) return 1;
                    if (!b.last_updated) return -1;
                    return new Date(b.last_updated) - new Date(a.last_updated);
                });

                sortedConversations.forEach(conv => {
                    const convDiv = document.createElement('div');
                    convDiv.classList.add('conversation-item');
                    
                    const span = document.createElement('span');
                    span.classList.add('conversation-item-text');
                    
                    const date = new Date(conv.name);
                    const formattedDate = date.toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                    });
                    
                    span.textContent = "Started on " + formattedDate + ", last updated " + formattedDate + " (" + conv.message_count + " messages)";
                    convDiv.appendChild(span);
                    
                    
                    const controlBox = document.createElement('div');
                    controlBox.classList.add('control-box');

                    const continueBtn = document.createElement('button');
                    continueBtn.textContent = 'Continue';
                    continueBtn.classList.add('continue-btn');
                    continueBtn.onclick = (e) => {
                        e.stopPropagation();
                        window.location.href = `/game/${conv.conversation_id}`;
                    };

                    controlBox.appendChild(continueBtn);

                    const deleteBtn = document.createElement('button');
                    deleteBtn.textContent = 'X';
                    deleteBtn.classList.add('delete-btn');
                    deleteBtn.onclick = (e) => {
                        e.stopPropagation();
                        deleteConversation(conv.conversation_id);
                    };

                    controlBox.appendChild(deleteBtn);
                    
                    convDiv.appendChild(controlBox)
                    conversationList.appendChild(convDiv);
                });
            })
            .catch(error => {
                console.error('Error:', error);
                updateStatus.textContent = 'Error loading conversations';
            });
    }

    function deleteConversation(conversationId) {
        if (!confirm('Are you sure you want to delete this conversation? This cannot be undone.')) {
            return;
        }

        fetch('/delete_conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ conversation_id: conversationId }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateConversationList();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatus.textContent = 'Error deleting conversation';
        });
    }
}); 