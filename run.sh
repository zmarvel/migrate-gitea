#!/bin/bash

set -u -e -o pipefail

docker build -t migrate-gitea .
docker run \
    --rm \
    -v $(pwd):/app \
    --name migrate-gitea \
    --net=host \
    -it migrate-gitea /bin/bash
