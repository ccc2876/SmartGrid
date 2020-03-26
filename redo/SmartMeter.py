import sys
import random as rand
import socket


NUM_TIME_INSTANCES = 10
NUM_AGGREGATORS = 2
ZP_SPACE = 0
MAX_COEFFICIENT = 4
MAX_CONSUMPTION = 10
connections = []
sm = None


class SmartMeter:
    def __init__(self, id):
        self.ID = id
        self.polynomial = []
        self.degree = 0
        self.secret = 0

    def set_secret(self,secret):
        self.secret = secret

    def set_degree(self,degree):
        self.degree = degree

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
        print(share)
        return share

def initialization():
    global sm, MAX_CONSUMPTION, MAX_COEFFICIENT, NUM_AGGREGATORS

    ID = int(sys.argv[1])  # set the ID of the smart meter from command line args
    sm = SmartMeter(ID)  # create the smart meter object and initialize with the ID

    degree = NUM_AGGREGATORS - 1  # get the degree based on the number of aggs
    sm.set_degree(degree)  # set the degree var in the Smart Meter

    # code to generate a random polynomial and a secret
    bin_list = []
    bin_list.append(1)
    for i in range(1, degree):
        r = rand.randint(0, 1)
        bin_list.append(r)

    coeff_list = []
    for b in bin_list:
        if b == 1:
            coeff_list.append(rand.randint(1, MAX_COEFFICIENT))
    print(coeff_list)
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
    for conn in connections:
        share = sm.create_shares(id)
        send_string = str(share) + " "
        conn.sendall(send_string.encode("utf-8"))
        id += 1

def main():
    global sm, NUM_TIME_INSTANCES
    initialization()
    setup_connection()
    for i in range(0,NUM_TIME_INSTANCES):
        secret = rand.randint(1,MAX_CONSUMPTION)
        sm.set_secret(secret)
        send_shares()

if __name__ == '__main__':
    main()
