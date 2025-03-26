#!/bin/bash
# Author: Mitchell Kerns

sudo docker run --rm -it --network host -v ~/.pcredz:/root/.pcredz snovvcrash/pcredz -i eth0
