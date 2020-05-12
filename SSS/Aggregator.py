import sys
import socket
import time
import tracemalloc
import traceback
from threading import Thread, Lock
from numpy import long

NUM_TIME_INSTANCES = 5
NUM_SMART_METERS = 2
NUM_AGGREGATORS = 3
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
time_spatial = []
time_temporal = []
lock = Lock()


class Aggregator():
    def __init__(self, id):
        global NUM_SMART_METERS
        self.dynamic_bill_dict = dict()
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

        for i in range(1, NUM_SMART_METERS + 1):
            self.dynamic_bill_dict[i] = 0

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

    def update_dynamic_bill_dict(self, meter_id, value,bill_string):
        self.dynamic_bill_dict[int(meter_id)] += int(value) * int(bill_string)

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

    def get_billing_amount(self, num, billing_method):
        amount = 0
        mult = self.delta_func_multiplier
        if billing_method == 3:
            amount += mult * self.dynamic_bill_dict[num]
        else:
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
    print(total_consump)
    eu_conn.sendall(str(total_consump).encode("utf-8"))


def send_aggregators_spatial():
    global AGG_CONNS_SERVER, aggregator
    for conn in AGG_CONNS_SERVER:
        value = aggregator.sumofshares
        conn.sendall(str(value).encode("utf-8"))


def recv_aggregators_spatial(max_buffer_size=5120):
    global AGG_CONNS_CLIENT, aggregator
    for conn in AGG_CONNS_CLIENT:
        input = conn.recv(max_buffer_size)
        while not input:
            input = conn.recv(max_buffer_size)
        decoded_input = input.decode("utf-8")
        aggregator.set_total_consumption(int(float(decoded_input)))


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

def communicate_sm_dynamic(conn,bill_string):
    global sm_connections, NUM_TIME_INSTANCES, aggregator, eu_conn, recv_shares_count
    lock.acquire()
    string = ""
    string += receive_shares(conn)
    shares_time_instances = string.split(" ")
    print(shares_time_instances)
    meter_id = int(shares_time_instances[0])
    aggregator.update_billing_dict(meter_id, shares_time_instances[1])
    aggregator.update_spatial_counter(shares_time_instances[1])
    aggregator.update_dynamic_bill_dict(meter_id, shares_time_instances[1],int(bill_string))
    print(aggregator.dynamic_bill_dict)
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
    while len(AGG_CONNS_SERVER) < num - 1:
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
        value = aggregator.bill_share_value[i]
        print("vale", value)
        conn.sendall(str(value).encode("utf-8"))
    time.sleep(.5)


def recv_aggregators_temporal(i, max_buffer_size=5120):
    global AGG_CONNS_CLIENT, aggregator
    for conn in AGG_CONNS_CLIENT:
        input = conn.recv(max_buffer_size)
        while not input:
            input = conn.recv(max_buffer_size)
        decoded_input = input.decode("utf8")
        lock.acquire()
        aggregator.set_consumption(i, int(float(decoded_input)))
        lock.release()
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

def get_new_price(max_buffer_size=5120):
    global eu_conn
    input = eu_conn.recv(max_buffer_size)
    print(input)
    return input


def receive_data_eu(max_buffer_size=5120):
    global NUM_SMART_METERS, DEGREE, ZP_SPACE, BILL_PRICE
    input = eu_conn.recv(max_buffer_size)
    while not input:
        input = eu_conn.recv(max_buffer_size)
    start = time.time()
    decoded_input = input.decode("utf-8")
    values = decoded_input.split("\n")
    bill_method = int(values[0])
    billing_string = values[1]
    DEGREE = int(values[2])
    ZP_SPACE = int(values[3])
    NUM_SMART_METERS = int(values[4])
    end = time.time()
    print(end - start)
    print(DEGREE, ZP_SPACE, NUM_SMART_METERS)
    return bill_method,billing_string


def send_data_to_sm():
    global sm_connections, DEGREE, ZP_SPACE
    send_string = str(DEGREE) + "\n" + str(ZP_SPACE)
    for conn in sm_connections:
        conn.sendall(send_string.encode("utf-8"))


def create_bill_data(billing_method, billing_string):
    global aggregator
    if billing_method == 1:
        bill_amount = int(billing_string)
        for i in range(1, len(aggregator.consumption_dict) + 1):
            aggregator.consumption_dict[i] = aggregator.consumption_dict[i] * bill_amount
    elif billing_method == 2:
        b_dict= eval(billing_string)
        print(b_dict)
        for i in range(1, len(aggregator.consumption_dict) + 1):
            cost = 0
            val = aggregator.consumption_dict[i]
            sub = 0
            prev_key =0
            for key in b_dict.keys():
                if sub < val:
                    if (val > key and key !=-1):
                        cost +=(key-prev_key) * b_dict.get(key)
                        sub += key - prev_key
                        prev_key = key
                    else:
                        cost +=(val - prev_key) * b_dict.get(key)
                        sub +=(val - prev_key)
            aggregator.consumption_dict[i] = cost

    else:
        for i in range(1, len(aggregator.consumption_dict) + 1):
            print(aggregator.consumption_dict)



def send_bill_data_eu():
    global aggregator, eu_conn
    send_string = ""
    for i in range(1, len(aggregator.consumption_dict) + 1):
        send_string += str(i) + "\n"
        send_string += str(aggregator.consumption_dict[i]) + "\n"
    eu_conn.sendall(send_string.encode("utf-8"))


def send_bill_data_sm(i):
    global sm_connections, aggregator
    bill = aggregator.consumption_dict[i + 1]
    sm_connections[i].sendall(str(bill).encode("utf-8"))


def dynamic_billing(bill_method, bill_string):
    global aggregator, NUM_AGGREGATORS, DEGREE, ZP_SPACE, time_spatial, time_temporal
    send_bill = False
    for i in range(0, NUM_TIME_INSTANCES):
        if i!=0:
            bill_string = int(get_new_price())
            for conn in sm_connections:
                conn.sendall("sendpacket".encode("utf-8"))
        start = time.time()  # uncomment this when checking for time

        for conn in sm_connections:
            conn.send
            try:
                t = Thread(target=communicate_sm_dynamic, args=(conn,bill_string))
                t.start()
            except:
                print("Thread did not start.")
                traceback.print_exc()
            # spatial aggregation
            lock.acquire()
            send_aggregators_spatial()
            recv_aggregators_spatial()
            send_spatial_eu()
            aggregator.reset_spatial()
            lock.release()


    while recv_shares_count < (NUM_TIME_INSTANCES * NUM_SMART_METERS):
        send_bill = False
    send_bill = True
    time.sleep(.5)
    # temporal aggregation
    if send_bill:
        for i in range(1, NUM_SMART_METERS + 1):
            print("Starting memory trace...")
            aggregator.get_billing_amount(i,bill_method)
            start = time.time()  # uncomment this when checking for time
            send_aggregators_temporal(i)
            recv_aggregators_temporal(i)
            end = time.time()  # uncomment this when checking for time
            time.sleep(.25)
            print("Temporal:", end - start - 1)  # uncomment this when checking for time
            time_temporal.append((end - start - 1))
    print(aggregator.consumption_dict)
    start = time.time()
    create_bill_data(bill_method, bill_string)
    end = time.time()
    print(end - start)
    print(aggregator.consumption_dict)
    send_bill_data_eu()

    for i in range(0, NUM_SMART_METERS):
        send_bill_data_sm(i)

def linear_cumulative_bill(bill_method, bill_string):
    global aggregator, NUM_AGGREGATORS, DEGREE, ZP_SPACE, time_spatial, time_temporal
    send_bill = False
    for i in range(0, NUM_TIME_INSTANCES):
        start = time.time()  # uncomment this when checking for time

        for conn in sm_connections:
            try:
                t = Thread(target=communicate_smart_meter, args=(conn,))
                t.start()
            except:
                print("Thread did not start.")
                traceback.print_exc()
            # spatial aggregation
            lock.acquire()
            send_aggregators_spatial()
            recv_aggregators_spatial()
            send_spatial_eu()
            aggregator.reset_spatial()
            lock.release()

    while recv_shares_count < (NUM_TIME_INSTANCES * NUM_SMART_METERS):
        send_bill = False
    send_bill = True
    time.sleep(.5)
    # temporal aggregation
    if send_bill:
        for i in range(1, NUM_SMART_METERS + 1):
            print("Starting memory trace...")
            aggregator.get_billing_amount(i, bill_method)
            start = time.time()  # uncomment this when checking for time
            send_aggregators_temporal(i)
            recv_aggregators_temporal(i)
            end = time.time()  # uncomment this when checking for time
            time.sleep(.25)
            print("Temporal:", end - start - 1)  # uncomment this when checking for time
            time_temporal.append((end - start - 1))
    print(aggregator.consumption_dict)
    start = time.time()
    create_bill_data(bill_method, bill_string)
    end = time.time()
    print(end - start)
    print(aggregator.consumption_dict)
    send_bill_data_eu()

    for i in range(0, NUM_SMART_METERS):
        send_bill_data_sm(i)

    # # write time to files
    # filename_spatial = "/Users/clairecasalnova/PycharmProjects/SmartGrid/SSS/AggregatorFiles/time_spatial_agg" + str(
    #     ID) + ".txt"
    # fs = open(filename_spatial, "w+")
    # for val in time_spatial:
    #     fs.write(str(val) + "\n")
    #
    # filename_temporal = "/Users/clairecasalnova/PycharmProjects/SmartGrid/SSS/AggregatorFiles/time_temporal_agg" + str(
    #     ID) + ".txt"
    # ft = open(filename_temporal, "w+")
    # for val in time_temporal:
    #     ft.write(str(val) + "\n")


def setup():
    global aggregator, NUM_AGGREGATORS, DEGREE, ZP_SPACE, time_spatial, time_temporal
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
        counter += 1

    setup_sm_server(port)


def main():
    global aggregator, NUM_AGGREGATORS, DEGREE, ZP_SPACE, time_spatial, time_temporal
    connect_to_eu()
    bill_method, bill_string =receive_data_eu()
    if bill_method == 3:
        setup()
        dynamic_billing( bill_method, bill_string)
    else:
        setup()
        linear_cumulative_bill( bill_method, bill_string)



if __name__ == '__main__':
    main()
