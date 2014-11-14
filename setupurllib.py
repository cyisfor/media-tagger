from filedb import top
from contextlib import closing,contextmanager

from io import StringIO

import gzip,zlib
import sys
import os,tempfile
import urllib.request
Request = urllib.request.Request
import pickle
import shutil
import glob

isPypy = hasattr(pickle.Pickler,'dispatch')

proxy = urllib.request.ProxyHandler({"http": "http://127.0.0.1:8123"})
handlers = [proxy]

if not 'skipcookies' in os.environ:
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
        print('getting',ff_cookies)
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
    for ff_cookies in glob.glob(os.path.expanduser("~/.mozilla/firefox/*/cookies.sqlite")):
        get_cookies(jar,ff_cookies)

    with tempfile.NamedTemporaryFile(dir=os.path.join(top,"temp")) as out:
        pickler = MyPickler(out)
        pickler.dump(jar)
        if os.path.exists(cookiefile):
            os.unlink(cookiefile)
        os.rename(out.name,cookiefile)
        try: out.close()
        except OSError: pass
    handlers.append(urllib.request.HTTPCookieProcessor(jar))

opener = urllib.request.build_opener(*handlers)
opener.addheaders = [
        ('User-agent','Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0'),
        ('Accept-Encoding', 'gzip,deflate')]
urllib.request.install_opener(opener)

@contextmanager
def myopen(request):
    if not isinstance(request,Request):
        request = Request(request)
    try:
        request.full_url.encode('ascii')
    except UnicodeEncodeError as e:
        url = list(urllib.parse.urlparse(request.full_url))
        for i in range(2,len(url)):
            url[i] = urllib.parse.quote(url[i],safe="/&=?+")
        request.full_url = urllib.parse.urlunparse(url)
    with closing(opener.open(request)) as inp:
        headers = inp.headers
        encoding = headers['Content-Encoding']
        if encoding == 'gzip':
            inp = gzip.GzipFile(fileobj=inp,mode='rb')
        elif encoding == 'deflate':
            data = inp.read(0x40000)
            try: data = zlib.decompress(data)
            except zlib.error:
                data = zlib.decompress(data,-zlib.MAX_WBITS)
            inp = StringIO(data)
        inp.headers = headers
        yield inp

def myretrieve(request,dest):
    with myopen(request) as inp:
        shutil.copyfileobj(inp,dest)
        return inp.headers

print('urllib has been setup for proxying')
