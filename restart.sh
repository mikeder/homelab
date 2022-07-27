#!/bin/bash

for d in */ ; do
    echo "$d"
    docker-compose -f $d/docker-compose.yml restart
done
