# Imports
from struct import pack, unpack
import json
import uuid
from enum import IntEnum

# Constants
CHUNK_SIZE = 512
SERVER_DEFAULT_ADDR = '' # on windows this should probably be changed to localhost? Or the actual host address...
SERVER_TCP_PORT = 54345

#Enums
class REQUEST_TYPE(IntEnum):
    POST = 1
    CHOOSE = 2
    READ = 3
    REPLY = 4
    DISCONNECT = 5
    r_SYNC = 6
    r_GET_ID = 7
    r_NOMINATE = 8
    r_WRITE = 9
    r_READ = 10

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
        print(nbytes_msg)
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