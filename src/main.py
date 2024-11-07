import socket, sys
from replica import Replica

from core import SERVER_TCP_PORT

if __name__ == "__main__":
    NUMBER_OF_PROCESSES_IN_TEST = 2

    args = sys.argv # Node_ID Mode

    # Hear we create the entire list of host_id's 
    this_test_bed_id = socket.gethostbyname(socket.gethostname())
    entire_host_id_list = [None]*NUMBER_OF_PROCESSES_IN_TEST

    for i in range(0,NUMBER_OF_PROCESSES_IN_TEST):
        entire_host_id_list[i] = (this_test_bed_id, SERVER_TCP_PORT + i)


    # Distributed Mutex object
    replica_server = Replica(int(args[1]), entire_host_id_list, mode=args[2] )
