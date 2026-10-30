import fcntl
qmp_client_lock = open("/workspace/windows-vm/qmp-client.lock", "a")
fcntl.flock(qmp_client_lock, fcntl.LOCK_EX)
import socket,json,sys,time
s=socket.socket(socket.AF_UNIX);s.settimeout(60);s.connect('/workspace/windows-vm/qmp.sock');f=s.makefile('rwb');f.readline()
def cmd(name,args=None):
 o={'execute':name}
 if args:o['arguments']=args
 f.write((json.dumps(o)+'\n').encode());f.flush()
 while True:
  r=json.loads(f.readline())
  if 'return' in r or 'error' in r:return r
cmd('qmp_capabilities')
m={' ':'spc','\n':'ret','\\':'backslash',':':'shift-semicolon','.':'dot','/':'slash','-':'minus','_':'shift-minus','"':'shift-apostrophe','=':'equal','>':'shift-dot','|':'shift-backslash','(':'shift-9',')':'shift-0',',':'comma',';':'semicolon',"'":'apostrophe','?':'shift-slash','&':'shift-7','!':'shift-1','$':'shift-4','%':'shift-5','+':'shift-equal','*':'shift-8','[':'bracket_left',']':'bracket_right','{':'shift-bracket_left','}':'shift-bracket_right'}
for c in sys.argv[1]:
 key=m.get(c,('shift-'+c.lower()) if c.isupper() else c)
 r=cmd('human-monitor-command',{'command-line':'sendkey '+key+' 100'})
 if 'error' in r:raise RuntimeError(r)
 time.sleep(.2)
