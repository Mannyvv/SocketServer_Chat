import socketserver
import sys
from util.request import Request
import os
import json
import mimetypes
from pymongo import MongoClient
import uuid
import datetime
import bcrypt
import hashlib
import base64
client = MongoClient('localhost', 27017)
db = client['SocketServer_DB']
chat_history_collection = db['chat_history']
users_collections = db['users']



class MyTCPHandler(socketserver.StreamRequestHandler):

     

    active_connections = []
    def handle(self):
        header_data = b''
        while True:
            #Note: strip() is used to remove the newline character at the end of the line
            line = self.rfile.readline()
            if line == b'\r\n':
                break
            header_data += line
        
        content_length = 0 
        for line in header_data.split(b'\r\n'):
            if line.startswith(b'Content-Length: '):
                content_length = int(line.split(b'Content-Length: ')[1])
                break
        body_data = b''

        if content_length > 0:
            body_data = self.rfile.read(content_length)

        # body_data = b'This is the body'
        request = Request(header_data, body_data)
        # print("Method: ", request.method)
        # print("URL: ", request.url)
        # print(request.protocol)
        # print("Headers: ", request.headers)
        # print("Body: ", request.body)

        # self.wfile.write(b"HTTP/1.1 200 OK\r\n")

        
        if request.url == b'/':
            self.serve_homepage(request.headers)
        elif request.url.startswith(b'/public/'):
            self.serve_file(request.url.strip(b'/').decode('utf-8'))
        elif request.url == b'/send-message':
            self.handle_send_message(request)
        elif request.url == b'/get-chat-history':
            self.handle_chat_history(request)
        elif request.url == b'/register-user':
            self.handle_register_user(request.body)
        elif request.url == b'/login-user':
            self.handle_login(request.body)
        elif request.url == b'/logout-user':
            self.logout()
        elif request.url == b'/image-upload':
            self.handle_image_upload(request.get_image_data(), request.headers) 
        elif request.url == b'/websocket':
            self.handle_websocket(request)

        
            

    def serve_homepage(self, headers):
        auth_token = self.get_auth_token(headers)
        if auth_token:
            print("User is logged in")
            user_image_url = users_collections.find_one({"auth_token" : auth_token}, {'image_url': 1, '_id':0})
            print("User Image URL: ", user_image_url)
            if os.path.exists(user_image_url["image_url"]):
                print("Image exists")
                with open("public/index.html", 'rb') as file:
                    print("Reading file")
                    content = file.read()
                    user_profile_image = f'<img id="user-image"  src=/{user_image_url["image_url"]} onclick ="upLoadImage()" alt="User Image" />'
                    updated_content = content.replace(b'<!-- Image Element -->', user_profile_image.encode('utf-8'))
                print("served homepage with image")
                return self.send_response(updated_content,'text/html', len(updated_content) )
                

            
        # with open('public/index.html', )
        else:
            print("User is not logged in")
            return self.serve_file('public/index.html')


    def serve_file(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                content = file.read()
                mime_type, _ = mimetypes.guess_type(file_path)
                content_length = len(content)
                # content_length = os.path.getsize(file_path)
                self.send_response(content, mime_type, content_length)

    def handle_send_message(self, request: Request):
        data = json.loads(request.body.decode('utf-8'))
        # cookies = self.get_cookies(request.headers)

        # print("Cookie type: ", type(cookies))
        #Add random id to the message

        # cookies = self.get_cookies(request.headers)
        # user_auth_token = cookies.get('auth_token', 0)
        user_auth_token = self.get_auth_token(request.headers)
        if user_auth_token:
            user_data = users_collections.find_one({'auth_token': user_auth_token}, {'user_id' :1,'username': 1 ,'_id':0})
            data['user_id'] = user_data['user_id']  
            data['username'] = user_data['username']
        else:
            data['user_id'] = "Guest"
            data['username'] = "Guest"
            
        data['message_id'] = str(uuid.uuid4())
        data['timestamp'] = datetime.datetime.now().isoformat()
        
       
        # There was a strange bug when I used the "data" variable, to insert into the database
        # and perform json.dumps(data). Had to use .copy() to fix the issue.
        new_data = data.copy()
        new_data["date"] = datetime.datetime.now().strftime("%m-%d-%Y")
        new_data["time"] = datetime.datetime.now().strftime("%I:%M %p")

        try:
            chat_history_collection.insert_one(data)
        except Exception as e:
            print("Error inserting message:", e)
            return

        json_data = json.dumps(new_data)
        content_length = len(json_data)
        self.send_response(json_data.encode(), "application/json", content_length)


    def handle_chat_history(self, request):
        chat_messages = list(chat_history_collection.find({}, {"_id": 0}))
        json_data = json.dumps(chat_messages)
        content_length = len(json_data)
        self.send_response(json_data.encode(), "application/json", content_length)
    
    def handle_register_user(self, body):
        user_register_data = self.extract_submissions(body)

        if not user_register_data.get('r-username') or not user_register_data.get('r-password'):
            return self.send_400("Username and password are required")

        user_document = {
            'user_id': str(uuid.uuid4()),
            'username': user_register_data['r-username'],
            'password': self.hash_password(user_register_data['r-password']),
            'image_url': 'public/profile_pics/no_image.jpg'
        }

        users_collections.insert_one(user_document)
        return self.redirect('/')
    
    def handle_login(self, body):
        user_login_data = self.extract_submissions(body)

        if not user_login_data.get('username') or not user_login_data.get('password'):
            return self.send_400("Username and password are required")

        user_data= users_collections.find_one({'username': user_login_data['username']}, {'password': 1, 'user_id':1, '_id': 0})
        
        if not user_data:
            return self.send_400("Invalid username or password")
        
        if bcrypt.checkpw(user_login_data['password'].encode(), user_data['password'].encode()):
            auth_token = str(uuid.uuid4())
            users_collections.update_one({'username': user_login_data['username']}, {'$set': {'auth_token':auth_token}})
            user_cookie = { "auth_token": auth_token, "user_id": user_data['user_id']}
            # auth_token_cookie = f'auth_token={auth_token}'
        return self.redirect('/', user_cookie )

    def handle_image_upload(self, image_data, headers):
        #might change get_cookie result to binary 
        # auth_token = self.get_cookies(headers).get('auth_token', 0)
        auth_token = self.get_auth_token(headers)
        if auth_token:
            user_data = users_collections.find_one({'auth_token': auth_token})
            path = "./public/profile_pics"

            if not os.path.exists(path):
                self.send_400({"message":"Folder not found"})

            image_path = "public/profile_pics/user_image_" + user_data["username"]+ ".jpg"


            with open(image_path, 'wb') as file:
                file.write(image_data)
            users_collections.update_one({"username": user_data["username"]}, {"$set":{"image_url" : image_path}})

        # return self.redirect('/')
        return self.send_200({"message": "Image uploaded successfully"})
    
    def handle_websocket(self, request):

        headers = request.headers
        wb_handshake = self.websocket_handshake(headers)
        if wb_handshake:
            self.active_connections.append(self)

            # #Not sure why I'm not reading out the bytes in the frames
            # print("Active connections: ", len(self.active_connections))
            # self.wfile.write(b"Connected")
            # while True:
            #     try:
            #         message = self.rfile.read(1024)
            #         print("Message: ", message)
            #         for connection in self.active_connections:
            #             if connection != self:
            #                 connection.wfile.write(message)
            #     except Exception as e:
            #         print("Error: ", e)
            #         self.active_connections.remove(self)
            #         break
            try:
                while True:
                    try:
                        frame_data= self.read_ws_frame()
                        if frame_data is None:
                            break
                        opcode, masking_key, payload_data = frame_data
                        unmasked_payload_data = self.parse_ws_frame(masking_key,payload_data)
                        payload = json.loads(unmasked_payload_data)
                        request.body = payload
                        self.process_payload(request)
                    except Exception as e:
                        print(f"Exception in frame processing: {e}")
                        continue
            except Exception as e:
                print(f"Exception in WebSocket connection handling: {e}")

            finally:
                self.cleanup_connection()
                if self in self.active_connections:
                    self.active_connections.remove(self)
                

    def read_ws_frame(self):

        frame_header = self.rfile.read(2)

        if not frame_header or len(frame_header) < 2:
            return None
        
        first_byte, second_byte = frame_header
        fin_bit = (first_byte & 0x80 ) == 0x80
        opcode = first_byte & 0x0F

        #0x00: Continuation Frame, 0x01: Text Frame(UTF-8 text data), 0x08: Close frame
        if opcode not in [0x00, 0x01, 0x08]:
            return None

        rsv = (first_byte & 0x70)
        if rsv != 0 :
            print("RSV bits not 000")
            return None

        if opcode == 0x8:
            return None

        mask_bit = second_byte & 0x80

        #if 0-125 then payload_length already set
        payload_length = second_byte & 0x7F

        if payload_length == 126:
            payload_length_bytes = self.rfile.read(2)
            #payload_length is a 16 bit integer
            payload_length = (payload_length_bytes[0] << 8) + payload_length_bytes[1]
        elif payload_length == 127:
            payload_length_bytes = self.rfile.read(8)
            payload_length = 0
            #payload_length is a 64 bit integer
            for byte in payload_length_bytes:
                payload_length = (payload_length << 8) + byte
        
        masking_key = None
        if mask_bit:
            masking_key = self.rfile.read(4)

        payload_data = b""
        if payload_length > 0:
            payload_data = self.rfile.read(payload_length)

        return opcode, masking_key, payload_data

    def parse_ws_frame(self, masking_key, payload_data):
        if masking_key:
            unmasked_payload = bytearray()
            for i in range(len(payload_data)):
                unmasked_payload.append(payload_data[i] ^ masking_key[i % 4])
            payload_data = unmasked_payload
        return payload_data.decode()
    
    def process_payload(self, request):
        if request.body.get('messageType') == 'chatMessage':
            self.handle_send_message(request)
    
    def cleanup_connection(self):
        if self in MyTCPHandler.active_connections:
            MyTCPHandler.active_connections.remove(self)





    def websocket_handshake(self, headers):
        #  TODO: Might have to  check host and origin in headers
        if b'Upgrade' in headers and headers[b'Upgrade'] == b'websocket':
            key = headers[b'Sec-WebSocket-Key']
            GUIID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            hash_key = key + GUIID
            response_key = base64.b64encode(hashlib.sha1(hash_key).digest())
            self.wfile.write(b"HTTP/1.1 101 Switching Protocols\r\n")
            self.wfile.write(b"Upgrade: websocket\r\n")
            self.wfile.write(b"Connection: Upgrade\r\n")
            self.wfile.write(f"Sec-WebSocket-Accept: {response_key.decode()}\r\n".encode())
            return True
        else:
            self.send_400("Invalid request")
            return False



    def extract_submissions(self, body):
        user_data = {}
        parts = body.split(b'&')
        for part in parts:
            key, value = part.split(b'=')
            user_data[key.decode('utf-8')] = value.decode('utf-8')

        return user_data



        # b'r-username=gd&r-password=dfgfd'

    def send_response(self, content, mime_type, content_length):
        #might use self.request.sendall() instead of self.wfile.write()
        self.wfile.write(b"HTTP/1.1 200 OK\r\n")
        self.wfile.write(f"Content-Type: {mime_type}\r\n".encode('utf-8'))
        self.wfile.write(f"Content-Length: {content_length}\r\n".encode('utf-8'))
        self.wfile.write(b"\r\n")
        self.wfile.write(content)
        self.wfile.write(b"\r\n")

    
    # def send_cookies(self, cookies: dict):
    #     cookie_string = ""
    #     for key, value in cookies.items():
    #         cookie_string += f"{key}={value}; "
    #     self.wfile.write(f"Set-Cookie: {cookie_string}\r\n".encode('utf-8'))
    def redirect(self, url, cookie=None):
        self.wfile.write(b"HTTP/1.1 302 Found\r\n")
        self.wfile.write(f"Location: {url}\r\n".encode('utf-8'))
        if cookie:
            self.wfile.write(f'Set-Cookie: auth_token={cookie["auth_token"]}; Path=/; HttpOnly; Max-Age=3600\r\n'.encode('utf-8'))
            self.wfile.write(f'Set-Cookie: loggedIn={cookie["user_id"]}; Path=/; Max-Age=3600\r\n'.encode('utf-8'))
        self.wfile.write(b"\r\n")

    def logout(self):
        print("Logging out")
        self.wfile.write(b"HTTP/1.1 303 See Other\r\n")
        self.wfile.write(b"Location: /\r\n")
        self.wfile.write(b"Set-Cookie: loggedIn=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;\r\n")
        self.wfile.write(b"Set-Cookie: auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;\r\n")
        self.wfile.write(b"\r\n")
        # self.redirect('/')

    def send_200(self, content):
        self.wfile.write(b"HTTP/1.1 200 OK\r\n")
        self.wfile.write(b"Content-Type: application/json\r\n")
        self.wfile.write(f"Content-Length: {len(json.dumps(content))}\r\n".encode('utf-8'))
        self.wfile.write(b"\r\n")
        self.wfile.write(json.dumps(content).encode('utf-8'))
        self.wfile.write(b"\r\n")

    def send_400(self, message = None):
        self.wfile.write(b"HTTP/1.1 400 Bad Request\r\n")
        if message:
            self.wfile.write(b"Content-Type: text/html\r\n")
            self.wfile.write(f"Content-Length: {len(message)}\r\n".encode('utf-8'))
            self.wfile.write(b"\r\n")
            self.wfile.write(message.encode('utf-8'))
        self.wfile.write(b"\r\n")

    def get_cookies(self, headers) -> dict:
       
        cookie_obj = {}
        if b'Cookie' not in headers:
            return cookie_obj
        cookies = headers[b'Cookie'].decode('utf-8')
        # for header in headers:
        #     if header.startswith(b'Cookie: '):
        #         cookie_string = header.split(b'Cookie: ')[1].decode('utf-8')
        #         cookie_strings = cookie_string.split('; ')
        #         for cookie in cookie_strings:
        #             key, value = cookie.split('=')
        #             cookies[key] = value
        cookies_strings = cookies.split('; ')
        for cookie in cookies_strings:
            key, value = cookie.split('=')
            cookie_obj[key] = value
        return cookie_obj 
    
    def get_auth_token(self, headers) -> str:
        cookies = self.get_cookies(headers)
        if cookies.get('auth_token', 0):
            return cookies['auth_token']
        return None


    def hash_password(self, password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8080

    socketserver.ThreadingTCPServer.allow_reuse_address = True

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)

    print("Listening on port " + str(port))
    sys.stdout.flush()
    sys.stderr.flush()

    server.serve_forever()
