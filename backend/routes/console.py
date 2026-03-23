import asyncio
import socket
import struct
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/api/servers", tags=["console"])

def rcon_send(host, port, password, command):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))
    
    auth_packet = struct.pack('<ii', 1, 3) + password.encode() + b'\x00\x00'
    sock.sendall(struct.pack('<i', len(auth_packet)) + auth_packet)
    
    length = struct.unpack('<i', sock.recv(4))[0]
    data = sock.recv(length)
    
    cmd_packet = struct.pack('<ii', 2, 2) + command.encode() + b'\x00\x00'
    sock.sendall(struct.pack('<i', len(cmd_packet)) + cmd_packet)
    
    length = struct.unpack('<i', sock.recv(4))[0]
    data = sock.recv(length)
    response = data[8:-2].decode('utf-8', errors='replace')
    
    sock.close()
    return response

@router.websocket("/{sid}/ws")
async def console(ws: WebSocket, sid: int):
    await ws.accept()
    name = f"mc-panel-{sid}"

    proc = await asyncio.create_subprocess_exec(
        "docker", "inspect", "-f", "{{.State.Status}}", name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    status = stdout.decode().strip()
    
    if status != "running":
        await ws.send_text(f"Server not running ({status})")
        await ws.close()
        return

    stop = False

    async def logs():
        nonlocal stop
        while not stop:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "docker", "logs", "--tail", "50", "-f", name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )
                while not stop:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    text = line.decode("utf-8", errors="replace")
                    if text.strip():
                        await ws.send_text(text)
                if not stop:
                    await asyncio.sleep(1)
            except Exception:
                if not stop:
                    await asyncio.sleep(1)

    task = asyncio.create_task(logs())

    try:
        while True:
            cmd = await ws.receive_text()
            if stop:
                break
            try:
                rcon_port = 25575 + sid
                loop = asyncio.get_event_loop()
                resp = await loop.run_in_executor(None, rcon_send, "localhost", rcon_port, "mcpanel", cmd)
                if resp:
                    await ws.send_text(resp)
            except Exception as e:
                await ws.send_text(f"Error: {e}")
    except WebSocketDisconnect:
        stop = True
        task.cancel()
    except Exception:
        stop = True
        task.cancel()
