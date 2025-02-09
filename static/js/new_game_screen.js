
document.addEventListener('DOMContentLoaded', () => {
    const customWorldButton = document.getElementById('custom-world-button');
    const worldPicker = document.querySelector('.world-picker');
    
    // Fetch and display game world listings
    updateGameWorldListings();
    
    customWorldButton.addEventListener('click', startNewCustomConversation);

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
                        <div class="world-title">${world.location}</div>
                        <div class="world-description">${world.description}</div>
                        <button class="play-world-button" data-seed-id="${world.id}">Play</button>
                    `;
                    
                    const playButton = worldCard.querySelector('.play-world-button');
                    playButton.addEventListener('click', () => startNewConversationFromSeed(world.id));
                    
                    worldPicker.appendChild(worldCard);
                });
                
                // Re-add the custom world card
                worldPicker.appendChild(customWorldCard);
            })
            .catch(error => {
                console.error('Error fetching game world listings:', error);
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