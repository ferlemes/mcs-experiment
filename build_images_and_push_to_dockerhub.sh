#!/bin/bash

docker-compose build

VERSION=1.0.1

docker tag syslog:latest kubeowl/syslog:${VERSION}
docker push kubeowl/syslog:${VERSION}

docker tag evaluator:latest kubeowl/evaluator:${VERSION}
docker push kubeowl/evaluator:${VERSION}

docker tag request-recorder:latest kubeowl/request-recorder:${VERSION}
docker push kubeowl/request-recorder:${VERSION}

