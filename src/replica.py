import jsonschema.exceptions
from msg_utils import *
from core import send_chunked, recvall
import random
import jsonschema
import socket, threading
import sys

TEST_CONNECTION_LIST = [('127.0.0.1', 5001), ('127.0.0.1', 5002), ('127.0.0.1', 5003)]

JSON_SCHEMA = {
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "parent": {
        "type": "number"
      },
      "id": {
        "type": "number"
      },
      "content": {
        "type": "string"
      },
      "meta": {
        "type": "object",
        "properties": {
          "title": {
            "type": "string"
          },
          "user": {
            "type": "string"
          }
        }
      }
    },
    "required": [
      "parent",
      "id",
      "content",
      "meta"
    ]
  }
}

# Will raise error if not a valid array of post objects...
def validate_payload_schema(msg_payload):
    jsonschema.validate(instance=msg_payload, schema=JSON_SCHEMA)


class Replica:
    def __init__(self, replica_id, connections, mode='sequential'):
        self.replica_id = int(replica_id)
        self.connections = connections      #list of (addr, port) tuples for all replicas
        self.consistency_mode = mode        #string that describes mode
        self.coordinator_index = 0
        self.data = {}                      #dict to hold all post data, metadata, etc.
        self.article_id = 0
        self.mode = mode

    #Sets coordinator flag
    @property
    def coordinator_flag(self):
        return self.replica_id == self.coordinator_index
    
    # Forward messages and wait to recevie ack
    def forward_to_coordinator(self, message):
        coord_host, coord_port = self.connections[self.coordinator_index]

        coord_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        coord_socket.connect((coord_host, coord_port))
        coord_socket.sendall(message)
        
        # TODO: Don't
        # return_message = coord_socket.recv(1000)
        return_message = read(coord_socket)

        length = pack(">Q", len(return_message))
        return length+return_message
    
    # Forward message and don't wait to receive ack
    def send_to_coordinator(self, message):
        coord_host, coord_port = self.connections[0]
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((coord_host, coord_port))
            s.sendall(message.encode('utf-8'))

   

    #Function that handles incoming messages and acts on consistency logic. This links communication logic to consistency logic
    def process_requests(self, conn, addr):
        #TODO Here we will read with JSON library and parse message. We may get rid of this while loop
        # while True:
            # message = conn.recv(1024).decode('utf-8')
            # print(message)
            # request_type_bytes = conn.recv(8)

        try:
            req_enum, = unpack('>Q', conn.recv(8))
            req_enum = int(req_enum)
            nbytes_msg = conn.recv(8)
            if nbytes_msg != b'': # Case for a disconnecting Client socket
                msglen, = unpack('>Q', nbytes_msg)
            print(msglen)
            print("Oh snap")
            message = recvall(conn, int(msglen))

            length = pack('>Q', len(message))
            request_type = pack('>Q', int(req_enum))

            packed_message = bytearray(request_type+length+message)

            print(message)
            print(packed_message)

            # if not req_enum:
            #     break
            if req_enum == int(REQUEST_TYPE.POST):
                self.execute_post(conn, packed_message)
            elif req_enum == int(REQUEST_TYPE.READ):
                self.execute_read(conn, packed_message)
            elif req_enum == 'choose':
                self.execute_choose(conn, packed_message)
            elif req_enum == int(REQUEST_TYPE.r_WRITE):
                self.execute_write(conn, packed_message)
            elif req_enum == int(REQUEST_TYPE.r_READ):
                self.execute_read_data(conn)
            else:
                print('unindentified req_enum type')
            conn.close()
        except Exception as e:
            print(e)

            conn.close()

    def execute_read(self, conn, message):
        if self.replica_id != self.coordinator_index:
            #Forward this to the coordinator
            print("Forwarding Post to coordinator")

            return_message = self.forward_to_coordinator(message)
            conn.sendall(return_message)
        else:
            self.execute_read_coordinator(conn, message)
    
    def execute_read_coordinator(self, conn, message):
        print("Executing post as coordinator")
        if self.mode == 'sequential':
            self.execute_read_sequential(conn, message)
        elif self.mode == 'quorum':
            self.execute_read_quorum(conn, message)
        elif self.mode == 'read_your_write':
            self.execute_read_read_your_write(conn, message)
        else:
            print(f"Unknown mode type: {self.mode}")

    def execute_read_sequential(self, conn, message):
        pass

    def execute_read_quorum(self, conn, message):
        print("Hey, its me, coordinator, I'm reading again...")
        read_replicas = random.sample(range(0,len(self.connections)), len(self.connections)//2 + 1)

        request_type = pack('>Q', int(REQUEST_TYPE.r_READ))
        message[:8] = request_type

        print(read_replicas)
        data_list = []
        for replica in read_replicas:
            
            target_host, target_port = self.connections[replica]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((target_host, target_port))
                s.sendall(message)
                data = json.loads(read(s).decode('utf-8'))
                
                if data:
                    data = {int(key):value for key,value in data.items()}

                    data_list.append(data)
                    
                print("Received Data from Read Request")
        
        if data_list:
            print(f"Data List: {data_list}")
            max_list = [max(list(d.keys())) for d in data_list]
            print(f"Max List: {max_list}")
            payload = data_list[max_list.index(max(max_list))]
            payload = json.dumps(payload).encode('utf-8')
            print(f"Payload after dumps: {payload}")
            length = pack('>Q', len(payload))
            
            conn.sendall(length+payload)

        else:
            length = pack('>Q', len(b"Nuthin"))
            conn.sendall(length + b"Nuthin")

    def execute_read_read_your_write(self, conn, message):
        pass

    def execute_post(self, conn, message):
        print("Executing Post")
        if self.replica_id != self.coordinator_index:
            #Forward this to the coordinator
            print("Forwarding Post to coordinator")

            return_message = self.forward_to_coordinator(message)
            conn.sendall(return_message)
        else:
            self.execute_post_coordinator(conn, message)
            
    # Picks the post function based on mode
    def execute_post_coordinator(self, conn, message):
        print("Executing post as coordinator")

        request_enum = message[:8]
        

        new_article = json.loads(message[16:].decode('utf-8'))
        new_article['id'] = self.get_article_id()
        payload = json.dumps(new_article).encode('utf-8')

        length = pack('>Q', len(payload))

        updated_message = request_enum+length+payload


        if self.mode == 'sequential':
            self.execute_post_sequential(conn, updated_message)
        elif self.mode == 'quorum':
            self.execute_post_quorum(conn, updated_message)
        elif self.mode == 'read_your_write':
            self.execute_post_read_your_write(conn, updated_message)
        else:
            print(f"Unknown mode type: {self.mode}")
    
    def execute_post_sequential(self, conn, message):
        pass
    
    def execute_post_quorum(self, conn, message):
        print("Hey, its me, coordinator, I'm posting again...")
        post_replicas = random.sample(range(0,len(self.connections)), len(self.connections)//2 + 1)

        request_type = pack('>Q', int(REQUEST_TYPE.r_WRITE))
        message[:8] = request_type

        print(post_replicas)
        for replica in post_replicas:
            
            target_host, target_port = self.connections[replica]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((target_host, target_port))
                s.sendall(message)
                action_message = s.recv(1000)
                print("Received Ack from Write Request")
                
        conn.sendall(action_message)
    
    def execute_post_read_your_write(self, conn, message):
        pass
    
    def execute_choose(self, conn, message):
        if self.replica_id != self.coordinator_index:
            #Forward this to the coordinator
            return_message = self.forward_to_coordinator(message)
            conn.sendall(return_message.encode('utf-8'))
        else:
            self.execute_choose_coordinator(self, conn, message)

    def execute_choose_coordinator(self, conn, message):
        if self.mode == 'sequential':
            self.execute_choose_sequential(conn, message)
        elif self.mode == 'quorum':
            self.execute_choose_quorum(conn, message)
        elif self.mode == 'read_your_write':
            self.execute_choose_read_your_write(conn, message)
        else:
            print(f"Unknown mode type: {self.mode}")

    # Contacting _any_ replica should always return the same sequence of data
    def execute_choose_sequential(self, conn, message):
        print("Hey, its me, coordinator, I'm choosing again.")
        post_replicas = len(self.connections)
        for replica in post_replicas:
            target_host, target_port = self.connections[replica]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((target_host, target_port))
                s.sendall('read_data'.encode('utf-8'))
                action_message = str(s.recv(1000))
            
        conn.sendall(action_message.encode('utf-8'))
    
    def execute_choose_read_your_wrtie(self, conn, message):
        pass
    
    # A subset W > N/2 of replicas are written to at random
    def execute_choose_quorum(self, conn, message):
        print("Hey, its me, coordinator, I'm choosing again.")
        post_replicas = random.sample(range(0,len(self.connections)), 2)
        for replica in post_replicas:
            target_host, target_port = self.connections[replica]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((target_host, target_port))
                s.sendall('read_data'.encode('utf-8'))
                action_message = str(s.recv(1000))
            
        conn.sendall(action_message.encode('utf-8'))

    def execute_write(self, conn, message):
        print('Received WRITE from coordinator')

        req_enum, = unpack('>Q', message[:8])
        req_enum = int(req_enum)
        # nbytes_msg = message[8:16] TODO Toss this
        message = json.loads(message[16:].decode('utf-8'))

        self.data[int(message['id'])] = message
        print(self.data)

        message = "ACK".encode('utf-8')
        length = pack(">Q", len(message))

        conn.sendall(length+message)

    def execute_read_data(self, conn):
        print('Received read_data from coordinator')
        payload = json.dumps(self.data).encode('utf-8')
        payload_length = pack('>Q', len(payload))
        print(f"Read payload: {payload}")
        conn.sendall(payload_length + payload)

    def get_article_id(self):
        self.article_id += 1

        return self.article_id


    def run_server(self):
        while True:
            # Block and accept new socket
            conn, addr = self.server_socket.accept()
            print(f"Node {self.replica_id} connected by {addr}")
            # Pass new accepted socket connection to the process requests function
            threading.Thread(target = self.process_requests, args=(conn,addr)).start()

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_host_name, my_host_port = self.connections[self.replica_id]
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((my_host_name, my_host_port))
        self.server_socket.listen(5)
        print(f"Node {self.replica_id} listening on {my_host_port}")
        threading.Thread(target=self.run_server).start()

if __name__=="__main__":
    args = sys.argv
    node_id = args[1]

    connections_list = TEST_CONNECTION_LIST
    node_1 = Replica(replica_id=0, connections=connections_list, mode='quorum')
    node_2 = Replica(replica_id=1, connections=connections_list, mode='quorum')
    node_3 = Replica(replica_id=2, connections=connections_list, mode='quorum')

    replicas = [node_1, node_2, node_3]

    replicas[int(node_id)].run()