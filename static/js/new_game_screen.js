document.addEventListener('DOMContentLoaded', () => {
    const customWorldButton = document.getElementById('custom-world-button');
    const worldPicker = document.querySelector('.world-picker');
    const loadingIndicator = document.getElementById('loading-indicator');
    const customWorldCard = worldPicker.lastElementChild;
    
    // Fetch and display game world listings
    updateGameWorldListings();
    
    customWorldButton.addEventListener('click', startNewCustomConversation);

    function updateGameWorldListings() {
        fetch('/get_game_world_listings')
            .then(response => response.json())
            .then(data => {
                // Remove loading indicator
                loadingIndicator.remove();
                
                // Add game world listings
                data.game_seed_listings.forEach(world => {
                    const worldCard = document.createElement('div');
                    worldCard.classList.add('built-in-world');
                    
                    worldCard.innerHTML = `
                        <div class="world-title">${world.location}</div>
                        <div class="world-description">${world.description}</div>
                        <button class="play-world-button" data-seed-id="${world.id}">Play</button>
                    `;
                    
                    const playButton = worldCard.querySelector('.play-world-button');
                    playButton.addEventListener('click', () => startNewConversationFromSeed(world.id));
                    
                    worldPicker.appendChild(worldCard);
                });
                
                // Show and append the custom world card
                customWorldCard.style.display = 'flex';
                worldPicker.appendChild(customWorldCard);
            })
            .catch(error => {
                console.error('Error fetching game world listings:', error);
                loadingIndicator.textContent = 'Error loading worlds. Please try again later.';
            });
    }

    function startNewConversationFromSeed(seedId) {
        fetch('/create_conversation_from_seed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ seed_id: seedId })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.href = `/game/${data.conversation_id}`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }

    function startNewCustomConversation() {
        fetch('/create_conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.href = `/game/${data.conversation_id}`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    }
}); 