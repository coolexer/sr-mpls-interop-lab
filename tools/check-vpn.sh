#!/usr/bin/env bash
set -u

status=0
for destination in 203.0.113.194 2001:db8:300:2::2; do
    docker exec clab-sr-interop-host1 ping -c 3 -W 2 "$destination" || status=1
done
exit "$status"
