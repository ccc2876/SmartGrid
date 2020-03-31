import sys
import time
import random as rand
import socket

import tracemalloc

NUM_TIME_INSTANCES = 10
NUM_AGGREGATORS = 2
ZP_SPACE = 0
DEGREE = 0
MAX_COEFFICIENT = 4
MAX_CONSUMPTION = 10
connections = []
sm = None


class SmartMeter:
    def __init__(self, id):
        self.ID = id
        self.polynomial = []
        self.degree = DEGREE
        self.secret = 0

    def get_ID(self):
        return self.ID

    def set_secret(self,secret):
        self.secret = secret


    def set_polynomial(self,polynomial):
        self.polynomial = polynomial

    def get_polynomial(self):
        return self.polynomial

    def create_shares(self, ID):
        deg_copy= self.degree
        share = 0
        for num in self.polynomial:
            share += num * (ID**deg_copy)
            deg_copy -= 1
        share += self.secret
        print("Share for AGG #"+ str(ID), ": ",share)
        return share

def initialization():
    global sm, MAX_CONSUMPTION, MAX_COEFFICIENT, NUM_AGGREGATORS,DEGREE
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
    global connections,sm
    id = 1
    # sum_one= 0
    # sum_two = 0

    for conn in connections:
        share = sm.create_shares(id)
        # if id ==1:
        #     sum_one+=share
        # else:
        #     sum_two+=share
        send_string = str(sm.get_ID()) + " " + str(share)
        conn.sendall(send_string.encode("utf-8"))
        id += 1

    # return sum_one,sum_two

def get_initialization_data(connections,max_buffer_size=5120):
    global DEGREE, ZP_SPACE
    for conn in connections:
        input = conn.recv(max_buffer_size)
        while not input:
            input = conn.recv(max_buffer_size)
        decoded_input = input.decode("utf-8")
        values= decoded_input.split("\n")
        DEGREE= int(values[0])
        ZP_SPACE = int(values[1])
    print("Degree:", DEGREE)
    print("ZP:", ZP_SPACE)


def main():
    global sm, NUM_TIME_INSTANCES,connections

    setup_connection()
    get_initialization_data(connections)
    initialization()
    #send the sm id to the aggs
    # for conn in connections:
    #     send = str(sm.get_ID()) + " "
    #     conn.sendall(send.encode("utf-8"))
    total = 0

    #run for number of time instances

    for i in range(0,NUM_TIME_INSTANCES):
        set_polynomial()
        secret = rand.randint(1,MAX_CONSUMPTION)
        total+= secret
        print("Secret: ", secret)
        sm.set_secret(secret)
        # tracemalloc.start()                            # uncomment this when checking for memory amount
        # start=time.time()                              # uncomment this when checking time
        send_shares()
        # end= time.time()                               # uncomment this when checking time
        # snapshot = tracemalloc.take_snapshot()         # uncomment this when checking for memory amount
        # top_stats = snapshot.statistics('lineno')      # uncomment this when checking for memory amount
        # for stat in top_stats:                         # uncomment this when checking for memory amount
        #     print(stat)                                # uncomment this when checking for memory amount
        # print(end-start)                               # uncomment this when checking time
        time.sleep(1.5)
    print("Total:", total)

    # time.sleep(30)

if __name__ == '__main__':
    main()
