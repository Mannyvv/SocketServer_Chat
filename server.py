import socketserver
import sys
from util.request import Request
import os
import mimetypes


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
        
        # for line in header_data.split(b'\r\n'):
        #     print(line.decode('utf-8'))
        #     if line.startswith(b'Content-Length: '):
        #         content_length = int(line.split(b'Content-Length: ')[1])
        #         break
        # body = b''

        # if content_length > 0:
        #     body = self.rfile.read(content_length)
        #     print("Body:", body)
        # request = Request(header_data + b'\r\n\r\n' + body)
        body_data = b'This is the body'
        request = Request(header_data, body_data)
        print(request.method)
        print(request.url)
        print(request.protocol)
        # print(request.headers)
        # print(request.body)

        # self.wfile.write(b"HTTP/1.1 200 OK\r\n")

        
        if request.url == b'/':
            self.serve_homepage(request.headers)
        elif request.url.startswith(b'/public/'):
            self.serve_file(request.url.strip(b'/').decode('utf-8'))
            

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

    def send_response(self, content, mime_type, content_length):
        #might use self.request.sendall() instead of self.wfile.write()
        self.wfile.write(b"HTTP/1.1 200 OK\r\n")
        self.wfile.write(f"Content-Type: {mime_type}\r\n".encode('utf-8'))
        self.wfile.write(f"Content-Length: {content_length}\r\n".encode('utf-8'))
        self.wfile.write(b"\r\n")
        self.wfile.write(content)
        self.wfile.write(b"\r\n")


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8080

    socketserver.ThreadingTCPServer.allow_reuse_address = True

    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)

    print("Listening on port " + str(port))
    sys.stdout.flush()
    sys.stderr.flush()

    server.serve_forever()
