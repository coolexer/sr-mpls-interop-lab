#!/usr/bin/env bash
set -euo pipefail

host_ip() {
    nsenter -t "$host_pid" -n ip "$@"
}

for host in 1 2; do
    host_pid=$(docker inspect --format '{{.State.Pid}}' "clab-sr-interop-host${host}")
    host_ip link set eth1 up
    for vlan in 100 200 300; do
        if ! host_ip link show "eth1.${vlan}" >/dev/null 2>&1; then
            host_ip link add link eth1 name "eth1.${vlan}" type vlan id "$vlan"
        fi
        host_ip link set "eth1.${vlan}" up
    done
    host_ip address replace "203.0.113.${host}/26" dev eth1.100
    host_ip address replace "203.0.113.$((64 + host))/26" dev eth1.200
    host_ip -6 address replace "2001:db8:300:${host}::2/64" dev eth1.300
    if [[ "$host" == 1 ]]; then
        host_ip address replace 203.0.113.130/26 dev eth1.300
        host_ip route replace 203.0.113.192/26 via 203.0.113.129 dev eth1.300
        host_ip -6 route replace 2001:db8:300:2::/64 via 2001:db8:300:1::1 dev eth1.300
    else
        host_ip address replace 203.0.113.194/26 dev eth1.300
        host_ip route replace 203.0.113.128/26 via 203.0.113.193 dev eth1.300
        host_ip -6 route replace 2001:db8:300:1::/64 via 2001:db8:300:2::1 dev eth1.300
    fi
done
