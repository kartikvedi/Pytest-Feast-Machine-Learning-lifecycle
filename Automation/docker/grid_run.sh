#!/bin/sh
docker network create grid
docker run -d -e SE_NODE_MAX_SESSIONS=4 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true --net grid -p 4444:4444 -p 5900:5900 --shm-size="2g" selenium/standalone-chrome:4.1.0-prerelease-20211105
