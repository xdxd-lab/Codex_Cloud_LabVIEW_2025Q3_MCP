import fcntl
qmp_client_lock = open("/workspace/windows-vm/qmp-client.lock", "a")
fcntl.flock(qmp_client_lock, fcntl.LOCK_EX)
import socket,json,time,shutil,subprocess
from pathlib import Path
s=socket.socket(socket.AF_UNIX);s.settimeout(60);s.connect('/workspace/windows-vm/qmp.sock')
f=s.makefile('rwb');f.readline()
def cmd(n,a=None):
 d={'execute':n}
 if a:d['arguments']=a
 f.write((json.dumps(d)+'\n').encode());f.flush()
 while True:
  r=json.loads(f.readline())
  if 'return' in r or 'error' in r:return r
cmd('qmp_capabilities')
status=cmd('query-status')
devices={x['device']:x['stats'] for x in cmd('query-blockstats')['return'] if x.get('device')}
b=devices['ide0-hd0']
cmd('screendump',{'filename':'/workspace/windows-vm/screen.ppm'})
f.close();s.close()
o=subprocess.run(['tesseract','/workspace/windows-vm/screen.ppm','stdout','-l','eng','--psm','11'],capture_output=True,text=True).stdout.strip().replace('\n',' ')
r={'time':time.strftime('%H:%M:%S',time.gmtime()),'state':status,'free_GiB':round(shutil.disk_usage('/workspace').free/1024**3,2),'read_MB':round(b['rd_bytes']/1024**2),'written_MB':round(b['wr_bytes']/1024**2),'failed_writes':b.get('failed_wr_operations'),'devices':{n:{'read_MB':round(v['rd_bytes']/1024**2),'written_MB':round(v['wr_bytes']/1024**2)} for n,v in devices.items()},'screen':o}
t=json.dumps(r,ensure_ascii=False);print(t)
with open('/workspace/windows-vm/install-monitor.jsonl','a') as log:log.write(t+'\n')
