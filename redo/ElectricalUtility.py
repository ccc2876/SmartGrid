import socket
import time
from sympy import isprime

NUM_AGGREGATORS = 2
NUM_SMART_METERS = 2
connections = []
MAX_CONSUMPTION = 10
NUM_TIME_INSTANCES = 10
ZP_SPACE = 0
eu = None

class ElectricalUtility:
    def __init__(self):
        self.bills_dict = dict()
        self.spatial_value = 0

    def set_spatial_value(self,value):
        self.spatial_value = value

    def get_spatial_value(self):
        return self.spatial_value

    def set_bills_dict(self,id, num):
        pass


def send_data():
    global NUM_AGGREGATORS,NUM_TIME_INSTANCES, MAX_CONSUMPTION,ZP_SPACE,connections, NUM_SMART_METERS
    val = NUM_TIME_INSTANCES * MAX_CONSUMPTION
    while not isprime(val):
        val += 1
    ZP_SPACE = val
    degree= NUM_AGGREGATORS - 1
    send_string = str(degree) + "\n" + str(ZP_SPACE) + "\n" + str(NUM_SMART_METERS)
    for conn in connections:
        conn.sendall(send_string.encode("utf-8"))

def get_spatial_results(max_buffer_size=5120):
    global connections, NUM_TIME_INSTANCES,eu
    for i in range(0, NUM_TIME_INSTANCES):
        for conn in connections:
            input = conn.recv(max_buffer_size)
            while not input:
                input = conn.recv(max_buffer_size)
            decoded_input = input.decode("utf-8")
            eu.set_spatial_value(int(decoded_input))
    print(eu.get_spatial_value())

def main():
    global eu
    eu  = ElectricalUtility()
    global connections, NUM_AGGREGATORS, NUM_TIME_INSTANCES
    host = "127.0.0.1"
    port = 8000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket Created")
    s.bind((host, port))
    s.listen()
    print("Socket Listening")
    while len(connections) < NUM_AGGREGATORS:
        conn, addr = s.accept()
        connections.append(conn)
    print("All aggregators connected")
    send_data()
    get_spatial_results()


if __name__ == '__main__':
    main()