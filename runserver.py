#!/bin/runbang python3 -O $THIS

import os
nofork = 'nofork' in os.environ
if not nofork:
    import socket
    try:
        socket.create_connection(('::1',8029)).close();
    except socket.error: pass
    else:
        raise SystemExit(3)

import sys
import subprocess as s
eu = os.path.expanduser

name = 'imageViewer';
s.call(['killfile',eu('~/tmp/run/'+name+'.pid')])
os.environ['name'] = name;
os.environ['skipcookies'] = '1'
print('oy')
if nofork:
	import myserve
else:
	os.execlp('daemonize','daemonize',
						sys.executable,eu("~/code/image/tagger/myserve.py"))
