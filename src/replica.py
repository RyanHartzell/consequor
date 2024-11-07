import select
from msg_utils import *
import random
import core
import jsonschema

POST_JSON_SCHEMA = {
  "$schema": "http://json-schema.org/draft-04/schema#",
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
  }
}


class Replica():
    def __init__(self, node_id, replica_address_list, mode = 'sequential' ) -> None:
        # If this class exists, then it must be the coordinator. So there is no flag.
        self.consistency_mode = mode
        self.replica_addresses = replica_address_list
        self.coordinator_index = 0
        self.data = {}                      #dict to hold all post data, metadata, etc.

        self.this_replica_id = node_id
        self.me_socket = core.create_server(self.replica_addresses[node_id][0], self.replica_addresses[node_id][1], core.Modes.TCP)
        self.connections = [None] * len(self.replica_addresses)
        self.connect_to_replicas()        # includes our own socket and conections to every other replica

        # self.elect_leader() #TODO
    
    @property
    def coordinator_flag(self):
        return self.this_replica_id == self.coordinator_index

    #POpulates list of sockets.
    def connect_to_replicas(self):
        for replica in range(0,len(self.replica_addresses)):
            if replica != self.this_replica_id:
                self.connections[replica] = core.create_client(self.replica_addresses[replica][0], self.replica_addresses[replica][1], core.Modes.TCP)
            else:
                self.connections[replica] = self.me_socket

    def run_replica(self):
        # Listen to all replica and client connections
        readable, writable, _ = select.select(self.connections, [], [], 0.1)

        for r in readable:
            # Check if tcp or udp and handle accordingly
            if r is self.me_socket: # ONLY RUNS FOR NEW CONNECTION!!!

                conn, addr = self._tcp_read(r) # Accept connection

                peers = [s.getpeername() for s in self.connections]

                if addr not in peers:
                    self.connections.append(conn)
                else:
                    # In case of EOF, remove the connection instantly
                    for i,p in enumerate(peers):
                        if p == addr:
                            self.connections[i].close()
                            self.connections.remove(self.connections[i])

            # Saved TCP connections (mostly used in object oriented mode) that are sending will be handled here
            else:
                ret = self._tcp_read(r, accept=False)
                if ret == 'KILL_CONNECTION': # Maybe just use the disconnect request here
                    self.connections.remove(r)
                    r.close() # hopefully this waits for the final message to clear the write queue, but not tragic if it doesn't.

    # This function actually receives messages and processes them.
    def _tcp_read(self, conn, accept=True):
        if accept:
            conn, addr = conn.accept()
            conn.setblocking(1)
            return (conn, addr)

        # HANDLE REQUEST TYPE FIRST
        msg = conn.recv(8) # We want int64, which will represent an integer value
        request_type = unpack_msg(msg) # Always first byte of communication
        print(f"* REQUEST TYPE: {request_type}")

        nbytes_msg, = unpack('>Q', conn.recv(8)) # Need the comma during assignment to unpack tuple returned from unpack

        msg = recvall(conn, nbytes_msg, chunk_size=512)

        if request_type == REQUEST_TYPE.POST:
            self.execute_POST(conn, msg)
        elif request_type == REQUEST_TYPE.CHOOSE:
            self.execute_CHOOSE(conn)
        elif request_type == REQUEST_TYPE.READ:
            self.execute_READ(conn)
        elif request_type == REQUEST_TYPE.REPLY:
            self.execute_REPLY(conn)
        elif request_type == REQUEST_TYPE.DISCONNECT:
            self.execute_DISCONNECT(conn)
        elif request_type == REQUEST_TYPE.r_SYNC:
            self.execute_SYNC(conn)
        elif request_type == REQUEST_TYPE.r_GET_ID:
            self.execute_GET_ID(conn)
        elif request_type == REQUEST_TYPE.r_NOMINATE:
            self.execute_NOMINATE(conn)
        else:
            print(f"[!] Error: Client {conn} must attempt to resend its message. Invalid request type.")

            try:
                conn.send(b'[!] Error: Request Type must be one of those described in the Request_Type class... Please try again.')
            except:
                print(Warning('Client connection unexpectedly terminated.'))
                return 'KILL_CONNECTION'

    def execute_POST(self, conn, msg):
        if self.coordinator_flag:
            if self.consistency_mode == 'Sequential':
                pass

            elif self.consistency_mode == 'Quorum':
                total_replicas_in_group = len(self.replica_addresses)
                quorum_size = (total_replicas_in_group/2) + 1
                replicas_to_write = random.sample(range(0, total_replicas_in_group), quorum_size)

                for replica in replicas_to_write:
                    print(f"Sending Write to replica number {replica}")
                
            elif self.consistency_mode == 'RYW':
                pass
            else:
                print("Woah there. I don't recognize that mode")
        else:
            #Forward POST to coordinator
            forward_message = pack_msg(msg)
            #send message to coordinator
            self.connections[self.coordinator_index].sendall(forward_message.encode('utf-8'))

    def execute_CHOOSE(self, conn):
        if self.coordinator_flag:
            pass
        else:
            #Forward CHOOSE  to coordinator
            pass

    def execute_READ(self, conn):
        if self.coordinator_flag:
            pass
        else:
            #Forward READ to coordinator
            pass

    def execute_REPLY(self, conn):
        if self.coordinator_flag:
            pass
        else:
            #Forward REPLY to coordinator
            pass 

    def execute_DISCONNECT(self, conn):
        pass

    def execute_SYNC(self, conn):
        pass

    def execute_GET_ID(self, conn):
        pass

    def execute_NOMINATE(self, conn):
        pass