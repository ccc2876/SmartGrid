import socket
import time
import sys
import tracemalloc
from sympy import isprime

NUM_AGGREGATORS = 3
NUM_SMART_METERS = 2
agg_connections = []
sm_connections = []
MAX_CONSUMPTION = 10
NUM_TIME_INSTANCES = 5
ZP_SPACE = 0
eu = None
time_spatial = []
time_temporal = []


class ElectricalUtility:
    def __init__(self, billing_method, bill_string):
        self.bills_dict = dict()
        self.spatial_value = 0
        self.billing_method = billing_method

        for i in range(1, NUM_SMART_METERS + 1):
            self.bills_dict[i] = 0

        if billing_method == 1:
            self.bill_price = int(bill_string)
        elif billing_method == 2:
            bills = bill_string.split(";")
            self.price_dict = {}
            for entry in bills:
                keyval = entry.split(",")
                key = int(keyval[0])
                val = int(keyval[1])
                self.price_dict.__setitem__(key, val)
        else:
            self.bill_price = int(bill_string)


    def set_spatial_value(self, value):
        self.spatial_value = value

    def get_spatial_value(self):
        return self.spatial_value


def send_data():
    global NUM_AGGREGATORS, NUM_TIME_INSTANCES, MAX_CONSUMPTION, ZP_SPACE, agg_connections, NUM_SMART_METERS, eu
    val = NUM_TIME_INSTANCES * MAX_CONSUMPTION
    while not isprime(val):
        val += 1
    ZP_SPACE = val
    degree = NUM_AGGREGATORS - 1
    if eu.billing_method == 1:
        send_string = str(billing_method) + "\n" + str(eu.bill_price) + "\n" + str(degree) + "\n" + str(
            ZP_SPACE) + "\n" + str(NUM_SMART_METERS)
    elif eu.billing_method == 2:
        send_string = str(billing_method) + "\n" + str(eu.price_dict) + "\n" + str(degree) + "\n" + str(
            ZP_SPACE) + "\n" + str(NUM_SMART_METERS)
    else:
        send_string = str(billing_method) + "\n" + str(eu.bill_price) + "\n" + str(degree) + "\n" + str(
            ZP_SPACE) + "\n" + str(NUM_SMART_METERS)
    for conn in agg_connections:
        conn.sendall(send_string.encode("utf-8"))


def send_data_sm(bill_method):
    global NUM_AGGREGATORS, NUM_TIME_INSTANCES, MAX_CONSUMPTION, ZP_SPACE, sm_connections, NUM_SMART_METERS
    degree = NUM_AGGREGATORS - 1
    send_string = str(bill_method)+ "\n" +str(degree) + "\n" + str(ZP_SPACE) + "\n" + str(NUM_AGGREGATORS)
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


def main(billing_method, bill_string):
    global eu, agg_connections, sm_connections, NUM_AGGREGATORS, NUM_TIME_INSTANCES, time_spatial, time_temporal

    eu = ElectricalUtility(billing_method, bill_string)
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
    send_data_sm(billing_method)

    print("Spatial")
    count = 0
    for i in range(0, NUM_TIME_INSTANCES * NUM_SMART_METERS):
        if billing_method == 3 and ( count!= 0 and count % NUM_SMART_METERS == 0):
            new_bill=input("Please enter a price for the new time instance")
            for conn in agg_connections:
                conn.sendall(str(new_bill).encode("utf-8"))
        for conn in agg_connections:
            start = time.time()
            get_spatial_results(conn)
            end = time.time()
            time_spatial.append(end - start)
        count += 1



    print("Spatial Sum: ", eu.get_spatial_value())
    print("Temporal")

    for conn in agg_connections:
        get_bills(conn)

    print(eu.bills_dict)

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
    print("Please enter the number for the preferred billing method:   ")
    print("\t1. linear")
    print("\t2. cumulative")
    print("\t3. dynamic")
    billing_method = int(input())
    if billing_method == 1:
        print("Please enter the price per unit: ")
        bill_string = input()
    elif billing_method == 2:
        print("Please enter billing chart in the form \n\t5,2;10,3;15,1\n"
              "Where the first number is the max value for that range and the second value is the price per unit in that range\n"
              "Enter -1 for infinity")
        bill_string = input()
    else:
        print("Please enter the price for the first time instance:")
        bill_string =input()
    main(billing_method, bill_string)
