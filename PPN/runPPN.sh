#!/bin/bash
i=1
while [ "$i" -le 10 ];do
    python3 PrivacyPerservingNode.py $i &
    i=$(( i+1 ))
    sleep .02
done