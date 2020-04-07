#!/bin/bash
i=1
while [ "$i" -le 9 ];do
    python3 SmartMeter.py 127.0.0.1 8001 0 &
    i=$(( i+1 ))
    sleep .02
done

