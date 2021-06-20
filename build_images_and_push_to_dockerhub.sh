#!/bin/bash

docker-compose build

VERSION=1.0.5

docker tag syslog:latest kubeowl/syslog:${VERSION}
docker push kubeowl/syslog:${VERSION}

docker tag enrichment:latest kubeowl/enrichment:${VERSION}
docker push kubeowl/enrichment:${VERSION}

docker tag model-trainer:latest kubeowl/model-trainer:${VERSION}
docker push kubeowl/model-trainer:${VERSION}

docker tag model-evaluator:latest kubeowl/model-evaluator:${VERSION}
docker push kubeowl/model-evaluator:${VERSION}
