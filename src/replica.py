import select
from msg_utils import *


class Replica():
    def __init__(self, node_id, mode = 'sequential' ) -> None:
        # If this class exists, then it must be the coordinator. So there is no flag.
        self.consistency_mode = mode
        self.replica_addresses = []
        self.replica_connections = self.connect_to_replicas()        # includes our own socket and conections to every other replica
        self.client_connections = []
        self.coordinator_index = 0
        self.data = {}                      #dict to hold all post data, metadata, etc.
        self.connections = self.replica_connections + self.client_connections           #concatenated list for selecting
        self.me_socket = create_tcp_socket(node_id)
        
        self.coordinator_flag = True

        # self.elect_leader() #TODO

    def run(self):
        while True:
            if self.coordinator_flag:
                self.run_coordinator()
            else:
                #Must be a replica
                self.run_replica()

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
                            self.connections.remove(self.connections[i])
                            self.client_connections[i].close()

            # Saved TCP connections (mostly used in object oriented mode) that are sending will be handled here
            else:
                ret = self._tcp_read(r, accept=False)
                if ret == 'KILL_CONNECTION': # Maybe just use the disconnect request here
                    self.connections.remove(r)
                    r.close() # hopefully this waits for the final message to clear the write queue, but not tragic if it doesn't.

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



        if request_type == Request_Type.POST:
            self.execute_POST(conn, msg)
        elif request_type == Request_Type.CHOOSE:
            self.execute_CHOOSE(conn)
        elif request_type == Request_Type.READ:
            self.execute_READ(conn)
        elif request_type == Request_Type.REPLY:
            self.execute_REPLY(conn)
        elif request_type == Request_Type.DISCONNECT:
            self.execute_DISCONNECT(conn)
        elif request_type == Request_Type.r_SYNC:
            self.execute_SYNC(conn)
        elif request_type == Request_Type.r_GET_ID:
            self.execute_GET_ID(conn)
        elif request_type == Request_Type.r_NOMINEE:
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
            pass
        else:
            while(True):
                #Forward POST to coordinator
                forward_message = pack_msg(msg)
                #send message to coordinator
                self.replica_connections[self.coordinator_index].sendall(forward_message.encode('utf-8'))

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



    def run(self):

        # Receive a message. This may need to be threaded. Will leave unthreaded for now.
        message = listen()
        
        # process message 
        if self.consistency_mode == 'sequential':
            process_sequential_message(message)
        elif self.consistency_mode == 'quorum':
            process_quorum_message(message)
        elif self.consistency_mode == 'read-your-write':
            process_RYW_message(message)
        else:
            # Should not make it here
            pass


    def process_sequential_message(self):
        pass

    def process_quorum_message(self):
        pass

    def process_RYW_message(self):
        pass