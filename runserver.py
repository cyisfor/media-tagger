#!/usr/bin/env pypy3

import os
if not 'nofork' in os.environ:
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
os.execlp('daemonize','daemonize',
          sys.executable,eu("~/code/image/tagger/myserve.py"))
