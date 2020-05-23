import socket
import sys

eu_conn = None
NUM_PPN = 10
ppn_conns = []
config = None

class Configurator:
    def __init__(self, price):
        self.billing_price = price

    def get_price(self):
        return self.billing_price



def connect_to_eu():
    global eu_conn
    eu_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = "127.0.0.1"
    port = 8000
    try:
        eu_conn.connect((host, port))
        print("Connected")
    except:
        print("Connection Error")
        sys.exit()

def connect_to_ppns():
    global NUM_PPN
    host = "127.0.0.1"
    port_sm = 9000
    s_ppn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket Created")
    s_ppn.bind((host, port_sm))
    s_ppn.listen()
    print("PPN Socket Listening")
    while len(ppn_conns) < NUM_PPN:
        conn, addr = s_ppn.accept()
        ppn_conns.append(conn)
    print("Configurator connected")


def get_price(max_buffer_size = 5120):
    global eu_conn
    data = eu_conn.recv(max_buffer_size)
    data = data.decode("utf-8")
    data = int(data)
    return data


def send_price():
    global ppn_conns, config
    for conn in ppn_conns:
        conn.sendall(str(config.get_price()).encode("utf-8"))

def main():
    global config
    connect_to_eu()
    connect_to_ppns()
    price = get_price()
    config = Configurator(price)
    send_price()
    print(config.get_price())


if __name__ == '__main__':
    main()