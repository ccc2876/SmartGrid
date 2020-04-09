import random
import socket
import sys
import traceback
import time
import json
from phe import paillier
from numpy import long
from queue import Queue
from threading import Thread, Lock

#
g = -1
n = -1
r= -1
total_count = 0
num_sm = 2
total_readings = 1
time_instances = 2
server_done = False
SM_CONN_SERVER = []
SM_CONN_CLIENT = []
eu_conn = None
lock = Lock()



def get_readings():
    # will be read from csv file REMEMBER TO SUM THE ROWS EVENTUALY
    read = random.randint(1, 10)
    print("Read", int(read))
    return read


def encrypt(read):
    global g, n,r
    # start = time.time()
    print("Message:\t", read)
    k1 = pow(g, read, n * n)
    k2 = pow(r, n, n * n)
    cipher = (k1 * k2) % (n * n)
    print(cipher)
    return cipher


def receive_input(connection, max_buffer_size=5120):
    """
    function for receiving and decoding input from the smart meters
    :param connection: the connection the smart meter
    :param max_buffer_size: the max buffer size of receiving input
    :return: the decoded input
    """
    client_input = connection.recv(max_buffer_size)
    client_input_size = sys.getsizeof(client_input)
    if client_input_size > max_buffer_size:
        print("The input size is greater than expected {}".format(client_input_size))
    decoded_input = client_input.decode("utf8").rstrip()
    print("Dec", decoded_input)
    return decoded_input


def get_key(soc):
    global n, g
    inp = receive_input(soc)
    values = inp.split(" ")
    n = int(values[0])
    g = int(values[1])
    r = int(values[2])
    print("pub", n, g)
    public_key = str(n) + " " + str(g) + " "  +str(r)
    return public_key



def send_final(soc):
    global total_readings
    print("Final send:", total_readings)
    lock.acquire()
    soc.sendall(str(total_readings).encode("utf-8"))
    lock.release()

def sm_server_setup(host, port):
    global SM_CONN_SERVER
    TCP_IP = host
    TCP_PORT = port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    print("Socket Created")
    print(TCP_IP, " ", TCP_PORT)
    s.bind((TCP_IP, TCP_PORT))
    s.listen()
    print("Socket Listening")
    while len(SM_CONN_SERVER) < num_sm - 1:
        conn, addr = s.accept()
        SM_CONN_SERVER.append(conn)
        print('Connected to :', addr[0], ':', addr[1])
    print("All SM connected")

def connect_to_sm_as_client(host, port):
    global SM_CONN_CLIENT
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SM_CONN_CLIENT.append(soc)
    if not (port == int(sys.argv[1]) + 8000):
        try:
            soc.connect((host, port))
        except:
            print("Connection Error")
            sys.exit()


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



def send_to_sm(encrypted):
    global SM_CONN_SERVER,total_readings
    total_readings*= encrypted
    print("Cipher:\t\t", encrypted)
    for conn in SM_CONN_SERVER:
        conn.sendall(str(total_readings).encode("utf-8"))


def recv_from_sm(max_buffer_size=5120):
    global SM_CONN_CLIENT,total_readings, n
    for conn in SM_CONN_CLIENT:
        inp = conn.recv(max_buffer_size)
        while not inp:
            inp = conn.recv(max_buffer_size)
        decoded_input = inp.decode("utf-8")
        value = int(decoded_input)
        total_readings*= value
        total_readings = total_readings % (n * n )


def main():
    global n, g, time_instances, eu_conn,total_readings
    counter = 1
    host = "127.0.0.1"
    ID = int(sys.argv[1])
    print(counter, " ", ID)
    port = ID + 8000

    for i in range(0, num_sm):
        sm_port = 8000 + counter
        if ID == counter:
            sm_server_setup(host, port)
        else:
            time.sleep(1)
            connect_to_sm_as_client(host, sm_port)
        counter += 1

    connect_to_eu()
    get_key(eu_conn)

    for i in range(0,time_instances):
        val = get_readings()
        encrypted = encrypt(val)
        send_to_sm(encrypted)
        recv_from_sm()
        time.sleep(1)
        print(total_readings)
    send_final(eu_conn)







if __name__ == '__main__':
    main()
