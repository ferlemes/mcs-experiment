#!/bin/bash

docker-compose build

VERSION=1.0.4

docker tag syslog:latest kubeowl/syslog:${VERSION}
docker push kubeowl/syslog:${VERSION}

