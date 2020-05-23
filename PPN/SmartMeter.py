import socket
import sys
import time
import random as rand


ppn_conns = []
NUM_PPNS= 10
DEGREE = NUM_PPNS - 1
NUM_TIME_INSTANCES = 10
MAX_COEFFICIENT = 4
MAX_CONSUMPTION = 10
ZP_SPACE = 0
sm = None
eu_conn = None



class SmartMeter:
    def __init__(self, id):
        self.ID = id
        self.polynomial = []
        self.degree = DEGREE
        self.secret = 0

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
        print("Share for AGG #" + str(ID), ": ", share)
        return share


def set_polynomial():
    global DEGREE, sm
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


def connect_to_ppn():
    global ppn_conns

    for i in range(0, NUM_PPNS):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ppn_conns.append(soc)
    host = "127.0.0.1"
    port = 7001

    try:
        for conn in ppn_conns:
            conn.connect((host, port))
            port += 1
    except:
        print("Connection Error")
        sys.exit()

def connect_to_eu():
    global eu_conn

    eu_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "127.0.0.1"
    port = 6000
    try:
        eu_conn.connect((host, port))
    except:
        print("Connection Error")
        sys.exit()


def send_shares():
    global ppn_conns, sm
    id = 1
    for conn in ppn_conns:
        share = sm.create_shares(id)
        send_string = str(sm.get_ID()) + " " + str(share)
        conn.sendall(send_string.encode("utf-8"))
        id += 1



def receive_bill(max_buffer_size=5120):
    bill = eu_conn.recv(max_buffer_size)
    while not bill:
        bill = eu_conn.recv(max_buffer_size)
    bill = bill.decode("utf-8")
    print("Bill: ", bill)

def main():
    global sm,NUM_TIME_INSTANCES
    connect_to_eu()
    sm = SmartMeter(int(sys.argv[1]))
    connect_to_ppn()
    total = 0
    for i in range(0, NUM_TIME_INSTANCES):
        set_polynomial()
        secret = rand.randint(1, MAX_CONSUMPTION)
        total += secret
        print("Secret: ", secret)
        sm.set_secret(secret)
        start_create = time.time()  # uncomment this when checking time
        send_shares()
        end_create = time.time()  # uncomment this when checking time
        time.sleep(.5)
        print(end_create - start_create)  # uncomment this when checking time



    receive_bill()

if __name__ == '__main__':
    main()