import db
from tornado.gen import coroutine

class Versioner:
    def __init__(self,kind,after=None):
        self.versions = []
        self.name = kind + 'Version';
        self.after = after
    @coroutine
    def setup(self):
        #print(self.name)
        try:
            yield db.execute("CREATE TABLE "+self.name+" (latest int)")
            yield db.execute("INSERT INTO "+self.name+" (latest) VALUES (0)")
        except db.ProgrammingError: pass
        self.versions.sort(key=lambda pair: pair[0])
        version = yield db.execute("SELECT latest FROM "+self.name)
        if version:
            version = version[0][0]
        else:
            version = 0

        if self.after:
            after = yield db.execute('SELECT latest FROM'+self.after)
            if after:
                after = after[0][0]
            else:
                after = 0
        else:
            after = 0

        for testversion,setup in self.versions:
            #print(testversion,'>',version)
            if testversion > version:
                version = testversion
                yield from setup()
                yield db.execute("UPDATE "+self.name+" SET latest = $1",(version,))

    def __call__(self,version=0):
        def decorator(go):
            self.versions.append((version,go))
        return decorator
