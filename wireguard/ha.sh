#!/bin/bash

read -sp 'Enter password:'
docker run ghcr.io/wg-easy/wg-easy:14 wgpw $REPLY
