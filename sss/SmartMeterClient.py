__author__ = "Claire Casalnova"

import socket
import sys
import random
import time
from sympy import isprime
from sss.SmartMeter import SmartMeter

NUM_AGGS = 2


def main():
    # set up preprocess information
    aggregator_IDs = []
    connections = []

    max_time_consumption = 10
    max_coefficient = 4
    max_agg_id = 3
    num_time_instances = 1
    max_total_consumption = num_time_instances * max_time_consumption
    zp_space = max_total_consumption * num_time_instances

    zp = zp_space + 1
    while not isprime(zp):
        zp += 1
    print(zp)

    # set up the smart meter object
    sm = SmartMeter()
    sm.set_id(int(sys.argv[1]))
    name = "sm" + ".txt"
    f = open(name, "a+")
    print(sys.argv[1])
    sm.set_zp_space(zp_space)

    for i in range(0, NUM_AGGS):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connections.append(soc)
    host = "127.0.0.1"
    port = 8001

    try:
        for conn in connections:
            conn.connect((host, port))
            port += 1
    except:
        print("Connection Error")
        sys.exit()

    # receive aggregator ID information from the Aggregators
    for conn in connections:
        agg_id = int(conn.recv(5120).decode("utf8"))
        aggregator_IDs.append(agg_id)

    # send the id of the smart meter, the time period and the num of aggs to the aggregators
    for conn in connections:
        conn.sendall(str(sm.get_ID()).encode("utf-8"))
        time.sleep(1.5)
        conn.sendall(str(num_time_instances).encode("utf-8"))
        time.sleep(1.5)
        conn.sendall(str(len(aggregator_IDs)).encode("utf-8"))
        time.sleep(1.5)
        conn.sendall(str(zp_space).encode("utf-8"))

    counter = 0
    secrets = []
    # set the degree based on number of aggregators
    sm.set_degree(len(aggregator_IDs) - 1)

    # loop over the time instances
    while counter < num_time_instances:
        print("Generating secret...")
        secret = random.randint(1, max_time_consumption)
        sm.set_secret(secret)
        secrets.append(secret)
        sm.create_polynomial(max_coefficient)
        shares = []

        # send the shares to the aggregators and record the amount of time that it took
        start = time.time()
        for i in range(0, len(connections)):
            conn = connections[i]
            agg_id = aggregator_IDs[i]
            single_share_time_start = time.time()
            val = sm.create_shares(agg_id)
            shares.append(val)
            val = val
            print("sending val:", val)
            conn.sendall(str(val).encode("utf8"))
            single_share_time_end = time.time()
            sm.add_time(single_share_time_end - single_share_time_start)

        counter += 1
    end = time.time()
    #f.write(str(end - start) + "\n")
    print(sum(secrets))
    f.close()


if __name__ == "__main__":
    main()

