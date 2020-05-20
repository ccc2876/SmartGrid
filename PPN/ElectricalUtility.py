import socket
import time
import sys
import tracemalloc
from sympy import isprime

NUM_SMART_METERS = 2
NUM_PPN = 2
config_conn = None
ppn_connections = []
sm_conns = []
MAX_CONSUMPTION = 10
NUM_TIME_INSTANCES = 2
ZP_SPACE = 0
eu = None
time_spatial = []
time_temporal = []


class ElectricalUtility:
    def __init__(self, price):
        self.bills_dict = dict()
        self.spatial_value = 0
        self.bill_price = price
        for i in range(1, NUM_SMART_METERS + 1):
            self.bills_dict[i] = 0

    def set_spatial_value(self, value):
        self.spatial_value = value

    def get_spatial_value(self):
        return self.spatial_value


def send_data():
    global config_conn
    send_string = str(eu.bill_price) + "\n"
    config_conn.sendall(send_string.encode("utf-8"))


def get_spatial_results(conn, max_buffer_size=5120):
    global eu
    inp = conn.recv(max_buffer_size)
    while not inp:
        inp = conn.recv(max_buffer_size)
    decoded_input = inp.decode("utf-8")
    eu.set_spatial_value(int(decoded_input))


def get_bills(max_buffer_size=5120):
    global eu, NUM_SMART_METERS
    for conn in ppn_connections:
        inp = conn.recv(max_buffer_size)
        while not input:
            inp = conn.recv(max_buffer_size)

        decoded_input = inp.decode("utf-8")
        values = decoded_input.split("\n")
        for i in range(0, NUM_SMART_METERS * 2, 2):
            eu.bills_dict[int(values[i])] += int(float(values[i + 1]))


def send_sm_bills():
    counter = 1
    for conn in sm_conns:
        conn.sendall(str(eu.bills_dict[counter]).encode("utf-8"))
        counter += 1



def main(price):
    global eu, config_conn, NUM_SMART_METERS, NUM_PPN, NUM_TIME_INSTANCES, sm_conns

    eu = ElectricalUtility(price)
    host = "127.0.0.1"
    port_agg = 8000
    s_config = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Config Socket Created")
    s_config.bind((host, port_agg))
    s_config.listen()
    print("Config Socket Listening")

    host = "127.0.0.1"
    port_ppn = 7999
    s_ppn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("PPN Socket Created")
    s_ppn.bind((host, port_ppn))
    s_ppn.listen()
    print("PPN Socket Listening")

    host = "127.0.0.1"
    port_sm = 6000
    s_sm = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("SM Socket Created")
    s_sm.bind((host, port_sm))
    print("SM Socket Listening")

    while config_conn is None:
        config_conn, addr = s_config.accept()
    print("Configurator connected")

    while len(ppn_connections) < NUM_PPN:
        conn, addr = s_ppn.accept()
        ppn_connections.append(conn)
    print("PPNs connected")

    send_data()

    while len(sm_conns) < NUM_SMART_METERS:
        s_sm.listen()
        conn, addr = s_sm.accept()
        sm_conns.append(conn)
    print("SM connected")

    get_bills()
    print(eu.bills_dict)
    send_sm_bills()


if __name__ == '__main__':
    price = int(input("Please enter the billing price: "))
    main(price)
