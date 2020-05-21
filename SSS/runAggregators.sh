#!/bin/bash
i=1
while [ "$i" -le 10 ];do
    python3 Aggregator.py $i &
    i=$(( i+1 ))
    sleep .02
done
