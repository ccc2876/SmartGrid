import sys
import socket
import numpy
import sympy
import time
from memory_profiler import profile

#implement once per month
#implement and every time instance

num_sm = 20
price_per_unit = 1
# the EU private key for decryption
private_key = -1
n = -1
g = -1

class ElectricalUtility:
    def __init__(self, billing_method, bill_string):
        self.bills_dict = dict()
        self.billing_method = billing_method

        for i in range(1, num_sm + 1):
            self.bills_dict[i] = 0

        if billing_method == 1:
            self.bill_price = int(bill_string)
        elif billing_method == 2:
            bills = bill_string.split(";")
            self.price_dict = {}
            for entry in bills:
                keyval = entry.split(",")
                key = int(keyval[0])
                val = int(keyval[1])
                self.price_dict.__setitem__(key, val)
        else:
            self.bill_price = int(bill_string)

def generate_keys():
    global private_key, n, g
    # hard code these
    # set these to be higher than SSS
    p = 5
    q = 7

    private_key = numpy.lcm(p-1, q-1)
    n = p * q
    g = n + 1
    print("n",n)
    print("g",g)
    return n, g

def decrypt(value):
    global private_key, n, g
    top = numpy.long(pow(value, int(private_key), n**2))
    bottom = numpy.long(pow(g, int(private_key), n**2))
    top = L(top)
    bottom = L(bottom)
    bottom = sympy.mod_inverse(int(bottom), int(n))
    result = (top * bottom) % n
    return result


def L(val):
    global n
    return (val - 1) // n


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


def main(billing_method,bill_string):
    eu =ElectricalUtility(billing_method,bill_string)
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
    soc.listen(5)  # queue up to 5 requests
    print("Socket now listening")

    generate_keys()
    while len(connections) < num_sm:
        connection, address = soc.accept()
        connections.append(connection)
        ip, port = str(address[0]), str(address[1])
        print("Connected with " + ip + ":" + port)
    start =time.time()

    for conn in connections:
        total = 0
        value = 0
        if eu.billing_method == 1:
            send_string = str(n) + "\n" + str(g) + "\n" +str(billing_method) + "\n" + str(eu.bill_price)
        elif eu.billing_method == 2:
            send_string = str(n) + "\n" + str(g) + "\n" + str(billing_method) + "\n" + str(eu.price_dict)
        else:
            send_string = str(n) + "\n" + str(g) + "\n" + str(billing_method) + "\n" + str(eu.bill_price)

        conn.sendall(str(send_string).encode("utf-8"))
        for i in range(0,10):
            value = receive_input(conn)
            print(value)
            while value == "":
                value = receive_input(conn)
            print(value)
            total*=int(value)
        print("Bill: ", decrypt(int(total)))
    end= time.time()
    print(end-start)



if __name__ == "__main__":
    print("Please enter the number for the preferred billing method:   ")
    print("\t1. linear")
    print("\t2. cumulative")
    print("\t3. dynamic")
    billing_method = int(input())
    if billing_method == 1:
        print("Please enter the price per unit: ")
        bill_string = input()
    elif billing_method == 2:
        print("Please enter billing chart in the form \n\t5,2;10,3;15,1\n"
              "Where the first number is the max value for that range and the second value is the price per unit in that range\n"
              "Enter -1 for infinity")
        bill_string = input()
    else:
        print("Please enter the price for the first time instance:")
        bill_string = input()
    main(billing_method, bill_string)
