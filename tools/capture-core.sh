#!/usr/bin/env bash
set -euo pipefail

mkdir -p test-output
containerlab capture --name sr-interop \
    --target pe2:Gi0-0-0-0 --target pe2:Gi0-0-0-1 \
    --duration 10s -w test-output/core.pcapng
