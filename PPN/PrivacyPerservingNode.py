import sys
import socket
import traceback
import time
from threading import Thread, Lock

config_conn = None
NUM_SMART_METERS = 2
NUM_TIME_INSTANCES = 1
sm_conns = []

class PPN():
    def __init__(self,id, price):
        self.ID = id
        self.price = price

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
    s_ppn.listen()
    print("SM Socket Listening")
    while len(sm_conns) < NUM_SMART_METERS:
        conn, addr = s_ppn.accept()
        sm_conns.append(conn)
    print("SM connected")


def receive_shares():
    for i in range(0, NUM_TIME_INSTANCES):
        start = time.time()  # uncomment this when checking for time

        for conn in sm_conns:
            try:
                t = Thread(target=communicate_smart_meter, args=(conn,))
                t.start()
            except:
                print("Thread did not start.")
                traceback.print_exc()


def main():
    connect_to_config()
    price = get_price()
    ppn = PPN(int(sys.argv[1]), price)
    connect_to_sm(ppn.ID)
    receive_shares()


if __name__ == '__main__':
    main()