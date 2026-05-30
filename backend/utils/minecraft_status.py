import json
import socket


def _encode_varint(value: int) -> bytes:
    data = bytearray()
    value &= 0xFFFFFFFF
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            data.append(byte | 0x80)
        else:
            data.append(byte)
            break
    return bytes(data)


def _read_exact(sock: socket.socket, length: int) -> bytes:
    data = bytearray()
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed while reading Minecraft status response")
        data.extend(chunk)
    return bytes(data)


def _read_varint(sock: socket.socket) -> int:
    num_read = 0
    result = 0
    while True:
        byte = _read_exact(sock, 1)[0]
        result |= (byte & 0x7F) << (7 * num_read)
        num_read += 1
        if num_read > 5:
            raise ValueError("Minecraft status VarInt is too large")
        if (byte & 0x80) == 0:
            break
    return result


def query_minecraft_status(host: str, port: int, timeout: float = 2.0) -> dict:
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)

        host_bytes = host.encode("utf-8")
        handshake_payload = b"".join(
            [
                _encode_varint(0x00),
                _encode_varint(47),
                _encode_varint(len(host_bytes)),
                host_bytes,
                port.to_bytes(2, "big", signed=False),
                _encode_varint(1),
            ]
        )
        sock.sendall(_encode_varint(len(handshake_payload)) + handshake_payload)

        request_payload = _encode_varint(0x00)
        sock.sendall(_encode_varint(len(request_payload)) + request_payload)

        _read_varint(sock)
        packet_id = _read_varint(sock)
        if packet_id != 0x00:
            raise ValueError(f"Unexpected Minecraft status packet id: {packet_id}")

        json_length = _read_varint(sock)
        response = _read_exact(sock, json_length).decode("utf-8", errors="replace")
        return json.loads(response)
