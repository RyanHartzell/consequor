"""
Basic server/client classes and helper utilities.

    NOTE: Referenced some code my buddies and I wrote a while back for a chatroom app:
                https://github.com/jmaggio14/imagepypelines-tools/tree/master
"""

__author__="Ryan Hartzell"
__email__="ryan_hartzell@mines.edu"
__copyright__="Copyright Ryan Hartzell, AUG 29 2024"

# Imports
import socket
from threading import *
from struct import pack, unpack
import select
from queue import Queue, Empty
import json
import uuid

# Constants
CHUNK_SIZE = 512
SERVER_DEFAULT_ADDR = ''
SERVER_TCP_PORT = 54345
SERVER_UDP_PORT = 54346

class Modes:
    TCP = socket.SOCK_STREAM

# Set up our classes and helper functions

# MSG MANIPULATION
######################
def pack_msg(msg_str):
    return msg_str.encode('utf-8')

def unpack_msg(msg_bytes):
    return msg_bytes.decode('utf-8')

# These chunking and unchunking funcs are basically my only junky protocol I suppose
def chunk_msg(msg, chunk_size):
    # Assume we've already got a bytes object (not string) and we'll send the length prior to chunking
    chunks = []

    # Get message length in bytes, packed into binary representation (>Q = big endianness, unsigned long long [in C], 8 byte unsigned integer [in Python])
    length = pack('>Q', len(msg)) # Optionally we might want to include a second int representing prepended data in each chunk (roughly len(pre) * (len(chunks)-1)
    chunks.append(length)

    # append each chunk to sub-message list 'chunks'. NOTE last chunk will be a bit shorter generally
    for i in range(0, len(msg), chunk_size):
        chunks.append(msg[i:i+chunk_size])

    # Includes initial length message
    return chunks

# Unused since select + single threaded Server is sufficient, but would have been necessary for more reliable chunked data.
def prepend(chunks):
    header_template = {"uuid": None, "seqid": None, "payload": None}
    altchunks = [None]*len(chunks)
    for i,c in enumerate(chunks):
        header_template['uuid'] = uuid.uuid1()
        header_template['seqid'] = i
        header_template['payload'] = c
        altchunks[i] = json.dumps(header_template)
    return altchunks

# SEND AND RECEIVE FUNCTIONS
############################

def recvall(c, length, chunk_size=4096, address=None):
    '''Convenience function to read large amounts of data (> N bytes)'''
    data = b''

    if address is None:
        # This assumes we already determined chunk length from initial message from client
        while len(data) < length:
            remaining = length - len(data)
            data += c.recv(min(remaining, chunk_size))

    else:
        # This assumes we already determined chunk length from initial message from client
        while len(data) < length:
            remaining = length - len(data)
            buf, _ = c.recvfrom(min(remaining, chunk_size))
            data += buf

    return data

# takes a socket and bytes object as argument
def send(sock, data, address=None, send_length=True):
    if send_length:
        length = pack('>Q', len(data))

        if address is None:
            sock.send(length) # send length of the message as 64bit integer
            sock.send(data) # send the message itself
        else:
            try:
                sock.sendto(length, address)
                sock.sendto(data, address)
            except:
                print(Warning(f'Paired socket at address {address} could not be found.'))

    else:
        if address is None:
            sock.send(data) # send the message itself
        else:
            try:
                sock.sendto(data, address)
            except:
                print(Warning(f'Paired socket at address {address} could not be found.'))

# takes a socket and bytes object as argument
def send_chunked(sock, data, address=None):

    chunks = chunk_msg(data, chunk_size=CHUNK_SIZE)

    if address is None:
        for chunk in chunks:
            sock.send(chunk) # send the message itself
    else:
        try:
            for chunk in chunks:
                sock.sendto(chunk, address) # send the message itself
        except:
            print(Warning(f'Paired socket at address {address} could not be found.'))

# takes socket as argument and optionally a client address if meant to run in UDP mode
def read(sock, address=None):
    if address is None:
        nbytes_msg = sock.recv(8) # 8 bytes for 64bit integer message length
        if nbytes_msg == b'': # Case for a disconnecting Client socket
            return nbytes_msg
        length, = unpack('>Q', nbytes_msg)
        return recvall(sock, length, chunk_size=512) # Note we're not unpacking this result - leave that to server logic
    else:
        try:
            nbytes_msg = sock.recvfrom(8)[0] # 8 bytes for 64bit integer
            if nbytes_msg == b'': # Case for a disconnecting Client socket
                return nbytes_msg
            length, = unpack('>Q', nbytes_msg)
            return recvall(sock, length, chunk_size=512, address=address) # Note we're not unpacking this result - leave that to server logic
        except:
            print(Warning(f'Paired socket at address {address} could not be found.'))
            
# CLIENT / SERVER SOCKET CREATIONS
##################################

def create_client(addr, port, mode, block=True):
    c = socket.socket(socket.AF_INET, mode)
    c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    c.setblocking(block)
    c.connect((addr,port))
    return c

def create_server(addr, port, mode, block=False):
    s = socket.socket(socket.AF_INET, mode)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(block)
    s.bind((addr,port))  # server specific bind
    # ONLY FOR TCP!!! CONNECTION BASED
    if mode==Modes.TCP:
        s.listen(5)  # set max num of unaccepted connections before not accepting connections
    return s

# Trying to make single threaded Server that can handle both TCP and UDP (separate sockets bound to same port!) client connections
# Currently does not block
class Server:
    def __init__(self, addr=SERVER_DEFAULT_ADDR, tcp_port=SERVER_TCP_PORT, udp_port=SERVER_UDP_PORT):
        self._addr = addr
        self._tcp_port = tcp_port

        self.tcp_socket = create_server(addr, self._tcp_port, Modes.TCP) # this is the 'listening' socket, and when ready to read will return a new connection socket file descriptor on 'accept'

        self.msg_queue = Queue(64) # blocks after 64 items pushed, until some are removed. Queue represents FULLY ASSEMBLED MESSAGES!!!!

    def run(self):
        # model after chatroom in IPTools
        connections = [self.tcp_socket, self.udp_socket]
        while True: # run forever
            # get all readable and writeable connections
            readable, writable, _ = select.select(connections, [], [], 0.1)

            for r in readable:
                # Check if tcp or udp and handle accordingly
                if r is self.tcp_socket: # ONLY RUNS FOR NEW CONNECTION!!!
                    conn = self._tcp_read(r)
                    connections.append(conn)

                # Saved TCP connections (mostly used in object oriented mode) that are sending will be handled here
                else:
                    ret = self._tcp_read(r, accept=False)
                    if ret == 'DEL':
                        connections.remove(r)
                        r.close() # hopefully this waits for the final message to clear the write queue, but not tragic if it doesn't.

    def _tcp_send(self, conn, nbytes_recv):
        # simple SHORT message sender which responds to a client request with an acknowledgment that the server has completed its request
        # send a confirmation value like "REQUEST #{hash} HANDLED, {actual}/{intended} BYTES RECIEVED" 
        conn.send(pack_msg(f"REQUEST HANDLED, {nbytes_recv} BYTES RECIEVED.")) # Should I replace this with simple ACK?

    def _tcp_read(self, conn, accept=True):
        if accept:
            conn, addr = conn.accept()
            conn.setblocking(1)

        # HANDLE REQUEST TYPE FIRST
        msg = conn.recv(3)
        request_type = unpack_msg(msg) # Always first 3 bytes of communication
        print(f"* REQUEST TYPE: {request_type}")

        if request_type == 'PUT':

            nbytes_msg, = unpack('>Q', conn.recv(8)) # Need the comma during assignment to unpack tuple returned from unpack

            msg = recvall(conn, nbytes_msg, chunk_size=512)

            if len(msg) != nbytes_msg:
                conn.send(b'Full message not received... Please try again.')
                print(f"[!] Error: Client {conn.getsockname()} must attempt to resend its message. Only {len(msg)} of {nbytes_msg} bytes received.")
                return

            print(f"* RECIEVED MESSAGE FROM {conn.getsockname()}, LENGTH {len(msg)} BYTES, PREVIEW:\n{msg[:50].decode('utf-8')}...\n")
            self._tcp_send(conn, len(msg))

            # Now decode full message and store in Queue
            self.msg_queue.put(unpack_msg(msg))

        elif request_type == 'GET':
            fwdmsg = 'No messages in the Queue :( Try again soon!'
            try:
                fwdmsg = self.msg_queue.get(timeout=0.1)
            except Empty:
                pass
            send_chunked(conn, pack_msg(fwdmsg)) # If timeout, means there are no messages to send! So just continue on

        elif request_type == 'DEL':
            conn.send(b'GOODBYE!')
            return 'DEL'

        else:
            print(f"[!] Error: Client {conn} must attempt to resend its message. Invalid request type.")

            try:
                conn.send(b'[!] Error: Request Type must be either "GET" or "PUT"... Please try again.')
            except:
                print(Warning('Client connection unexpectedly terminated.'))
                return 'DEL'

        # only return the connection if we accepted a new one 
        if accept:
            return conn


# Client sockets block by default, and default to TCP mode.
class Client:
    def __init__(self, server_addr=SERVER_DEFAULT_ADDR, server_port=SERVER_TCP_PORT, mode=Modes.TCP):
        self.socket = create_client(server_addr, server_port, mode, block=True)
        self.server = (server_addr, server_port)
        print(f"Communicating with server at {self.server} over {'UDP' if mode==Modes.UDP else 'TCP'}.")
        self.mode = mode

    # Default chunking behavior active in this send function for all size messages.
    def put_request(self, msg):
        address = None
        if self.mode == Modes.UDP:
            address = self.server

        request = b"PUT"
        send(self.socket, request, address=address, send_length=False)
        send_chunked(self.socket, pack_msg(msg), address=address)
        return self._recv_server_ack()

    # Simple ACK message from server. Client sockets block.
    def _recv_server_ack(self):
        if self.mode == Modes.UDP:
            return unpack_msg(self.socket.recvfrom(1024)[0]) # Hardcoding 1024 here because I'm never sending an "ACK" or info notification over 1024
        else:
            return unpack_msg(self.socket.recv(1024)) # Hardcoding 1024 here because I'm never sending an "ACK" or info notification over 1024

    # Here's where things get dicey... going to turn this into a GET request (so we send, then receive)
    def get_request(self): # old receive
        address = None
        if self.mode == Modes.UDP:
            address = self.server

        # Send a quick 'header' that says we'd like to be sent the next message off the queue (will also need to handle this GET vs PUT switch in our handler function)
        request = b"GET"
        send(self.socket, request, address=address, send_length=False) # always going to be 3 bytes for GET or PUT

        return unpack_msg(read(self.socket, address=address))

    # Kill method (TCP only!!!)
    def kill_request(self):
        # For TCP, need to give the indication to server that it can remove our connection.
        send(self.socket, b"DEL", address=None, send_length=False)

        # Now receive our goodbye ACK from server (setting timeout for good measure)
        self.socket.settimeout(3) # 3 second timeout
        try:
            return unpack_msg(self.socket.recv(8))
        except TimeoutError:
            # do nothing if we have a timeout
            pass

# Output a 4000 character long string. Will be encoded in utf-8 so one byte per character
# useful for testing, debugging
def make_fake_data():
    import string, random
    return ''.join([random.choice(string.ascii_letters) for _ in range(4000)])

if __name__=="__main__":
    s = Server()
    print("SERVER INFO:")
    print("TCP:", s.tcp_socket)
    s.run()

