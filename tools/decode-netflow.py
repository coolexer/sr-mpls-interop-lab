import ipaddress
import re
import struct
import sys

templates = {}
seen = set()
for line in open(sys.argv[1], encoding="ascii"):
    if line.startswith("v"):
        message = re.match(r"v(\d+) (\S+) -> (\d+)", line)
        version, source, port = int(message[1]), message[2], int(message[3])
    elif line.startswith("  set "):
        flowset, raw = line.removeprefix("  set ").split(":", 1)
        set_id, data = int(flowset), bytes.fromhex(raw)
        if (version, set_id) in {(10, 2), (9, 0)}:
            offset = 0
            while offset + 4 <= len(data):
                template, count = struct.unpack_from("!HH", data, offset)
                offset += 4
                fields = []
                for _ in range(count):
                    field, size = struct.unpack_from("!HH", data, offset)
                    offset += 4
                    enterprise = 0
                    if version == 10 and field & 0x8000:
                        enterprise = struct.unpack_from("!I", data, offset)[0]
                        field &= 0x7fff
                        offset += 4
                    fields.append((enterprise, field, size))
                templates[version, source, port, template] = fields
        elif set_id >= 256:
            fields = templates.get((version, source, port, set_id), [])
            width = sum(field[2] for field in fields)
            if not width or not any(e == 0 and 70 <= f <= 79 for e, f, _ in fields):
                continue
            for start in range(0, (len(data) // width) * width, width):
                offset = start
                record = {}
                for enterprise, field, length in fields:
                    value = data[offset:offset + length]
                    offset += length
                    if enterprise == 0:
                        record[field] = value
                labels = []
                for label_field in range(70, 80):
                    value = record.get(label_field)
                    if not value:
                        break
                    word = int.from_bytes(value, "big")
                    labels.append(word >> (4 if len(value) == 3 else 12))
                    if word & (1 if len(value) == 3 else 256):
                        break
                src_port = int.from_bytes(record.get(7, b""), "big")
                direction = int.from_bytes(record.get(61, b""), "big")
                ingress = int.from_bytes(record.get(10, b""), "big")
                dst = str(ipaddress.ip_address(record[12])) if 12 in record else "absent"
                outcome = (version, port, set_id, src_port, dst, direction, ingress, tuple(labels))
                if outcome not in seen:
                    print(f"v{version} collector-port={port}, template={set_id}, src-port={src_port}, destination={dst}, direction={direction}, ingress={ingress}, MPLS labels={labels}")
                    seen.add(outcome)
