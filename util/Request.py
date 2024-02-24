

class Request:
    def __init__(self, header_data: bytes, body_data: bytes):
        '''
        Takes in the request data(bytes) and parses it into the request object
        Args:
            request_data (bytes): The raw request data
        Derived attributes:
            self.method (bytes): The CRUD method of the request
            self.url (bytes): The URL of the request
            self.protocol (bytes): The protocol of the request
            self.headers (dict): The headers of the request
            self.body (bytes): The body of the request
        '''
        # print("header_data", header_data)
        self.method, self.url, self.protocol = self.get_method_url_protocol(header_data)
        self.headers = self.get_headers(header_data)
        self.body = body_data

        #Both methods could be made into one method, but I think 
        #it's better to keep them separate for readability
    def get_method_url_protocol(self, header_data):
        
        header_data_split = header_data.split(b'\r\n')
        if len(header_data_split[0].split(b' ')) < 3:
            return None, None, None
        #Obtains CRUD method, URL, and protocol from first line e.g GET / HTTP/1.1
        method, url, protocol = header_data_split[0].split(b' ')
        return method, url, protocol
    def get_headers(self, header_data):
        #Obtains headers from the request data after first line
        header_data_split = header_data.split(b'\r\n')
        # print("header_data_split", header_data_split)
        headers = {}
        #Obtains headers and stores them as attributes, skipping the first line
        #and the last line
        for header in header_data_split[1:-1]:
            key, value = header.split(b': ')
            headers[key] = value
        
        return headers
    def get_image_data(self):

        content_type = self.headers.get(b'Content-Type', 0)

        if not content_type or not b'multipart/form-data' in content_type:
            print("No multipart/form-data")
            return None
        
        boundary = content_type.split(b'boundary=')[1]

        parts = self.body.split(b'--' + boundary)
        print(parts[0])
        # print(parts[1])
        print(parts[2])
        image_data = parts[1].split(b'\r\n\r\n')[1]
        
        print(len(image_data))
        if image_data:
            return image_data
            
        


    
    
  
   

    # def __str__(self):
    #     return f"Request(method={self.method}, url={self.url}, headers={self.headers}, body={self.body})"