from multiprocessing import Process
import os
from replica import Replica
from msg_utils import *
import sys
import time
import socket
import json
import struct


BASE_ADDRESS = '127.0.0.1'
BASE_PORT = 5000


def info(title):
    print(title)
    print('module name:', __name__)
    print('parent process:', os.getppid())
    print('process id:', os.getpid())

def f(name):
    info('function f')
    print('hello', name)

def generate_connections_list(total_number_of_replicas):
    connections_list = [None]*total_number_of_replicas

    i = 0
    for index in range(len(connections_list)):
        connections_list[index] = (BASE_ADDRESS, BASE_PORT+i)
        i+=1

    return connections_list

def generate_replicas_list(total_number_of_replicas, connections_list, mode):
    replicas_list = [None]*total_number_of_replicas

    for replica_index in range(len(connections_list)):
        replicas_list[replica_index] = Replica(replica_id=replica_index, connections=connections_list, mode=mode)

    print(replicas_list)
    return replicas_list

if __name__ == '__main__':



    # Code to benchmark




    args = sys.argv
    node_id = int(args[1])
    mode = args[2]
    total_number_of_replicas = int(args[3])

    connections_list = generate_connections_list(total_number_of_replicas, )
    # node_1 = Replica(replica_id=0, connections=connections_list, mode=mode)
    # node_2 = Replica(replica_id=1, connections=connections_list, mode=mode)
    # node_3 = Replica(replica_id=2, connections=connections_list, mode=mode)

    replicas_list = generate_replicas_list(total_number_of_replicas, connections_list, mode)

    # replicas[int(node_id)].run()


    process_list = [None]*len(replicas_list)
    for replica_index in range(len(replicas_list)):
        # Setting daemon to true here ensures the process ends when i ctrl+c this bad boi
        process_list[replica_index] = Process(target=replicas_list[replica_index].run(), daemon=True)
    
    for process in process_list:
        process.start()

    # STARTING THE TIMER
    start_time = time.perf_counter()

    print(f"Attempting to connect to server at {connections_list[0]}...")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((connections_list[0][0], connections_list[0][1]))
    
    title = "This is a title test"
    post = "And this is the body post"
    user = "Minorkeys"
    # Setup payload
    payload = json.dumps({"id": None,
                            "parent": 0,
                            "title": title,
                            "content": post,
                            "user": user}).encode('utf-8') # bytes

    length = pack('>Q', len(payload))
    request_type = pack('>Q', int(REQUEST_TYPE.POST))
    # Send POST
    client_socket.sendall(request_type+length+payload)

    ack = client_socket.recv(1000)

    print(ack)

    # NOW WE TRY TO READ A POST
    # 
    # 
    # 
    print(f"Attempting to connect to server at {connections_list[0]}...")

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((connections_list[0][0], connections_list[0][1]))
    
    title = "dummy"
    post = "dummy"
    user = "Minorkeys"
    # Setup payload
    payload = json.dumps({"id": None,
                            "parent": 0,
                            "title": title,
                            "content": post,
                            "user": user}).encode('utf-8') # bytes

    length = pack('>Q', len(payload))
    request_type = pack('>Q', int(REQUEST_TYPE.READ))
    # Send POST
    client_socket.sendall(request_type+length+payload)

    new_post = client_socket.recv(1000)

    print(f"{new_post=}")

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    print(elapsed_time)

