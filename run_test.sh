#!/bin/sh

docker run --network=hello-chih-hsiang_example -v "$(pwd)/app":"/usr/src/app" -it hello-chih-hsiang_app pytest