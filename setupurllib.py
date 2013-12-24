from filedb import top
from contextlib import closing

import sys
import os,tempfile
import urllib.request
import pickle
import shutil

isPypy = hasattr(pickle.Pickler,'dispatch')
if isPypy:
    print('ispypy')
    import copyreg
    import _thread
    import struct
    class DerpLock: pass
    class MyPickler(pickle.Pickler):
        def save_global(self,obj,name=None,pack=struct.pack):
            if isinstance(obj,_thread.RLock):
                obj = DerpLock()
            if obj is _thread.RLock:
                obj = DerpLock
            super().save_global(obj,name,pack)
        pickle.Pickler.dispatch[type] = save_global
    copyreg.pickle(DerpLock,lambda lock: '', _thread.RLock)
else:
    MyPickler = pickle.Pickler

import sqlite3
import http.cookiejar

def get_cookies(cj, ff_cookies):
    with closing(sqlite3.connect(ff_cookies)) as con:
        cur = con.cursor()
        cur.execute("SELECT host, path, isSecure, expiry, name, value FROM moz_cookies")
        for item in cur.fetchall():
            c = http.cookiejar.Cookie(0, item[4], item[5],
                None, False,
                item[0], item[0].startswith('.'), item[0].startswith('.'),
                item[1], False,
                item[2],
                item[3], item[3]=="",
                None, None, {})
            cj.set_cookie(c)

cookiefile = os.path.join(top,"temp","cookies.pickle")
try:
    with open(cookiefile,'rb') as inp:
        jar = pickle.load(inp)
    if isPypy:
        jar._cookies_lock = _thread.RLock()
except (IOError,AttributeError):
    jar = http.cookiejar.CookieJar()

get_cookies(jar,os.path.join(top,"cookies.sqlite"))
with tempfile.NamedTemporaryFile(dir=os.path.join(top,"temp")) as out:
    pickler = MyPickler(out)
    pickler.dump(jar)
    if os.path.exists(cookiefile):
        os.unlink(cookiefile)
    os.rename(out.name,cookiefile)
    try: out.close()
    except OSError: pass

proxy = urllib.request.ProxyHandler({"http": "http://127.0.0.1:8123"})
opener = urllib.request.build_opener(proxy,
        urllib.request.HTTPCookieProcessor(jar))
opener.addheaders = [('User-agent','Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0')]
urllib.request.install_opener(opener)

def myretrieve(request,dest):
    try:
        request.full_url.encode('ascii')
    except UnicodeEncodeError as e:
        url = list(urllib.parse.urlparse(request.full_url))
        for i in range(2,len(url)):
            url[i] = urllib.parse.quote(url[i])
        request.full_url = urllib.parse.urlunparse(url)
    try:
        with closing(opener.open(request)) as inp:
            shutil.copyfileobj(inp,dest)
            return inp.headers
    except: 
        print((request.get_data(),request.get_full_url(),request.headers),file=sys.stderr)
        raise

print('urllib has been setup for proxying')
