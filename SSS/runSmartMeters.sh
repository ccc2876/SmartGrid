#!/bin/bash
i=1
while [ "$i" -le 2 ];do
    python3 SmartMeter.py $i &
    i=$(( i+1 ))
    sleep .02
done
