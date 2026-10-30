import fcntl
qmp_client_lock = open("/workspace/windows-vm/qmp-client.lock", "a")
fcntl.flock(qmp_client_lock, fcntl.LOCK_EX)
import socket,json,sys,time
s=socket.socket(socket.AF_UNIX);s.settimeout(60);s.connect('/workspace/windows-vm/qmp.sock');f=s.makefile('rwb')
def recv(): return json.loads(f.readline())
def command(name,args=None):
 payload={'execute':name}
 if args:payload['arguments']=args
 f.write((json.dumps(payload)+'\n').encode());f.flush()
 while True:
  r=recv()
  if 'return' in r or 'error' in r:return r
recv();command('qmp_capabilities')
if sys.argv[1]=='screen':print(command('screendump',{'filename':'/workspace/windows-vm/screen.ppm'}))
elif sys.argv[1]=='key':
 print(command('human-monitor-command',{'command-line':'sendkey '+sys.argv[2]}));time.sleep(0.25)
else:print(command(sys.argv[1],json.loads(sys.argv[2]) if len(sys.argv)>2 else None))
