import numpy
import libnum
import socket
import sys
import time
import json
from random import randint
from numpy import long
from memory_profiler import profile


# the EU private key for decryption
n = -1
g = -1
r = -1
L =-1
gMu = -1
num_sm = 2
consumption = 0
gLambda = 0


def generate_keys():
    """
    generate public and private key
    """
    global  n, g, gLambda, l , gMu,r
    # # hard code these
    # # set these to be higher than SSS
    p = 5
    q = 7
    gLambda = int(numpy.lcm(p-2, q-1))
    g = randint(20, 100)
    if (numpy.gcd(g, n * n) == 1):
        print("g is relatively prime to n*n")
    else:
        print("WARNING: g is NOT relatively prime to n*n. Will not work!!!")

    n = p * q
    r = randint(20,150)
    l = (pow(g, gLambda, n * n) - 1) // n
    gMu = libnum.invmod(l, n)

    print("Public key (n,g):\t\t", n, g)
    print("Private key (lambda,mu):\t", gLambda, gMu)

    l = (pow(g, gLambda, n * n) - 1) // n
    gMu = libnum.invmod(l, n)
    return n, g, r



def decrypt(value):
    """
    paillier homomorphic decryption technique to recover values sent by smart meter
    """
    global private_key, n, g,gMu
    start = time.perf_counter()
    l = (pow(value, gLambda, n*n)-1) // n
    mess = (l * gMu) % n
    end = time.perf_counter()
    print(end-start)
    return mess



def receive_input(connection, max_buffer_size = 5120):
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
    result = process_input(decoded_input)
    return result


def process_input(input_str):
    """
    convert the input to uppercase
    :param input_str: the client input from the smart meter
    :return: the input converted the uppercase
    """
    return str(input_str).upper()


def main():
    global consumption, num_sm, n, g, r
    # set up the server
    connections = []
    host = "127.0.0.1"  # will be VM ip
    port = 8000  # always port 8000
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Socket created")
    try:
        soc.bind((host, port))
    except:
        print("Bind failed. Error : " + str(sys.exc_info()))
        sys.exit()
    soc.listen()  # queue up to 1 request
    print("Socket now listening")
    generate_keys()

    while len(connections) < num_sm:
        connection, address = soc.accept()
        connections.append(connection)
        ip, port = str(address[0]), str(address[1])
        print("Connected with " + ip + ":" + port)

        send = str(n) + " " + str(g) + " " + str(r)
        connection.sendall(send.encode("utf-8"))


    for connection in connections:
        #wait to receive input
        value = receive_input(connection)
        print(value)
        while value == "":
            value = receive_input(connection)
            print(value)
        consumption = decrypt(int(value))

    print("Final:", consumption)


if __name__ == "__main__":
    main()