import socket
import sys
import random
import time

g = -1
n = -1
price_per_unit = -1
all_readings=[]


def get_readings(billing_method, bill_string):
    global price_per_unit
    # will be read from csv file REMEMBER TO SUM THE ROWS EVENTUALY
    read = random.randint(1, 10)
    if billing_method == 1:
        bill_amount = int(bill_string)
        cost = read * bill_amount
    elif billing_method == 2:
        b_dict= eval(bill_string)
        print(b_dict)
        cost = 0
        val = read
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
    else:
        cost = read * price_per_unit
    return cost


def encrypt(read):
    global g, n
    r = random.randint(1, 1)

    encrypted_val = ((g ** read) * (r ** n)) % (n ** 2)
    # print("e", encrypted_val)
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

    return   decoded_input


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
    start = time.time()
    inp = receive_input(soc)
    inp = inp.split("\n")
    n = int(inp[0])
    g = int(inp[1])
    billing_method = int(inp[2])
    bill_string = inp[3]
    for i in range(0,10):
        value = encrypt(get_readings(billing_method, bill_string))
        # print(value)
        soc.sendall(str(value).encode("utf-8"))
        time.sleep(.0001)


    end = time.time()
    print(end-start)

if __name__ == "__main__":
    main()
