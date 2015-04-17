request = '''GET / HTTP/1.1
User-Agent: curl/7.38.0
Host: 127.0.0.1:8934
Accept: */*

'''.replace('\n','\r\n').encode('utf-8')

import socket

def hammer(i):
    s = socket.create_connection(('127.0.0.1',8934))
    for i in range(10):
        s.send(request)

    while True:
        print(s.recv(16).decode('utf-8'))

import multiprocessing
multiprocessing.Pool(4).map(hammer,range(4))
