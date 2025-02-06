
document.addEventListener('DOMContentLoaded', () => {
    const conversationList = document.getElementById('saved-game-picker');
    const updateStatus = document.getElementById('update-status');
    updateConversationList();

    function getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        
        let interval = seconds / 31536000; // years
        if (interval > 1) {
            return Math.floor(interval) + ' years ago';
        }
        
        interval = seconds / 2592000; // months
        if (interval > 1) {
            return Math.floor(interval) + ' months ago';
        }
        
        interval = seconds / 86400; // days
        if (interval > 1) {
            return Math.floor(interval) + ' days ago';
        }
        
        interval = seconds / 3600; // hours
        if (interval > 1) {
            return Math.floor(interval) + ' hours ago';
        }
        
        interval = seconds / 60; // minutes
        if (interval > 1) {
            return Math.floor(interval) + ' minutes ago';
        }
        
        if(seconds < 10) return 'just now';
        
        return Math.floor(seconds) + ' seconds ago';
    }

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
                    
                  
                    
                    const text_content_block = document.createElement('div');
                    text_content_block.classList.add('conversation-item-text-block');

                    const title = document.createElement('div');
                    title.classList.add('conversation-item-title');
                    title.textContent = conv.location;
                    text_content_block.appendChild(title);

                    const metadata = document.createElement('div');
                    metadata.classList.add('conversation-item-metadata');
                    metadata.textContent = conv.location;
                    text_content_block.appendChild(metadata);
                    
                    const date = new Date(conv.name);
                    
                    const formattedDateForLastUpdated = date.toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                    });

                    const createdDate = new Date(conv.created_at);
                    const formattedDateForCreatedAt = createdDate.toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                    });
                    
                    const lastPlayedString = "Played " + getTimeAgo(date);
                    const messageCountString = "" + conv.message_count + " messages in game";
                    const dateStartedString = "Started on " + formattedDateForCreatedAt;

                    const metadataList = document.createElement('ul');
                    metadataList.style.listStyle = 'none';
                    metadataList.style.padding = '0';
                    metadataList.style.margin = '0';

                    const lastPlayedLi = document.createElement('li');
                    lastPlayedLi.textContent = lastPlayedString;
                    metadataList.appendChild(lastPlayedLi);

                    const messageCountLi = document.createElement('li'); 
                    messageCountLi.textContent = messageCountString;
                    metadataList.appendChild(messageCountLi);

                    const dateStartedLi = document.createElement('li');
                    dateStartedLi.textContent = dateStartedString;
                    metadataList.appendChild(dateStartedLi);

                    metadata.textContent = '';
                    metadata.appendChild(metadataList);
                    convDiv.appendChild(text_content_block);
                    
                    
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