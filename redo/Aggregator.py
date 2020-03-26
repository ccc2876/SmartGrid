import sys
import socket

NUM_TIME_INSTANCES = 10
NUM_SMART_METERS = 2
connections = []

class Aggregator():
    def __init__(self):
        pass


def setup_sm_server(port):
    global NUM_SMART_METERS, connections

    host="127.0.0.1"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))

    while len(connections) < NUM_SMART_METERS:
        s.listen()
        conn, addr = s.accept()
        print('Connected to :', addr[0], ':', addr[1])
        connections.append(conn)

def receive_shares(conn, max_buffer_size = 24):
    input =conn.recv(max_buffer_size)
    decoded_input = input.decode("utf8")
    return decoded_input


def main():
    global connections

    ID = int(sys.argv[1])
    port = 8000 + ID
    setup_sm_server(port)
    for conn in connections:
        string = ""
        shares_time_instances = []
        for i in range(0,NUM_TIME_INSTANCES):
            string += receive_shares(conn)
        string = string[:len(string)-1]
        shares_time_instances = string.split(" ")
        print(shares_time_instances)

if __name__ == '__main__':
    main()
