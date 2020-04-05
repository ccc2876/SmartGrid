import sys
import socket
import time
import tracemalloc
import traceback
from threading import Thread, Lock
from numpy import long

NUM_TIME_INSTANCES = 10
NUM_SMART_METERS = 10
NUM_AGGREGATORS = 3
BILL_PRICE = 0
ZP_SPACE = 0
DEGREE = 0
aggregator = None
aggs_client_connections = []
server_conns = []
sm_connections = []
AGG_CONNS_SERVER = []
AGG_CONNS_CLIENT = []
eu_conn = None
recv_shares_count = 0
total_consump = 0
AGGS = []
time_spatial =[]
time_temporal= []
lock = Lock()


class Aggregator():
    def __init__(self, id):
        global NUM_SMART_METERS

        self.ID = id
        self.delta_func_multiplier = 0
        self.billing_dict = dict()
        self.spatial_counter = 0
        self.sumofshares = 0
        self.aggregated_value = 0
        self.total_consumption = 0
        self.bill_share_value = dict()
        self.consumption_dict = dict()

        for i in range(1, NUM_SMART_METERS + 1):
            self.bill_share_value[i] = 0

        for i in range(1, NUM_SMART_METERS + 1):
            self.billing_dict[i] = 0

        for i in range(1, NUM_SMART_METERS + 1):
            self.consumption_dict[i] = 0

    def set_total_consumption(self, value):
        self.total_consumption += value

    def reset_spatial(self):
        self.spatial_counter = 0
        self.total_consumption = 0

    def set_consumption(self, id, value):
        self.consumption_dict[int(id)] += value

    def get_ID(self):
        return self.ID

    def update_spatial_counter(self, value):
        self.spatial_counter += int(value)

    def update_billing_dict(self, meter_id, value):
        self.billing_dict[int(meter_id)] += int(value)

    def calculate_lagrange_multiplier(self, num_aggregators):
        top = 1
        bottom = 1
        for i in range(1, num_aggregators + 1):
            if i != self.get_ID():
                top *= -i
                bottom *= (self.get_ID() - i)
        self.delta_func_multiplier = top / bottom

    def get_lagrange_multiplier(self):
        """
        :return: the lagrange multiplier
        """
        return self.delta_func_multiplier

    def get_spatial_counter(self):
        return self.spatial_counter

    def calc_sum(self, value):
        """
        calculate the sum of the shares that were sent by adding the value
        :param value: the value that corresponds to the share multiplied by the delta func multiplier of the agg
        :param sm_id: the smart meter id
        """
        self.sumofshares += value

    def set_aggregated_value(self, val):
        self.aggregated_value += val

    def get_aggregated_value(self):
        return self.aggregated_value

    def get_billing_amount(self, num):
        amount = 0
        mult = self.delta_func_multiplier
        amount += mult * int(self.billing_dict[num])
        self.bill_share_value[num] = amount
        self.consumption_dict[num] += amount


def setup_sm_server(port):
    global NUM_SMART_METERS, sm_connections

    host = "127.0.0.1"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))

    while len(sm_connections) < NUM_SMART_METERS:
        s.listen()
        conn, addr = s.accept()
        print('Connected to :', addr[0], ':', addr[1])
        sm_connections.append(conn)


def receive_shares(conn, max_buffer_size=24):
    input = conn.recv(max_buffer_size)
    decoded_input = input.decode("utf8")
    return decoded_input


def send_spatial_eu():
    global eu_conn, aggregator
    total_consump = aggregator.total_consumption
    total_consump += aggregator.sumofshares
    eu_conn.sendall(str(total_consump).encode("utf-8"))



def send_aggregators_spatial():
    global AGG_CONNS_SERVER, aggregator
    for conn in AGG_CONNS_SERVER:
        value = aggregator.sumofshares
        conn.sendall(str(value).encode("utf-8"))
    # time.sleep(.5)


def recv_aggregators_spatial(max_buffer_size=5120):
    global AGG_CONNS_CLIENT, aggregator
    for conn in AGG_CONNS_CLIENT:
        input = conn.recv(max_buffer_size)
        while not input:
            input = conn.recv(max_buffer_size)
        decoded_input = input.decode("utf-8")
        aggregator.set_total_consumption(int(float(decoded_input)))
        # time.sleep(.25)



def communicate_smart_meter(conn):
    global sm_connections, NUM_TIME_INSTANCES, aggregator, eu_conn, recv_shares_count
    lock.acquire()
    string = ""
    string += receive_shares(conn)
    shares_time_instances = string.split(" ")
    print(shares_time_instances)
    meter_id = int(shares_time_instances[0])
    aggregator.update_billing_dict(meter_id, shares_time_instances[1])
    aggregator.update_spatial_counter(shares_time_instances[1])
    constant = long(aggregator.get_spatial_counter()) * long(aggregator.get_lagrange_multiplier())
    aggregator.calc_sum(constant)
    recv_shares_count += 1
    lock.release()

def agg_server_setup(num):
    global AGG_CONNS_SERVER
    TCP_IP = '127.0.0.1'
    TCP_PORT = int(sys.argv[1]) + 7000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    print("Socket Created")
    print(TCP_IP, " ", TCP_PORT)
    s.bind((TCP_IP, TCP_PORT))
    s.listen()
    print("Socket Listening")
    while len(AGG_CONNS_SERVER) < num-1:
        conn, addr = s.accept()
        AGG_CONNS_SERVER.append(conn)
        print('Connected to :', addr[0], ':', addr[1])
    print("All aggregators connected")


def connect_to_aggs_as_client(port):
    global NUM_AGGREGATORS, aggs_client_connections, AGG_CONNS_CLIENT
    host = "127.0.0.1"
    print(port)
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    AGG_CONNS_CLIENT.append(soc)
    if not (port == int(sys.argv[1]) + 7000):
        try:
            print(port)
            soc.connect((host, port))
        except:
            print("Connection Error")
            sys.exit()


def send_aggregators_temporal(i):
    global AGG_CONNS_SERVER, aggregator
    for conn in AGG_CONNS_SERVER:
        # print("here")
        value = aggregator.bill_share_value[i]
        # print("val:", value)
        conn.sendall(str(value).encode("utf-8"))
        # print("Sent")
    time.sleep(.5)


def recv_aggregators_temporal(i, max_buffer_size=5120):
    global AGG_CONNS_CLIENT, aggregator
    for conn in AGG_CONNS_CLIENT:
        input = conn.recv(max_buffer_size)
        while not input:
            input = conn.recv(max_buffer_size)
        decoded_input = input.decode("utf8")
        # print("Recv")
        # print(decoded_input)
        lock.acquire()
        aggregator.set_consumption(i, int(float(decoded_input)))
        lock.release()
    # print(aggregator.consumption_dict)
    time.sleep(.5)

def connect_to_eu():
    global eu_conn
    eu_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = "127.0.0.1"
    port = 8000
    try:
        eu_conn.connect((host, port))
    except:
        print("Connection Error")
        sys.exit()


def receive_data_eu(max_buffer_size=5120):
    global NUM_SMART_METERS, DEGREE, ZP_SPACE,BILL_PRICE
    # tracemalloc.start()
    input = eu_conn.recv(max_buffer_size)
    while not input:
        input = eu_conn.recv(max_buffer_size)
    start= time.time()
    decoded_input = input.decode("utf-8")
    values = decoded_input.split("\n")
    BILL_PRICE= int(values[0])
    DEGREE = int(values[1])
    ZP_SPACE = int(values[2])
    NUM_SMART_METERS = int(values[3])
    end = time.time()
    print(end- start)
    # snapshot = tracemalloc.take_snapshot()          # uncomment this when checking for memory amount
    # top_stats = snapshot.statistics('lineno')       # uncomment this when checking for memory amount
    # for stat in top_stats:                          # uncomment this when checking for memory amount
    #     print(stat)
    print(DEGREE, ZP_SPACE, NUM_SMART_METERS)


def send_data_to_sm():
    global sm_connections, DEGREE, ZP_SPACE
    send_string = str(DEGREE) + "\n" + str(ZP_SPACE)
    for conn in sm_connections:
        conn.sendall(send_string.encode("utf-8"))

def create_bill_data():
    global aggregator, BILL_PRICE
    for i in range(1,len(aggregator.consumption_dict)+1):
        aggregator.consumption_dict[i] = aggregator.consumption_dict[i] * BILL_PRICE

def send_bill_data_eu():
    global aggregator, eu_conn
    send_string = ""
    for  i in range(1,len(aggregator.consumption_dict)+1):
       send_string += str(i) + "\n"
       send_string += str(aggregator.consumption_dict[i]) + "\n"
    eu_conn.sendall(send_string.encode("utf-8"))

def send_bill_data_sm(i):
    global sm_connections,aggregator
    bill= aggregator.consumption_dict[i+1]
    sm_connections[i].sendall(str(bill).encode("utf-8"))

def main():
    global aggregator, NUM_AGGREGATORS, DEGREE, ZP_SPACE,time_spatial,time_temporal
    connect_to_eu()
    receive_data_eu()
    counter = 1
    ID = int(sys.argv[1])
    print(ID)
    port = 8000 + ID

    aggregator = Aggregator(ID)
    aggregator.calculate_lagrange_multiplier(NUM_AGGREGATORS)


    for i in range(1, NUM_AGGREGATORS + 1):
        agg_port = 7000 + counter
        if ID == counter:
            agg_server_setup(NUM_AGGREGATORS)
        else:
            time.sleep(1)
            connect_to_aggs_as_client(agg_port)
        counter +=1


    setup_sm_server(port)
    # send_data_to_sm()
    send_bill = False
    for i in range(0, NUM_TIME_INSTANCES):
    # while recv_shares_count < (NUM_TIME_INSTANCES * NUM_SMART_METERS):
        for conn in sm_connections:
            try:
                t = Thread(target=communicate_smart_meter, args=(conn,))
                t.start()
            except:
                print("Thread did not start.")
                traceback.print_exc()
            # spatial aggregation
            # tracemalloc.start()                             # uncomment this when checking for memory amount
            start=time.time()                              # uncomment this when checking for time
            lock.acquire()
            send_aggregators_spatial()
            recv_aggregators_spatial()
            send_spatial_eu()
            aggregator.reset_spatial()
            end= time.time()                               # uncomment this when checking for time
            # snapshot = tracemalloc.take_snapshot()         # uncomment this when checking for memory amount
            # top_stats = snapshot.statistics('lineno')      # uncomment this when checking for memory amount
            # for stat in top_stats:                         # uncomment this when checking for memory amount
            #     print(stat)
            print("Spatial:", end-start)                               # uncomment this when checking for time
            time_spatial.append(end-start)
            lock.release()

    while recv_shares_count < (NUM_TIME_INSTANCES * NUM_SMART_METERS):
        send_bill = False
    send_bill = True
    time.sleep(.25)
    # temporal aggregation
    if send_bill:
        for i in range(1, NUM_SMART_METERS+1):
            print("Starting memory trace...")
            # tracemalloc.start()                             # uncomment this when checking for memory amount
            aggregator.get_billing_amount(i)
            start = time.time()                             # uncomment this when checking for time
            send_aggregators_temporal(i)
            recv_aggregators_temporal(i)
            end = time.time()                               # uncomment this when checking for time
            time.sleep(.25)
            # snapshot = tracemalloc.take_snapshot()          # uncomment this when checking for memory amount
            # top_stats = snapshot.statistics('lineno')       # uncomment this when checking for memory amount
            # for stat in top_stats:                          # uncomment this when checking for memory amount
            #     print(stat)
            print("Temporal:", end-start-1)                                # uncomment this when checking for time
            time_temporal.append((end-start-1))
    print(aggregator.consumption_dict)
    create_bill_data()
    print(aggregator.consumption_dict)
    send_bill_data_eu()

    for i in range(0, NUM_SMART_METERS ):
        send_bill_data_sm(i)

    # write time to files
    filename_spatial = "/Users/clairecasalnova/PycharmProjects/SmartGrid/SSS/AggregatorFiles/time_spatial_agg" + str(ID) + ".txt"
    fs = open(filename_spatial, "w+")
    for val in time_spatial:
        fs.write(str(val) + "\n")

    filename_temporal = "/Users/clairecasalnova/PycharmProjects/SmartGrid/SSS/AggregatorFiles/time_temporal_agg" + str(ID) + ".txt"
    ft = open(filename_temporal, "w+")
    for val in time_temporal:
        ft.write(str(val) + "\n")

if __name__ == '__main__':
    main()
