__author__ = "Claire Casalnova"

import socket
import sys
import random
import time
from SmartMeter import SmartMeter


def main():

    # set up preprocess information
    aggregator_IDs = []
    connections = []
    time_length = 20
    num_aggs = 2

    # set up the smart meter object
    sm = SmartMeter()
    sm.set_id(int(sys.argv[1]))

    for i in range(0, num_aggs):
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
        time.sleep(1)
        conn.sendall(str(time_length).encode("utf-8"))
        time.sleep(1)
        conn.sendall(str(len(aggregator_IDs)).encode("utf-8"))

    counter = 0
    secrets = []
    # set the degree based on number of aggregators
    sm.set_degree(len(aggregator_IDs) - 1)

    # loop over the time instances
    while counter < time_length:
        secret = random.randint(1, 5)
        sm.set_secret(secret)
        secrets.append(secret)
        sm.create_polynomial()
        shares = []

        # send the shares to the aggregators and record the amount of time that it took
        for i in range(0, len(connections)):
            conn = connections[i]
            agg_id = aggregator_IDs[i]
            single_share_time_start = time.time()
            val = sm.create_shares(agg_id)
            shares.append(val)
            conn.sendall(str(val).encode("utf8"))
            single_share_time_end = time.time()
            sm.add_time(single_share_time_end - single_share_time_start)
            print(single_share_time_end - single_share_time_start)
        counter += 1
    print(sum(secrets))


if __name__ == "__main__":
    main()
