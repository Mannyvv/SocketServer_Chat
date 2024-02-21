
let username = "Guest";
const getCookies = () => {
    const cookies = document.cookie.split(';');
    const cookieObj = {};

    cookies.forEach((cookie) => {
        const [key, value] = cookie.split('=');
        cookieObj[key] = value;
    })
    // decodeURIComponent() ?
    return cookieObj;
}

const sendMessage = () => {
    const message = document.getElementById('text-box').value;
    cookies = getCookies();
    if (cookies.auth_token) {
        username = "Logged User"
    }
    fetch('/send-message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username: username, message: message })
    })
        .then((response) => {
            // When sending a message, the response
            // will be the same message sent, but will go through validations
            // before getting here
            response.json().then((data) => {
                addToChatWindow(data);
            })
            // const chatWindowBody = document.getElementById('chat-window-body');
            // chatWindowBody.innerHTML = '';
            // getChatHistory();
            console.log("Message Sent")
        })
        .catch(error => {
            console.error('Error:', error);
        });
    // Clear the input box
    document.getElementById('text-box').value = '';
    getChatHistory();



}

const addToChatWindow = (data) => {
    const chatWindowBody = document.getElementById('chat-window-body');
    const newMessage = document.createElement('li');
    newMessage.classList.add('chat-window-item');
    if (getCookies().auth_token) {
        newMessage.classList.add('logged-user-message');
    }
    newMessage.innerHTML = `${data.username}: ${data.message}`
    chatWindowBody.appendChild(newMessage);
    chatWindowBody.lastChild.scrollIntoView();


}

const onLoad = () => {
    getChatHistory();
    document.getElementById("text-box").addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
    setInterval(getChatHistory, 2000);

}


const getChatHistory = () => {

    

    fetch('/get-chat-history', {
        method: 'GET',
        headers: {
            'Content-Type': 'applcation/json'
        }
    }).then((response) => {
        response.json().then((messages_data) => {
            const chatWindowBody = document.getElementById('chat-window-body');
            chatWindowBody.innerHTML = '';
            messages_data.forEach((message_data) => {
                addToChatWindow(message_data);
            })
        })
    })
}


document.getElementById("text-box-button").addEventListener('keyup', (event) => {
    console.log(event.key);
    if (event.key === 'Enter') {
        sendMessage();
    }
});