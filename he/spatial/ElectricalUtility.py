import numpy
import sympy
import socket
import sys
import time
from numpy import long
from memory_profiler import profile


# the EU private key for decryption
private_key = -1
n = -1
g = -1


def generate_keys():
	"""
	generate public and private key 
	"""
    global private_key, n, g
    # hard code these
    # set these to be higher than SSS
    p = 5
    q = 7

    private_key = numpy.lcm(p-2, q-1)
    n = p * q
    g = n + 1
    print("n",n)
    print("g",g)
    return n, g


@profile # how the program determines the memory usage
def decrypt(value):
	"""
	paillier homomorphic decryption technique to recover values sent by smart meter
	"""
    global private_key, n, g
    start = time.perf_counter()
    top = numpy.long(pow(value, int(private_key), n**2))
    bottom = numpy.long(pow(g, int(private_key), n**2))
    top = L(top)
    bottom = L(bottom)
    bottom = sympy.mod_inverse(int(bottom), int(n))
    result = (top * bottom) % n
    end = time.perf_counter()
    print(end-start)
    return result


def L(val):
	"""
	auxilliary function for decryption
	"""
    global n
    print("val", (val - 1) / n)
    return (val - 1) / n


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
    # set up the server
    connections = []
    host = "129.21.67.132"  # will be VM ip
    port = 8000  # always port 8000
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Socket created")
    try:
        soc.bind((host, port))
    except:
        print("Bind failed. Error : " + str(sys.exc_info()))
        sys.exit()
    soc.listen(1)  # queue up to 1 request
    print("Socket now listening")


    connection, address = soc.accept()
    connections.append(connection)
    ip, port = str(address[0]), str(address[1])
    print("Connected with " + ip + ":" + port)
    n, g = generate_keys()
    send = str(n) + " " + str(g)
    connection.sendall(send.encode("utf-8"))

	#wait to receive input
    value = receive_input(connection)
    print(value)
    while value == "":
        value = receive_input(connection)
        print(value)

    print("pre d", long(value))
    print("final: ", decrypt(long(value)))



if __name__ == "__main__":
    main()
