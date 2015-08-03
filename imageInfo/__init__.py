import note

import os
import subprocess
import struct

os.environ['LD_LIBRARY_PATH'] = '/opt/ImageMagick/lib'

here = os.path.dirname(__file__)
exe = os.path.join(here,'imageInfo')

if not os.path.exists(exe):
    os.chdir(here)
    subprocess.call(['make'])

def makeProcess():
    return subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
process = makeProcess()
def getProcess():
    global process
    if (not process) or (process.poll() is not None):
        process = makeProcess()
    return process

class Error(Exception): 
    def __getitem__(self,key):
        return self.args[0][key]

def readString(inp):
    size = inp.read(1)[0]
    return inp.read(size).decode('utf-8')

def get(path):
    global process
    getProcess()
    process.stdin.write((path+'\n').encode('utf-8'))
    process.stdin.flush()
    result = process.stdout.read(1).decode()
    if result == 'E':
        reason = readString(process.stdout)
        description = readString(process.stdout)
        error = readString(process.stdout)
        num = struct.unpack(">H",process.stdout.read(2))[0]
        print('error',description)
        raise Error({
            'reason': reason,
            'description': description,
            'error': error,
            'num': num})
    elif result == "I":
        type = readString(process.stdout)
        animated = (process.stdout.read(1)[0] > 1)
        width = struct.unpack('>H',process.stdout.read(2))[0]
        height = struct.unpack('>H',process.stdout.read(2))[0]
        note.blue('type found',type)
        return (animated,width,height),type
    else:
        print('unsync')
        process.terminate()
        process.wait()
        process = None
        raise Error("Subprocess got out of sync!")
