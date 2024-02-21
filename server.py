import socketserver
import sys
from util.request import Request
import os
import json
import mimetypes
from pymongo import MongoClient
import uuid
import datetime

client = MongoClient('localhost', 27017)
db = client['SocketServer_DB']
chat_history_collection = db['chat_history']



class MyTCPHandler(socketserver.StreamRequestHandler):

    

    active_connections = []
    def handle(self):
        header_data = b''
        while True:
            #Note: strip() is used to remove the newline character at the end of the line
            line = self.rfile.readline()
            
            if not line or line == b'\r\n':
                break
            header_data += line
        
        content_length = 0 
        
        for line in header_data.split(b'\r\n'):
            # print(line.decode('utf-8'))
            if line.startswith(b'Content-Length: '):
                content_length = int(line.split(b'Content-Length: ')[1])
                break
        body_data = b''

        if content_length > 0:
            body_data = self.rfile.read(content_length)
            # print("Body:", body_data)

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

            # self.send_200({"message": "Message sent"})
            

    def serve_homepage(self, headers):
        self.serve_file('public/index.html')


    def serve_file(self, file_path):
        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                content = file.read()
                mime_type, _ = mimetypes.guess_type(file_path)
                content_length = len(content)
                # content_length = os.path.getsize(file_path)
                self.send_response(content, mime_type, content_length)

    def handle_send_message(self, request):
        data = json.loads(request.body.decode('utf-8'))
        # cookies = self.get_cookies(request.headers)

        # print("Cookie type: ", type(cookies))
        #Add random id to the message
        data['message_id'] = str(uuid.uuid4())
        data['timestamp'] = datetime.datetime.now().isoformat()
        
       
        # There was a strange bug when I used "data" varaible to insert into the database
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

    def send_200(self, content):
        self.wfile.write(b"HTTP/1.1 200 OK\r\n")
        self.wfile.write(b"Content-Type: application/json\r\n")
        self.wfile.write(f"Content-Length: {len(json.dumps(content))}\r\n".encode('utf-8'))
        self.wfile.write(b"\r\n")
        self.wfile.write(json.dumps(content).encode('utf-8'))
        self.wfile.write(b"\r\n")

    def get_cookies(self, headers):
       
        cookie_obj = {}
        
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
       
if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8080

    socketserver.ThreadingTCPServer.allow_reuse_address = True

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)

    print("Listening on port " + str(port))
    sys.stdout.flush()
    sys.stderr.flush()

    server.serve_forever()
