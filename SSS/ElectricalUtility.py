import socket
import time
import tracemalloc
from sympy import isprime

NUM_AGGREGATORS = 3
NUM_SMART_METERS = 10
agg_connections = []
sm_connections = []
MAX_CONSUMPTION = 10
NUM_TIME_INSTANCES = 10
ZP_SPACE = 0
BILL_PRICE = 2
eu = None
time_spatial = []
time_temporal = []


class ElectricalUtility:
    def __init__(self):
        self.bills_dict = dict()
        self.spatial_value = 0

        for i in range(1, NUM_SMART_METERS + 1):
            self.bills_dict[i] = 0

    def set_spatial_value(self, value):
        self.spatial_value = value

    def get_spatial_value(self):
        return self.spatial_value


def send_data():
    global NUM_AGGREGATORS, NUM_TIME_INSTANCES, MAX_CONSUMPTION, ZP_SPACE, agg_connections, NUM_SMART_METERS
    val = NUM_TIME_INSTANCES * MAX_CONSUMPTION
    while not isprime(val):
        val += 1
    ZP_SPACE = val
    degree = NUM_AGGREGATORS - 1
    send_string = str(BILL_PRICE) + "\n" + str(degree) + "\n" + str(ZP_SPACE) + "\n" + str(NUM_SMART_METERS)
    for conn in agg_connections:
        conn.sendall(send_string.encode("utf-8"))


def send_data_sm():
    global NUM_AGGREGATORS, NUM_TIME_INSTANCES, MAX_CONSUMPTION, ZP_SPACE, sm_connections, NUM_SMART_METERS
    degree = NUM_AGGREGATORS - 1
    send_string = str(degree) + "\n" + str(ZP_SPACE) + "\n" + str(NUM_AGGREGATORS)
    for conn in sm_connections:
        conn.sendall(send_string.encode("utf-8"))


def get_spatial_results(conn, max_buffer_size=5120):
    global agg_connections, NUM_TIME_INSTANCES, eu
    inp = conn.recv(max_buffer_size)
    while not inp:
        inp = conn.recv(max_buffer_size)
    decoded_input = inp.decode("utf-8")
    eu.set_spatial_value(int(decoded_input))


def get_bills(conn, max_buffer_size=5120):
    global eu, NUM_SMART_METERS
    inp = conn.recv(max_buffer_size)
    while not input:
        inp = conn.recv(max_buffer_size)
    decoded_input = inp.decode("utf-8")
    values = decoded_input.split("\n")
    for i in range(0, NUM_SMART_METERS * 2, 2):
        eu.bills_dict[int(values[i])] = int(float(values[i + 1]))


def main():
    global eu
    eu = ElectricalUtility()
    global agg_connections, sm_connections, NUM_AGGREGATORS, NUM_TIME_INSTANCES, time_spatial, time_temporal
    host = "127.0.0.1"
    port_agg = 8000
    s_agg = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket Created")
    s_agg.bind((host, port_agg))
    s_agg.listen()
    print("Agg Socket Listening")

    host = "127.0.0.1"
    port_sm = 7999
    s_sm = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket Created")
    s_sm.bind((host, port_sm))
    s_sm.listen()
    print("SM Socket Listening")

    while len(agg_connections) < NUM_AGGREGATORS:
        conn, addr = s_agg.accept()
        agg_connections.append(conn)
    print("All aggregators connected")

    send_data()

    while len(sm_connections) < NUM_SMART_METERS:
        conn, addr = s_sm.accept()
        sm_connections.append(conn)
    send_data_sm()
    print("Spatial")
    for i in range(0, (NUM_TIME_INSTANCES * NUM_SMART_METERS)):
        for conn in agg_connections:
            # tracemalloc.start()  # uncomment this when checking for memory amount
            start = time.time()
            get_spatial_results(conn)
            end = time.time()

            time_spatial.append(end - start)
    # snapshot = tracemalloc.take_snapshot()  # uncomment this when checking for memory amount
    # top_stats = snapshot.statistics('lineno')  # uncomment this when checking for memory amount
    # for stat in top_stats:  # uncomment this when checking for memory amount
    #     print(stat)
    # print("\n\n\n\n\n")

    print("Spatial Sum: ", eu.get_spatial_value())
    # tracemalloc.start()
    print("Temporal")
    start = time.time()
    for conn in agg_connections:
        get_bills(conn)
    end = time.time()
    # snapshot = tracemalloc.take_snapshot()  # uncomment this when checking for memory amount
    # top_stats = snapshot.statistics('lineno')  # uncomment this when checking for memory amount
    # for stat in top_stats:  # uncomment this when checking for memory amount
    #     print(stat)
    time_temporal.append(end - start)
    print(eu.bills_dict)

    # write time to files
    filename_spatial = "/Users/clairecasalnova/PycharmProjects/SmartGrid/SSS/ElectricalUtilityFiles/time_spatial_eu.txt"
    fs = open(filename_spatial, "w+")
    for val in time_spatial:
        fs.write(str(val) + "\n")
    fs.close()

    filename_temporal = "/Users/clairecasalnova/PycharmProjects/SmartGrid/SSS/ElectricalUtilityFiles/time_temporal_eu.txt"
    ft = open(filename_temporal, "w+")
    for val in time_temporal:
        ft.write(str(val) + "\n")
    ft.close()


if __name__ == '__main__':
    main()
