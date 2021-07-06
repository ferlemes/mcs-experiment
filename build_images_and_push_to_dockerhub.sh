#!/bin/bash

VERSION=1.0.12
IMAGES="enrichment,anomaly-detector,archiver"

echo ${IMAGES} | tr ',' '\n' | while read image_name; do
    docker-compose build ${image_name}
    docker tag ${image_name}:latest kubeowl/${image_name}:${VERSION}
    docker push kubeowl/${image_name}:${VERSION}
done
