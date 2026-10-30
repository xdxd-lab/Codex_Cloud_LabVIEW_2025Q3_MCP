from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
import datetime
import shutil
root=Path(__file__).parent
automation=Path('/workspace/labview-automation')
extra_get={
 '/labview-mcp.zip': automation/'downloads/labview-mcp-v2.3.1.zip',
 '/automation-install.ps1': automation/'guest/automation-install.ps1',
 '/automation-install.cmd': automation/'guest/automation-install.cmd',
 '/automation-start.cmd': automation/'guest/automation-start.cmd',
 '/mcp_stdio_http.py': automation/'bridge/mcp_stdio_http.py',
}
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  target=extra_get.get(self.path)
  if target is None and self.path in ['/prepare.cmd','/mcp-probe.ps1','/state.cmd','/power.cmd']:target=root/self.path[1:]
  if target is None or not target.is_file():self.send_error(404);return
  self.send_response(200);self.send_header('Content-Length',str(target.stat().st_size));self.end_headers()
  with target.open('rb') as f:shutil.copyfileobj(f,self.wfile,length=1024*1024)
 def do_POST(self):
  if self.path not in ['/bootstrap.log','/trim.log','/mcp-test.json','/state.txt','/power.txt','/automation-state.json']:self.send_error(403);return
  n=int(self.headers.get('Content-Length','0'))
  if n>16*1024**2:self.send_error(413);return
  data=self.rfile.read(n);(root/('guest-'+self.path[1:])).write_bytes(data)
  self.send_response(200);self.send_header('Content-Length','2');self.end_headers();self.wfile.write(b'OK')
 def log_message(self,format,*args):
  with (root/'http.log').open('a') as f:f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+' '+format%args+'\n')
print('Guest transfer helper listening on host loopback:8765',flush=True)
HTTPServer(('127.0.0.1',8765),Handler).serve_forever()
