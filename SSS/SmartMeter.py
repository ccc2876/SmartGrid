import sys
import time
import random as rand
import socket

import tracemalloc
BILL_METHOD = 0
NUM_TIME_INSTANCES = 80
NUM_AGGREGATORS = 10
ZP_SPACE = 0
DEGREE = 0
MAX_COEFFICIENT = 4
MAX_CONSUMPTION = 10
connections = []
sm = None
eu_conn = None
start = 0
sub_start = 0
sub_end = 0
share_creation_time = []


class SmartMeter:
    def __init__(self, id):
        self.ID = id
        self.polynomial = []
        self.degree = DEGREE
        self.secret = 0
        self.bill = 0

    def set_bill(self, bill):
        self.bill = bill

    def get_ID(self):
        return self.ID

    def set_secret(self, secret):
        self.secret = secret

    def set_polynomial(self, polynomial):
        self.polynomial = polynomial

    def get_polynomial(self):
        return self.polynomial

    def create_shares(self, ID):
        deg_copy = self.degree
        share = 0
        for num in self.polynomial:
            share += num * (ID ** deg_copy)
            deg_copy -= 1
        share += self.secret
        # print("Share for AGG #" + str(ID), ": ", share)
        return share


def initialization():
    global sm, MAX_CONSUMPTION, MAX_COEFFICIENT, NUM_AGGREGATORS, DEGREE
    ID = int(sys.argv[1])  # set the ID of the smart meter from command line args
    sm = SmartMeter(ID)  # create the smart meter object and initialize with the ID


def set_polynomial():
    global DEGREE
    # code to generate a random polynomial and a secret
    bin_list = []
    bin_list.append(1)
    for i in range(1, DEGREE):
        r = rand.randint(0, 1)
        bin_list.append(r)

    coeff_list = []
    for b in bin_list:
        if b == 1:
            coeff_list.append(rand.randint(1, MAX_COEFFICIENT))
    sm.set_polynomial(coeff_list)


def setup_connection():
    global sm, NUM_AGGREGATORS, connections

    for i in range(0, NUM_AGGREGATORS):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connections.append(soc)
    host = "127.0.0.1"
    port = 8001

    try:
        for conn in connections:
            conn.connect((host, port))
            port += 1
    except:
        print("Connection Error")
        sys.exit()


def send_shares():
    global connections, sm
    id = 1
    for conn in connections:
        share = sm.create_shares(id)
        send_string = str(sm.get_ID()) + " " + str(share)
        conn.sendall(send_string.encode("utf-8"))
        id += 1
    time.sleep(.1)


def get_initialization_data(connections, max_buffer_size=5120):
    global DEGREE, ZP_SPACE, start, BILL_METHOD
    input = eu_conn.recv(max_buffer_size)
    start = time.time()  # uncomment this when checking time
    while not input:
        input = eu_conn.recv(max_buffer_size)


    decoded_input = input.decode("utf-8")
    values = decoded_input.split("\n")
    BILL_METHOD = int(values[0])
    DEGREE = int(values[1])
    ZP_SPACE = int(values[2])
    end= time.time()
    # print("Degree:", DEGREE)
    # print("ZP:", ZP_SPACE)


def connect_to_eu():
    global eu_conn
    eu_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = "127.0.0.1"
    port = 7999
    try:
        eu_conn.connect((host, port))
    except:
        print("Connection Error")
        sys.exit()


def receive_bill():
    global connections, sm, sub_start, sub_end
    sub_start = time.time()
    for conn in connections:
        inp = conn.recv(5120)
        while not inp:
            inp = conn.recv(5120)
        sub_end = time.time()
        decoded_input = inp.decode("utf-8")
        sm.set_bill(int(float(decoded_input)))


def main():
    global sm, NUM_TIME_INSTANCES, connections, eu_conn, start, sub_start, sub_end, BILL_METHOD
    connect_to_eu()
    get_initialization_data(eu_conn)
    setup_connection()
    initialization()
    total = 0

    # run for number of time instances

    for i in range(0, NUM_TIME_INSTANCES):
        if BILL_METHOD == 3 and i != 0:
            for conn in connections:
                conn.recv(5120)
        set_polynomial()
        secret = rand.randint(1, MAX_CONSUMPTION)
        total += secret
        # print("Secret: ", secret)
        sm.set_secret(secret)
        # start_create = time.time()  # uncomment this when checking time
        send_shares()
        # end_create = time.time()  # uncomment this when checking time
        time.sleep(.015)
        # print(end_create - start_create)  # uncomment this when checking time

    print("sum", total)
    bill_start = time.time()
    receive_bill()
    bill_end = time.time()
    print("Bill: ", sm.bill)

    print("Total:", total)


if __name__ == '__main__':
    main()
