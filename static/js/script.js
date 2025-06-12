document.addEventListener('DOMContentLoaded', function() {
    // Landing page functionality
    if (document.getElementById('start-chat')) {
        const startButton = document.getElementById('start-chat');
        const usernameInput = document.getElementById('username');
        
        startButton.addEventListener('click', startChat);
        usernameInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') startChat();
        });
    }
    
    // Chat page functionality
    if (document.getElementById('message-input')) {
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-btn');
        const chatMessages = document.getElementById('chat-messages');
        const typingIndicator = document.getElementById('typing-indicator');
        
        // Only show the initial greeting
        showInitialGreeting();
        
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
        
        // Set up beforeunload to clean up chat
        window.addEventListener('beforeunload', endChat);
    }
});

function showInitialGreeting() {
    const chatMessages = document.getElementById('chat-messages');
    const greeting = "Hello! I'm Buddy, your AI assistant. How can I help you today? 🤖";
    
    const greetingElement = createMessageElement('bot', greeting);
    chatMessages.appendChild(greetingElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function startChat() {
    const username = document.getElementById('username').value.trim();
    if (!username) {
        alert('Please enter your name to start chatting');
        return;
    }
    
    const startButton = document.getElementById('start-chat');
    startButton.disabled = true;
    startButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
    
    fetch('/start-chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `username=${encodeURIComponent(username)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.href = '/chat';
        } else {
            alert(data.message);
            startButton.disabled = false;
            startButton.innerHTML = 'Start Chatting <i class="fas fa-arrow-right"></i>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        startButton.disabled = false;
        startButton.innerHTML = 'Start Chatting <i class="fas fa-arrow-right"></i>';
    });
}

function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    const chatMessages = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing-indicator');
    
    if (!message) return;
    
    // Add user message to chat
    const userMessageElement = createMessageElement('user', message);
    chatMessages.appendChild(userMessageElement);
    messageInput.value = '';
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Show typing indicator
    typingIndicator.style.display = 'flex';
    
    // Send message to server
    fetch('/send-message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        typingIndicator.style.display = 'none';
        
        if (data.status === 'success') {
            // Add bot response to chat
            const botMessageElement = createMessageElement('bot', data.response, data.timestamp);
            chatMessages.appendChild(botMessageElement);
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        typingIndicator.style.display = 'none';
        console.error('Error:', error);
    });
}

function endChat() {
    // Clean up the chat session when leaving the page
    fetch('/end-chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    }).catch(error => console.error('Error ending chat:', error));
}

function createMessageElement(type, message, timestamp = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type} message-animation`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = `message-content ${type}-message`;
    contentDiv.textContent = message;
    
    if (timestamp) {
        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = formatTimestamp(timestamp);
        contentDiv.appendChild(timeSpan);
    }
    
    messageDiv.appendChild(contentDiv);
    return messageDiv;
}

function formatTimestamp(timestamp) {
    if (!timestamp) return '';
    return timestamp;
}