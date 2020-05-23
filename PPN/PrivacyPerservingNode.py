import sys
import socket
import traceback
import time
from numpy import long
from threading import Thread, Lock


recv_shares_count = 0
config_conn = None
eu_conn = None
NUM_PPNS = 10
NUM_SMART_METERS = 20
NUM_TIME_INSTANCES = 10
sm_conns = []
lock = Lock()
e,s =0,0
times = []

class PPN():
    def __init__(self,id, price):
        self.ID = id
        self.price = price
        self.billing_dict = dict()
        self.consumption_dict = dict()
        self.delta_func_multiplier = 0
        self.spatial_counter = 0
        self.sumofshares = 0
        self.total_consumption = 0

        for i in range(1, NUM_SMART_METERS + 1):
            self.consumption_dict[i] = 0

        for i in range(1, NUM_SMART_METERS + 1):
            self.billing_dict[i] = 0

    def get_ID(self):
        return self.ID


    def calc_sum(self, value):
        """
        calculate the sum of the shares that were sent by adding the value
        :param value: the value that corresponds to the share multiplied by the delta func multiplier of the agg
        :param sm_id: the smart meter id
        """
        self.sumofshares += value

    def get_spatial_counter(self):
        return self.spatial_counter

    def set_total_consumption(self, value):
        self.total_consumption += value

    def update_spatial_counter(self, value):
        self.spatial_counter += int(value)

    def update_billing_dict(self, meter_id, value):
        self.billing_dict[int(meter_id)] += int(value)

    def calculate_lagrange_multiplier(self, num_ppn):
        top = 1
        bottom = 1
        for i in range(1, num_ppn + 1):
            if i != self.get_ID():
                top *= -i
                bottom *= (self.get_ID() - i)
        self.delta_func_multiplier = top / bottom


    def get_lagrange_multiplier(self):
        """
        :return: the lagrange multiplier
        """
        return self.delta_func_multiplier


    def get_billing_amount(self, num):
        amount = 0
        mult = self.delta_func_multiplier
        # print("mult",mult)
        amount += mult * int(self.billing_dict[num])
        # print("amt,", amount)
        self.consumption_dict[num] += amount


def connect_to_config():
    global config_conn
    config_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = "127.0.0.1"
    port = 9000
    try:
        config_conn.connect((host, port))
        print("Connected")
    except:
        print("Connection Error")
        sys.exit()

def connect_to_eu():
    global eu_conn
    eu_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = "127.0.0.1"
    port = 7999
    try:
        eu_conn.connect((host, port))
        print("Connected")
    except:
        print("Connection Error")
        sys.exit()



def get_price(max_buffer_size = 5120):
    global config_conn
    data = config_conn.recv(max_buffer_size)
    data = data.decode("utf-8")
    data = int(data)
    return data


def connect_to_sm(port):
    global NUM_SMART_METERS, sm_conns
    host = "127.0.0.1"
    port_sm = 7000 + port
    s_ppn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket Created")
    s_ppn.bind((host, port_sm))

    print("SM Socket Listening")
    while len(sm_conns) < NUM_SMART_METERS:
        s_ppn.listen()
        conn, addr = s_ppn.accept()
        sm_conns.append(conn)
    print("SM connected")


def receive_shares(conn, max_buffer_size=24):
    input = conn.recv(max_buffer_size)
    decoded_input = input.decode("utf8")
    return decoded_input


def communicate_smart_meter(conn):
    global sm_conns, NUM_TIME_INSTANCES, ppn,recv_shares_count,e,s,times

    lock.acquire()
    s = time.time()
    string = ""
    string += receive_shares(conn)
    shares_time_instances = string.split(" ")
    # print(shares_time_instances)
    meter_id = int(shares_time_instances[0])
    ppn.update_billing_dict(meter_id, shares_time_instances[1])
    ppn.update_spatial_counter(shares_time_instances[1])
    constant = long(ppn.get_spatial_counter()) * long(ppn.get_lagrange_multiplier())
    ppn.calc_sum(constant)
    # print("const", constant)
    ppn.set_total_consumption(ppn.sumofshares)
    recv_shares_count += 1
    # time.sleep(0.015)
    e = time.time()
    # print( e - s)
    lock.release()


def create_bill_data():
    global ppn
    bill_amount = int(ppn.price)
    for i in range(1, len(ppn.consumption_dict) + 1):
        print("i", i , "val", ppn.consumption_dict[i])
        ppn.consumption_dict[i] = ppn.consumption_dict[i] * bill_amount


def send_bill_data_eu():
    global ppn, eu_conn,recv_shares_count
    send_string = ""
    for i in range(1, len(ppn.consumption_dict) + 1):
        send_string += str(i) + "\n"
        send_string += str(ppn.consumption_dict[i]) + "\n"
    eu_conn.sendall(send_string.encode("utf-8"))
    time.sleep(.0002)


def temporal_agg():
    global e, s,times, NUM_SMART_METERS,NUM_TIME_INSTANCES,recv_shares_count,ppn
    send_bill = False

    for i in range(0, NUM_TIME_INSTANCES):
        start = time.time()  # uncomment this when checking for tim
        for conn in sm_conns:
            try:
                t = Thread(target=communicate_smart_meter, args=(conn,))
                t.start()
            except:
                print("Thread did not start.")
                traceback.print_exc()

        end = time.time()
        # print(end-start)

    # time.sleep(0.5)
    # print(recv_shares_count)
    while recv_shares_count < (NUM_TIME_INSTANCES * NUM_SMART_METERS):
        send_bill = False
    send_bill = True

    if send_bill:
        start = time.time()
        for i in range(len(ppn.billing_dict) ):
            ppn.get_billing_amount(i + 1)
        print(ppn.billing_dict)
        print(ppn.consumption_dict)
        send_bill_data_eu()
        end = time.time()
        print(end-start)


def main():
    global ppn,times
    connect_to_config()
    connect_to_eu()
    price = get_price()
    ppn = PPN(int(sys.argv[1]), price)
    ppn.calculate_lagrange_multiplier(NUM_PPNS)
    connect_to_sm(ppn.ID)
    temporal_agg()


if __name__ == '__main__':
    main()