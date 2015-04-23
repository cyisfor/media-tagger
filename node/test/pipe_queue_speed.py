#!/usr/bin/env pypy

import multiprocessing as m
import sys,os,time

numtosend = 0x10000

def stat(s):
    return
    sys.stdout.write(s+'\n')
    sys.stdout.flush()
            
class Process(m.Process):
    def __init__(self,send,receive):
        super().__init__()
        self.send = send
        self.receive = receive
        self.start()
    def run(self):
        for i in range(numtosend):
            v = self.receive()
            stat('s-')
            self.send(v<<1)
            stat('s+')

def doOne(name,send1,receive1,send2,receive2):
    print('name',name)
    start = time.time()
    p = Process(send1,receive2)
    for i in range(numtosend):
        stat('+')
        send2(i)
        receive1()
    end = time.time()
    p.terminate()
    sys.stdout.write('\n')
    print(name,end-start)

def main():
    q1 = m.Queue()
    q2 = m.Queue()
    doOne('queue',q1.put,q1.get,q2.put,q2.get)
    del q1
    del q2
    send,receive = m.Pipe()
    doOne('pipe',send.send,receive.recv,receive.send,send.recv)
    
    
if __name__ == '__main__':
    main()
