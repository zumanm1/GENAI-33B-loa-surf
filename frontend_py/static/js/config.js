document.addEventListener('DOMContentLoaded', function() {
    // Fetch and set current AI config on page load
    fetch('/api/ai/config')
        .then(response => response.json())
        .then(data => {
            document.getElementById('ollamaModel').value = data.ollama_model;
            document.getElementById('embeddingModel').value = data.embedding_model;
            document.getElementById('aiAgentType').value = data.agent_type;
            document.getElementById('memoryConfig').value = data.memory_config;
        });

    // Save AI config
    document.getElementById('saveConfigBtn').addEventListener('click', () => {
        const config = {
            ollama_model: document.getElementById('ollamaModel').value,
            embedding_model: document.getElementById('embeddingModel').value,
            agent_type: document.getElementById('aiAgentType').value,
            memory_config: document.getElementById('memoryConfig').value,
        };

        fetch('/api/ai/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Config saved:', data);
            alert('Configuration saved successfully!');
        });
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

        fetch('/api/rag_query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        })
        .then(response => response.json())
        .then(data => {
            appendMessage('ai', data.response);
        })
        .catch(error => {
            console.error('Error:', error);
            appendMessage('ai', 'Sorry, an error occurred.');
        });
    }

    function appendMessage(sender, text) {
        const chatHistory = document.getElementById('chatHistory');
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', `${sender}-message`);
        messageElement.innerText = text;
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    // Document Upload
    document.getElementById('uploadForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        fetch('/api/upload_document', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message || data.error);
        })
        .catch(error => {
            console.error('Upload error:', error);
            alert('An error occurred during upload.');
        });
    });

    // Live Logs
    function fetchLogs() {
        fetch('/api/logs')
            .then(response => response.json())
            .then(logs => {
                const logContainer = document.getElementById('logContainer');
                logContainer.innerHTML = '';
                logs.forEach(log => {
                    const logElement = document.createElement('div');
                    logElement.classList.add('log-line', `log-${log.level.toLowerCase()}`);
                    logElement.textContent = `[${log.timestamp}] [${log.level}] ${log.message}`;
                    logContainer.appendChild(logElement);
                });
                logContainer.scrollTop = logContainer.scrollHeight;
            });
    }

    setInterval(fetchLogs, 3000); // Poll every 3 seconds
    fetchLogs(); // Initial fetch
});
