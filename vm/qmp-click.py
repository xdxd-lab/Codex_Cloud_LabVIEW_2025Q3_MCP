import fcntl
import json
import socket
import sys
import time
from PIL import Image

lock = open('/workspace/windows-vm/qmp-client.lock', 'a')
fcntl.flock(lock, fcntl.LOCK_EX)
x, y = map(int, sys.argv[1:3])
with Image.open('/workspace/windows-vm/screen.ppm') as screen:
    width, height = screen.size
assert 0 <= x < width and 0 <= y < height
sock = socket.socket(socket.AF_UNIX)
sock.settimeout(60)
sock.connect('/workspace/windows-vm/qmp.sock')
stream = sock.makefile('rwb')
stream.readline()

def command(name, arguments=None):
    payload = {'execute': name}
    if arguments:
        payload['arguments'] = arguments
    stream.write((json.dumps(payload) + '\n').encode())
    stream.flush()
    while True:
        reply = json.loads(stream.readline())
        if 'error' in reply:
            raise RuntimeError(reply)
        if 'return' in reply:
            return reply['return']

command('qmp_capabilities')
command('input-send-event', {'events': [
    {'type': 'abs', 'data': {'axis': 'x', 'value': round(x * 32767 / (width - 1))}},
    {'type': 'abs', 'data': {'axis': 'y', 'value': round(y * 32767 / (height - 1))}},
]})
command('input-send-event', {'events': [{'type': 'btn', 'data': {'button': 'left', 'down': True}}]})
time.sleep(0.3)
command('input-send-event', {'events': [{'type': 'btn', 'data': {'button': 'left', 'down': False}}]})
print(f'Clicked {x},{y} using absolute QMP input')
