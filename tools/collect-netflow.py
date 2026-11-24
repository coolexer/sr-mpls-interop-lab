import selectors
import socket
import struct
import time

collector = selectors.DefaultSelector()
for port in (2055, 4739):
    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listener.bind(("0.0.0.0", port))
    collector.register(listener, selectors.EVENT_READ, port)
deadline = time.monotonic() + 145
print("Listening for NetFlow v9 and IPFIX", flush=True)
while (remaining := deadline - time.monotonic()) > 0:
    for key, _ in collector.select(remaining):
        packet, peer = key.fileobj.recvfrom(65535)
        version = struct.unpack_from("!H", packet)[0]
        header = 16 if version == 10 else 20
        print(f"v{version} {peer[0]}:{peer[1]} -> {key.data}, {len(packet)} bytes", flush=True)
        index = header
        while index + 4 <= len(packet):
            set_id, length = struct.unpack_from("!HH", packet, index)
            if length < 4 or index + length > len(packet):
                break
            print(f"  set {set_id}: {packet[index + 4:index + length].hex()}", flush=True)
            index += length
