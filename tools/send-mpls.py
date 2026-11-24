import socket
import struct
import sys

def checksum(data):
    total = sum(struct.unpack(f"!{len(data) // 2}H", data))
    while total >> 16:
        total = (total & 0xffff) + (total >> 16)
    return (~total) & 0xffff

interface, target_mac = sys.argv[1:]
with open(f"/sys/class/net/{interface}/address", encoding="ascii") as source_mac:
    ethernet = bytes.fromhex(target_mac.replace(":", "") + source_mac.read().strip().replace(":", "")) + b"\x88\x47"
with socket.socket(socket.AF_PACKET, socket.SOCK_RAW) as sender:
    sender.bind((interface, 0))
    for labels in ((24501,), (24501, 7, 12345, 0)):
        stack = b"".join(struct.pack("!I", label << 12 | (index == len(labels) - 1) << 8 | 64) for index, label in enumerate(labels))
        payload = b"SR-MPLS IPFIX test"
        udp = struct.pack("!HHHH", 6000 + len(labels), 6000, 8 + len(payload), 0) + payload
        ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + len(udp), len(labels), 0, 64, 17, 0, socket.inet_aton("198.18.0.0"), socket.inet_aton("203.0.113.101"))
        ip = ip[:10] + struct.pack("!H", checksum(ip)) + ip[12:]
        for _ in range(60):
            sender.send(ethernet + stack + ip + udp)
