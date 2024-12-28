const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');

const topic = window.location.pathname.split('/')[2]; // Extract topic from URL

sendButton.addEventListener('click', sendMessage);

userInput.addEventListener("keyup", function(event) {
    if (event.keyCode === 13) {
        event.preventDefault();
        sendButton.click();
    }
});

function sendMessage() {
    const message = userInput.value.trim();
    if (message === "") return;

    displayMessage(message, 'user');
    userInput.value = '';

    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: message, topic: topic })
    })
    .then(response => response.json())
    .then(data => {
        displayMessage(data.response, 'bot');
    })
    .catch(error => {
        console.error('Error:', error);
        displayMessage("Error communicating with the server.", 'bot');
    });
}

function displayMessage(message, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    messageDiv.textContent = message;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight; // Auto-scroll
}