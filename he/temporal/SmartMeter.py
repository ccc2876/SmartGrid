import socket
import sys
import random

g = -1
n = -1
price_per_unit = -1
all_readings=[]


def get_readings():
    global price_per_unit
    # will be read from csv file REMEMBER TO SUM THE ROWS EVENTUALY
    read = random.randint(1, 10)
    read = read * price_per_unit
    print("Read", read)
    return read


def encrypt(read):
    global g, n
    r = random.randint(1, 1)

    encrypted_val = ((g ** read) * (r ** n)) % (n ** 2)
    print("e", encrypted_val)
    return encrypted_val


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
    global price_per_unit, n, g
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "127.0.0.1"
    port = 8000

    try:
        soc.connect((host, int(port)))
        port += 1
    except:
        print("Connection Error")
        sys.exit()

    inp = receive_input(soc)
    inp = inp.split(" ")
    price_per_unit = int(inp[0])
    n = int(inp[1])
    g = int(inp[2])
    value = encrypt(get_readings())
    print(value)
    soc.sendall(str(value).encode("utf-8"))




if __name__ == "__main__":
    main()
