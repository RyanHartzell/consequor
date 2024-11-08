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

    #Sets coordinator flag
    @property
    def coordinator_flag(self):
        return self.replica_id == self.coordinator_index
    
    # Forward messages and wait to recevie ack
    def forward_to_coordinator(self, message):
        coord_host, coord_port = self.connections[0]

        coord_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        coord_socket.connect((coord_host, coord_port))
        coord_socket.sendall(message.encode('utf-8'))
        
        # TODO: Don't
        return_message = coord_socket.recv(1000)
        return str(return_message)
    
    # Forward message and don't wait to receive ack
    def send_to_coordinator(self, message):
        coord_host, coord_port = self.connections[0]
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((coord_host, coord_port))
            s.sendall(message.encode('utf-8'))

   

    #Function that handles incoming messages and acts on consistency logic. This links communication logic to consistency logic
    def process_requests(self, conn, addr):
        #TODO Here we will read with JSON library and parse message. We may get rid of this while loop
        while True:
            # message = conn.recv(1024).decode('utf-8')
            # print(message)

            
            req_enum = conn.recv(1).decode('utf-8')
            msglen = conn.recv(8).decode('utf-8')
            message = recvall(conn, int(msglen))

            if not req_enum:
                break
            if req_enum == 'post':
                self.execute_post(conn, message)
            elif req_enum == 'choose':
                self.execute_choose(conn, message)
            elif req_enum == 'write':
                self.execute_write(conn, message)
            elif req_enum == 'read_data':
                self.execute_read_data(conn)
            else:
                print('unindentified req_enum type')
        conn.close()

    
    def execute_choose(self, conn, message):
        if self.replica_id != 0:
            #Forward this to the coordinator
            return_message = self.forward_to_coordinator(message)
            conn.sendall(return_message.encode('utf-8'))

        else:
            print("Hey, its me, coordinator, I'm choosing again.")
            post_replicas = random.sample(range(0,len(self.connections)), 2)
            for replica in post_replicas:
                target_host, target_port = self.connections[replica]
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((target_host, target_port))
                    s.sendall('read_data'.encode('utf-8'))
                    action_message = str(s.recv(1000))
                
            conn.sendall(action_message.encode('utf-8'))

    def execute_post(self, conn, message):
        if self.replica_id != 0:
            #Forward this to the coordinator
            return_message = self.forward_to_coordinator(message)
            conn.sendall(return_message.encode('utf-8'))
        else:
            print("Hey, its me, coordinator, I'm posting again.")
            post_replicas = random.sample(range(0,len(self.connections)), 2)
            for replica in post_replicas:
                target_host, target_port = self.connections[replica]
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((target_host, target_port))
                    s.sendall('write'.encode('utf-8'))
                    action_message = str(s.recv(1000))
            conn.sendall(action_message.encode('utf-8'))

    def execute_write(self, conn):
        print('Received WRITE from coordinator')
        # self.send_to_coordinator("Ack")
        conn.sendall('ACK'.encode('utf-8'))
        
    def execute_read_data(self, conn):
        print('Received read_data from coordinator')
        # self.send_to_coordinator("Ack")
        conn.sendall('ACK'.encode('utf-8'))


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
        self.server_socket.bind((my_host_name, my_host_port))
        self.server_socket.listen(5)
        print(f"Node {self.replica_id} listening on {my_host_port}")
        threading.Thread(target=self.run_server).start()

if __name__=="__main__":
    args = sys.argv
    node_id = args[1]

    connections_list = TEST_CONNECTION_LIST
    node_1 = Replica(replica_id=0, connections=connections_list)
    node_2 = Replica(replica_id=1, connections=connections_list)
    node_3 = Replica(replica_id=2, connections=connections_list)

    replicas = [node_1, node_2, node_3]

    replicas[int(node_id)].run()

