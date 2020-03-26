__author__ = "Claire Casalnova"

import socket
import sys
import traceback
from sss.ElectricalUtility import ElectricalUtility
from threading import Thread,Lock
import time


DELIMITER = "\n"
print_lock = Lock()
print_cycle = 1
num_aggs = 2
num_sm = 1
threads =[]
finished = False


def main():
    global finished
    eu = ElectricalUtility()
    eu.set_num_sm(int(num_sm))
    start_server(eu)
    while not finished:
        for x in threads:
            if not x.is_alive():
                finished = True
            else:
                finished = False
    if finished:
        billing(eu)



def billing(eu):
    print_lock.acquire()
    eu.get_total_amount()

    bills = eu.get_bills()
    for i in range(0, len(bills)):
        print("Bill amount for SM #", i+1, ": ", bills[i])

    print_lock.release()

def start_server(eu):
    """
    set up the connection to each of the aggregators
    start a thread for each connection
    """
    connections = []
    host = "127.0.0.1"
    port = 8000  # arbitrary non-privileged port
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Socket created")
    try:
        soc.bind((host, port))
    except:
        print("Bind failed. Error : " + str(sys.exc_info()))
        sys.exit()
    soc.listen()  # queue up to 6 requests
    print("Socket now listening")

    while len(connections) < num_aggs:
        connection, address = soc.accept()
        connections.append(connection)
        eu.set_num_aggs(len(connections))
        ip, port = str(address[0]), str(address[1])
        print("Connected with " + ip + ":" + port)
        try:
            t = Thread(target=clientThread, args=(connection,eu, ip, port))
            threads.append(t)
            t.start()

        except:
            print("Thread did not start.")
            traceback.print_exc()



def clientThread(connection, eu, ip, port, max_buffer_size=5120):
    """
    thread for each connection to an aggregator
    :param connection: the specific connection
    :param eu: the utility company object
    :param ip: the ip address of the connection
    :param port: the port of the connection
    :param max_buffer_size: the max buffer size set to 5120
    """

    global print_cycle
    sm_num = receive_input(connection, max_buffer_size)
    sm_num = int(sm_num[0])
    is_active = True
    counter = 1
    while is_active:
        # receive the input from the aggregators and process it in the utility company object
        client_input = receive_input(connection, max_buffer_size)
        counter += 1

        if client_input != ['']:
            print_lock.acquire()
            num_aggs_input = int(client_input[0])
            sm_id = int(client_input[1])
            value = int(client_input[2])
            eu.set_num_aggs(int(num_aggs_input))
            eu.set_spatial_sum(value)
            eu.generate_bill(sm_id, value)

            time.sleep(1)
            print_lock.release()
        else:
            if print_cycle % num_aggs == 0:
                print_lock.acquire()
                print_cycle = 1
                is_active = False
                print_lock.release()

            else:
                print_lock.acquire()
                print_cycle += 1
                print_lock.release()


def receive_input(connection, max_buffer_size):
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
    decoded_input = client_input.decode("utf8").split(DELIMITER)
    return decoded_input


if __name__ == "__main__":
    main()
