#!/bin/bash

for d in */ ; do
    echo "$d"
    docker-compose -f $d/docker-compose.yml pull
    docker-compose -f $d/docker-compose.yml down
    docker-compose -f $d/docker-compose.yml up -d
done

docker system prune -af
