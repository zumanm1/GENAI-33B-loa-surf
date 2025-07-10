document.addEventListener('DOMContentLoaded', function() {
    // Fetch and display current AI configuration on page load
    fetch('/api/ai/config')
        .then(response => response.json())
        .then(data => {
            document.getElementById('currentModel').textContent = data.ollama_model;
            document.getElementById('currentAgentType').textContent = data.agent_type;
            
            // Set the agent type dropdown to match the current config
            const agentTypeSelect = document.getElementById('chatAgentType');
            if (agentTypeSelect) {
                agentTypeSelect.value = data.agent_type;
            }
        })
        .catch(error => {
            console.error('Error fetching AI config:', error);
            document.getElementById('currentModel').textContent = 'Error loading';
            document.getElementById('currentAgentType').textContent = 'Error loading';
        });

    // Agent type change handler
    document.getElementById('chatAgentType').addEventListener('change', function() {
        const newAgentType = this.value;
        
        // Update the displayed agent type
        document.getElementById('currentAgentType').textContent = newAgentType;
        
        // Update the backend configuration
        fetch('/api/ai/config')
            .then(response => response.json())
            .then(data => {
                // Only update the agent type, keep other settings
                const updatedConfig = {
                    ...data,
                    agent_type: newAgentType
                };
                
                return fetch('/api/ai/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(updatedConfig),
                });
            })
            .then(response => response.json())
            .then(data => {
                console.log('Agent type updated:', data);
                // Display a small notification that the agent type was updated
                const notification = document.createElement('div');
                notification.className = 'notification';
                notification.textContent = 'Agent type updated successfully!';
                document.body.appendChild(notification);
                
                // Remove the notification after 3 seconds
                setTimeout(() => {
                    notification.remove();
                }, 3000);
            })
            .catch(error => {
                console.error('Error updating agent type:', error);
            });
    });

    // Clear chat history
    document.getElementById('clearChatBtn').addEventListener('click', function() {
        const chatHistory = document.getElementById('chatHistory');
        chatHistory.innerHTML = '';
        
        // Add a system message indicating the chat was cleared
        appendMessage('system', 'Chat history cleared. How can I help you today?');
    });

    // Send query
    document.getElementById('sendQueryBtn').addEventListener('click', sendQuery);
    document.getElementById('chatInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendQuery();
        }
    });

    function sendQuery() {
        const input = document.getElementById('chatInput');
        const query = input.value.trim();
        if (query === '') return;

        appendMessage('user', query);
        input.value = '';

        // Show a typing indicator while waiting for response
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('chat-message', 'ai-message', 'typing-indicator');
        typingIndicator.innerHTML = '<span></span><span></span><span></span>';
        document.getElementById('chatHistory').appendChild(typingIndicator);

        fetch('/api/rag_query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            typingIndicator.remove();
            appendMessage('ai', data.response);
        })
        .catch(error => {
            console.error('Error:', error);
            // Remove typing indicator
            typingIndicator.remove();
            appendMessage('ai', 'Sorry, an error occurred while processing your request.');
        });
    }

    function appendMessage(sender, text) {
        const chatHistory = document.getElementById('chatHistory');
        const messageElement = document.createElement('div');
        
        if (sender === 'system') {
            messageElement.classList.add('chat-message', 'system-message');
        } else {
            messageElement.classList.add('chat-message', `${sender}-message`);
        }
        
        messageElement.innerText = text;
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    // Add initial system message
    appendMessage('system', 'Hello! I am GENAI Networks Engineer Assistant. How can I help you today?');
});
