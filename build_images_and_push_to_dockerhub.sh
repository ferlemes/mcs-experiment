#!/bin/bash

docker-compose build

VERSION=1.0.6

docker tag enrichment:latest kubeowl/enrichment:${VERSION}
docker push kubeowl/enrichment:${VERSION}

docker tag response-time-evaluator:latest kubeowl/response-time-evaluator:${VERSION}
docker push kubeowl/response-time-evaluator:${VERSION}
