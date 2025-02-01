// New file for index.html specific functionality
document.addEventListener('DOMContentLoaded', () => {
    const customWorldButton = document.getElementById('custom-world-button');
    const worldPicker = document.querySelector('.world-picker');
    
    // Fetch and display game world listings
    updateGameWorldListings();
    
    customWorldButton.addEventListener('click', startNewConversation);

    function updateGameWorldListings() {
        fetch('/get_game_world_listings')
            .then(response => response.json())
            .then(data => {
                // Clear existing world cards except the last one (custom world)
                const customWorldCard = worldPicker.lastElementChild;
                worldPicker.innerHTML = '';
                
                // Add game world listings
                data.game_seed_listings.forEach(world => {
                    const worldCard = document.createElement('div');
                    worldCard.classList.add('built-in-world');
                    
                    worldCard.innerHTML = `
                        <div class="world-title">${world.description}</div>
                        <div class="world-description">${world.description}</div>
                        <button class="play-world-button">Play</button>
                    `;
                    
                    worldPicker.appendChild(worldCard);
                });
                
                // Re-add the custom world card
                worldPicker.appendChild(customWorldCard);
            })
            .catch(error => {
                console.error('Error fetching game world listings:', error);
            });
    }

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
            });
    }
}); 