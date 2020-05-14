import socket
import time
import sys
import tracemalloc
from sympy import isprime

NUM_SMART_METERS = 1
NUM_AGGREGATORS= 3
config_conn = None
sm_connections = []
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
    global agg_connections, NUM_TIME_INSTANCES, eu
    inp = conn.recv(max_buffer_size)
    while not inp:
        inp = conn.recv(max_buffer_size)
    decoded_input = inp.decode("utf-8")
    eu.set_spatial_value(int(decoded_input))


def get_bills(conn, max_buffer_size=5120):
    global eu, NUM_SMART_METERS, time_temporal
    inp = conn.recv(max_buffer_size)
    while not input:
        inp = conn.recv(max_buffer_size)
    start = time.time()
    decoded_input = inp.decode("utf-8")
    values = decoded_input.split("\n")
    for i in range(0, NUM_SMART_METERS * 2, 2):
        eu.bills_dict[int(values[i])] = int(float(values[i + 1]))
    end = time.time()
    time_temporal.append(end - start)


def main(price):
    global eu, config_conn, sm_connections, NUM_AGGREGATORS, NUM_TIME_INSTANCES, time_spatial, time_temporal

    eu = ElectricalUtility(price)
    host = "127.0.0.1"
    port_agg = 8000
    s_config = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket Created")
    s_config.bind((host, port_agg))
    s_config.listen()
    print("Config Socket Listening")

    # host = "127.0.0.1"
    # port_sm = 7999
    # s_sm = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # print("Socket Created")
    # s_sm.bind((host, port_sm))
    # s_sm.listen()
    # print("SM Socket Listening")

    while config_conn is None:
        config_conn, addr = s_config.accept()
    print("Configurator connected")

    send_data()



    # print("Spatial")
    # count = 0
    # for i in range(0, NUM_TIME_INSTANCES * NUM_SMART_METERS):
    #     for conn in agg_connections:
    #         start = time.time()
    #         get_spatial_results(conn)
    #         end = time.time()
    #         time_spatial.append(end - start)
    #     count += 1
    #

    #
    # print("Spatial Sum: ", eu.get_spatial_value())
    # print("Temporal")
    #
    # for conn in agg_connections:
    #     get_bills(conn)
    #
    # print(eu.bills_dict)

    # # write time to files
    # filename_spatial = "/Users/clairecasalnova/PycharmProjects/SmartGrid/SSS/ElectricalUtilityFiles/time_spatial_eu.txt"
    # fs = open(filename_spatial, "w+")
    # for val in time_spatial:
    #     fs.write(str(val) + "\n")
    # fs.close()
    #
    # filename_temporal = "/Users/clairecasalnova/PycharmProjects/SmartGrid/SSS/ElectricalUtilityFiles/time_temporal_eu.txt"
    # ft = open(filename_temporal, "w+")
    # for val in time_temporal:
    #     ft.write(str(val) + "\n")
    # ft.close()


if __name__ == '__main__':
    price = int(input("Please enter the billing price: "))
    main(price)