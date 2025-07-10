document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chat-input-full');
    const sendButton = document.querySelector('.chat-input-area .btn');
    const chatHistory = document.querySelector('.chat-history');

    const appendMessage = (text, sender) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', `${sender}-message`);
        messageElement.textContent = text;
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight; // Auto-scroll to the latest message
    };

    const handleSendMessage = async () => {
        const message = chatInput.value.trim();
        if (!message) return;

        appendMessage(message, 'user');
        chatInput.value = '';

        try {
            const response = await fetch('/api/rag/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: message }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            const aiResponse = data.response || 'No response from AI.';
            appendMessage(aiResponse, 'ai');

        } catch (error) {
            console.error('Error sending message:', error);
            appendMessage('Error: Could not connect to the AI service.', 'error');
        }
    };

    sendButton.addEventListener('click', handleSendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    });
});
