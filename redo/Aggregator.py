import sys
import socket
import time
import tracemalloc
import traceback
from threading import Thread, Lock
from numpy import long

NUM_TIME_INSTANCES = 10
NUM_SMART_METERS = 5
NUM_AGGREGATORS = 2
BILL_PRICE = 0
ZP_SPACE = 0
DEGREE = 0
aggregator = None
aggs_client_connections = []
server_conns = []
sm_connections = []
AGG_CONNS = []
eu_conn = None
recv_shares_count = 0
total_consump = 0

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
    global AGG_CONNS, aggregator
    for conn in AGG_CONNS:
        value = aggregator.sumofshares
        conn.sendall(str(value).encode("utf-8"))


def recv_aggregators_spatial(max_buffer_size=5120):
    global AGG_CONNS, aggregator
    for conn in AGG_CONNS:
        input = conn.recv(max_buffer_size)
        while not input:
            input = conn.recv(max_buffer_size)
        decoded_input = input.decode("utf-8")
        aggregator.set_total_consumption(int(float(decoded_input)))

# def do_stuff(meter_id,val):
#     global recv_shares_count
#     lock.acquire()
#     aggregator.update_billing_dict(meter_id, val)
#     aggregator.update_spatial_counter(val)
#     constant = long(aggregator.get_spatial_counter()) * long(aggregator.get_lagrange_multiplier())
#     aggregator.calc_sum(constant)
#     recv_shares_count += 1
#
#     # spatial aggregation
#     # tracemalloc.start()                            # uncomment this when checking for memory amount
#     # start=time.time()                              # uncomment this when checking for time
#     send_aggregators_spatial()
#     recv_aggregators_spatial()
#     send_spatial_eu()
#
#     aggregator.reset_spatial()
#     # end= time.time()                               # uncomment this when checking for time
#     # snapshot = tracemalloc.take_snapshot()         # uncomment this when checking for memory amount
#     # top_stats = snapshot.statistics('lineno')      # uncomment this when checking for memory amount
#     # for stat in top_stats:                         # uncomment this when checking for memory amount
#     #     print(stat)
#     # print(end-start)                               # uncomment this when checking for time
#     lock.release()
#

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
    # spatial aggregation
    # tracemalloc.start()                            # uncomment this when checking for memory amount
    # start=time.time()                              # uncomment this when checking for time
    send_aggregators_spatial()
    recv_aggregators_spatial()
    send_spatial_eu()
    aggregator.reset_spatial()
    # end= time.time()                               # uncomment this when checking for time
    # snapshot = tracemalloc.take_snapshot()         # uncomment this when checking for memory amount
    # top_stats = snapshot.statistics('lineno')      # uncomment this when checking for memory amount
    # for stat in top_stats:                         # uncomment this when checking for memory amount
    #     print(stat)
    # print(end-start)                               # uncomment this when checking for time
    lock.release()

def agg_server_setup():
    global AGG_CONNS
    TCP_IP = '127.0.0.1'
    TCP_PORT = int(sys.argv[1]) + 7000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket Created")
    s.bind((TCP_IP, TCP_PORT))
    s.listen()
    print("Socket Listening")
    while len(AGG_CONNS) < NUM_AGGREGATORS - 1:
        conn, addr = s.accept()
        AGG_CONNS.append(conn)
    print("All aggregators connected")


def connect_to_aggs_as_client():
    global NUM_AGGREGATORS, aggs_client_connections
    host = "127.0.0.1"
    port = 7001
    for i in range(0, NUM_AGGREGATORS - 1):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        AGG_CONNS.append(soc)
        if not (port == int(sys.argv[1]) + 7000):
            try:
                soc.connect((host, port))
            except:
                print("Connection Error")
                sys.exit()
        port += 1


def send_aggregators_temporal(i):
    global AGG_CONNS, aggregator
    for conn in AGG_CONNS:
        # print("here")
        value = aggregator.bill_share_value[i]
        # print("val:", value)
        conn.sendall(str(value).encode("utf-8"))
        # print("Sent")
    time.sleep(1)


def recv_aggregators_temporal(i, max_buffer_size=5120):
    global AGG_CONNS, aggregator
    for conn in AGG_CONNS:
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
    time.sleep(1)

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
    input = eu_conn.recv(max_buffer_size)
    while not input:
        input = eu_conn.recv(max_buffer_size)
    decoded_input = input.decode("utf-8")
    values = decoded_input.split("\n")
    BILL_PRICE= int(values[0])
    DEGREE = int(values[1])
    ZP_SPACE = int(values[2])
    NUM_SMART_METERS = int(values[3])
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

def send_bill_data():
    global aggregator, eu_conn
    send_string = ""
    for  i in range(1,len(aggregator.consumption_dict)+1):
       send_string += str(i) + "\n"
       send_string += str(aggregator.consumption_dict[i]) + "\n"
    eu_conn.sendall(send_string.encode("utf-8"))

def main():
    global aggregator, NUM_AGGREGATORS, AGG_CONNS, DEGREE, ZP_SPACE
    connect_to_eu()
    receive_data_eu()

    ID = int(sys.argv[1])
    port = 8000 + ID

    aggregator = Aggregator(ID)
    aggregator.calculate_lagrange_multiplier(NUM_AGGREGATORS)
    if ID == 1:
        agg_server_setup()
    else:
        time.sleep(.01)
        connect_to_aggs_as_client()

    setup_sm_server(port)
    send_data_to_sm()
    send_bill = False
    for i in range(0, NUM_TIME_INSTANCES):
    # while recv_shares_count < (NUM_TIME_INSTANCES * NUM_SMART_METERS):
        for conn in sm_connections:
            try:
                t = Thread(target=communicate_smart_meter, args=(conn,))
                t.start()
                time.sleep(0.25)
            except:
                print("Thread did not start.")
                traceback.print_exc()

    while recv_shares_count < (NUM_TIME_INSTANCES * NUM_SMART_METERS):
        send_bill = False
    send_bill = True
    time.sleep(2)
    # temporal aggregation
    if send_bill:
        for i in range(1, NUM_SMART_METERS+1):
            # print("Starting memory trace...")
            # tracemalloc.start()                             # uncomment this when checking for memory amount
            aggregator.get_billing_amount(i)
            # start = time.time()                             # uncomment this when checking for time
            send_aggregators_temporal(i)
            recv_aggregators_temporal(i)
            time.sleep(2)
            # end = time.time()                               # uncomment this when checking for time
            # snapshot = tracemalloc.take_snapshot()          # uncomment this when checking for memory amount
            # top_stats = snapshot.statistics('lineno')       # uncomment this when checking for memory amount
            # for stat in top_stats:                          # uncomment this when checking for memory amount
            #     print(stat)
            # print(end-start)                                # uncomment this when checking for time
    print(aggregator.consumption_dict)
    create_bill_data()
    print(aggregator.consumption_dict)
    send_bill_data()


if __name__ == '__main__':
    main()
