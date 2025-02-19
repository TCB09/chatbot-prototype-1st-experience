const sendButton = document.getElementById('sendButton');
const userInput = document.getElementById('userInput');
const chatBox = document.querySelector('.chat-box');
const chatHistory = document.getElementById('chatHistory');
const clearHistoryButton = document.getElementById('clearHistoryButton');

let isFirstInputSaved = false;

// Fungsi untuk menambah pesan ke dalam chat box
function addMessage(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    messageElement.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
    messageElement.textContent = message;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Fungsi untuk mengetik pesan secara bertahap di chat box
function typeMessage(message, callback) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', 'bot-message');
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;

    let index = 0;
    const typingInterval = setInterval(() => {
        if (index < message.length) {
            messageElement.textContent += message[index];
            index++;
        } else {
            clearInterval(typingInterval);
            if (callback) callback();
        }
    }, 50);
}

// Fungsi untuk menyimpan input pertama ke dalam localStorage
function saveFirstInput(content) {
    if (!isFirstInputSaved) {
        const chatHistoryData = JSON.parse(localStorage.getItem('chatHistory')) || [];
        chatHistoryData.push(content);
        localStorage.setItem('chatHistory', JSON.stringify(chatHistoryData));
        const historyItem = document.createElement('div');
        historyItem.classList.add('history-item');
        historyItem.textContent = content;
        chatHistory.appendChild(historyItem);
        isFirstInputSaved = true;
    }
}

// Fungsi untuk memuat riwayat chat dari localStorage
function loadChatHistory() {
    const chatHistoryData = JSON.parse(localStorage.getItem('chatHistory')) || [];
    chatHistoryData.forEach(content => {
        const historyItem = document.createElement('div');
        historyItem.classList.add('history-item');
        historyItem.textContent = content;
        chatHistory.appendChild(historyItem);
    });
}

// Fungsi untuk mengirimkan pesan dan memproses jawaban dari backend
function sendMessage() {
    const message = userInput.value.trim();
    if (message) {
        addMessage(message, 'user');
        saveFirstInput(message);
        userInput.value = '';

        // Kirim pertanyaan ke backend Flask
        fetch('http://127.0.0.1:5000/ask', { // Pastikan URL sesuai dengan backend
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: message }) // Key JSON adalah "query"
        })
        .then(response => response.json())
        .then(data => {
            if (data.answer) {
                typeMessage(data.answer, () => {
                    if (data.follow_up) {
                        typeMessage(data.follow_up); // Tampilkan tindak lanjut jika tersedia
                    }
                });
            } else if (data.error) {
                typeMessage(`Error: ${data.error}`);
            } else {
                typeMessage('Tidak ada jawaban tersedia.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            typeMessage('Terjadi kesalahan saat menghubungi server.');
        });
    }
}

// Fungsi untuk menghapus riwayat chat dari localStorage
function clearChatHistory() {
    localStorage.removeItem('chatHistory');
    chatHistory.innerHTML = '';
}

sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

clearHistoryButton.addEventListener('click', clearChatHistory);

document.addEventListener('DOMContentLoaded', function() {
    loadChatHistory();
    const welcomeModal = document.getElementById('welcomeModal');
    const startChatButton = document.getElementById('startChatButton');
    welcomeModal.style.display = 'flex';
    startChatButton.addEventListener('click', function() {
        welcomeModal.style.display = 'none';
        typeMessage('Halo, ada yang bisa saya bantu?');
    });
});
