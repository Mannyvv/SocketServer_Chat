
let username = "Guest";
let user_id = null;
let webSocket = null;

const getCookies = () => {
    const cookies = document.cookie.split(';');
    const cookieObj = {};
    // console.log(cookies)

    cookies.forEach((cookie) => {
        const [key, value] = cookie.split('=');
        cookieObj[key] = value;
    })
    // decodeURIComponent() ?
    return cookieObj; 
}

// const startWebSocket = () => {
//     // const webSocket = new WebSocket('ws://localhost:8080');
//     // webSocket = new WebSocket('ws://' + window.location.host + '/websocket');
//     webSocket = new WebSocket(`ws://localhost:${PORT}/websocket`);

//     // webSocket.onopen = () => {
//     //     console.log('WebSocket Client Connected');
//     // };

//     webSocket.onmessage = (ws_message) => {
//         const message = JSON.parse(ws_message.data);
//         const messageType = message.messageType

//         if (messageType === 'chatMessage') {
//             addToChatWindow(message);
//         }else{
//             console.log("Issue with message type")
//         }
//     }

//     // webSocket.onopen = () => {
//     //     console.log("Websocket connection established")
//     // }

//     webSocket.addEventListener('open', function (event) {
//         console.log('WebSocket connection established');
//     });

// }
const registerForm = () => {

    //Not sure if I should use this or stay with the form subsission
    // const username = document.getElementById('login-username').value;
    // const password = document.getElementById('login-password').value;
    // fetch('/login', {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json'
    //     },
    //     body: JSON.stringify({ username: username, password: password })
    // })
    //     .then((response) => {
    //         response.json().then((data) => {
    //             if (data.auth_token) {
    //                 document.cookie = `auth_token=${data.auth_token}`;
    //                 document.cookie = `username=${username}`;
    //                 location.reload();
    //             }
    //         })
    //     })
    //     .catch(error => {
    //         console.error('Error:', error);
    //     });
    alert("Successfully Registered") 
}

const loginForm = () => {
    // document.getElementById('logout-holder').hidden = false;
    

}

const sendMessage = () => {
    const message = document.getElementById('text-box').value;

    const wb_message = {
        messageType: 'chatMessage',
        message: message,
        username: username
    }
    
    // webSocket.send(JSON.stringify(wb_message))

    fetch('/send-message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        // body: JSON.stringify({ username: username, message: message })
        body: JSON.stringify(wb_message)
    })
        .then((response) => {
            // When sending a message, the response
            // will be the same message sent, but will go through validations
            // before getting here
            response.json().then((data) => {
                addToChatWindow(data);
            })

            console.log("Message Sent")
        })
        .catch(error => {
            console.error('Error:', error);
        });
    // Clear the input box
    document.getElementById('text-box').value = '';
    // getChatHistory();



}

const addToChatWindow = (data) => {
    const chatWindowBody = document.getElementById('chat-window-body');
    const newMessage = document.createElement('li');
    newMessage.classList.add('chat-window-item');
    newMessage.classList.add('open-sans-chat');
    newMessage.setAttribute('id', data.message_id);
    if (data.user_id === user_id) {
        newMessage.classList.add('logged-user-message');
    }
    newMessage.innerHTML = `<p>X</p>${data.username}: ${data.message}`
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
    // startWebSocket();
    cookies = getCookies();
    
    if (cookies.loggedIn) {
        document.getElementById('user-image').style.display = 'block'
        document.getElementById('logout-holder').style.display = 'block';
        document.getElementById('register-form').style.display = 'none';
        document.getElementById('login-form').style.display = 'none';
        user_id = cookies.loggedIn;
    }else{
        document.getElementById('register-form').style.display = 'block';
        document.getElementById('login-form').style.display = 'block';
    }
    setInterval(getChatHistory, 2000);

}

const upLoadImage = () => {
    
    const userImageUpload = document.getElementById('user-image-upload');
    userImageUpload.click();
    userImageUpload.addEventListener('change',(event) => {
        const imageFile = event.target.files[0];
        if (imageFile){
            sendImage(imageFile)

        }
    })
    


}




const sendImage = (imageFile) => {
    const formData = new FormData();
    formData.append('image', imageFile);

    fetch('/image-upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            console.log('Image uploaded successfully');
            location.reload();

        } else {
            console.error('Failed to upload image');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
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


// document.getElementById("text-box-button").addEventListener('keyup', (event) => {
//     console.log(event.key);
//     if (event.key === 'Enter') {
//         sendMessage();
//     }
// });


const logout = () => {
    fetch('/logout-user', {
        method: 'POST',
        
    }).then((response) => {
            console.log("Logged Out")
            window.location.reload();


        })
        document.getElementById('logout-holder').style.display = 'none';
        document.getElementById('user-image').style.display = 'none'
        document.getElementById('register-form').style.display = 'block';
        document.getElementById('login-form').style.display = 'block';

    
}

