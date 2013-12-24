import db

class Versioner:
    def __init__(self,kind):
        self.versions = []
        self.name = kind + 'Version';
        try:
            db.c.execute("CREATE TABLE "+self.name+" (latest int)")
            db.c.execute("INSERT INTO "+self.name+" (latest) VALUES (0)")
        except db.ProgrammingError: pass
    def setup(self):
        self.versions.sort(key=lambda pair: pair[0])
        version = db.c.execute("SELECT latest FROM "+self.name)
        if version:
            version = version[0][0]
        else:
            version = 0

        for testversion,setup in self.versions:
            if testversion > version:
                version = testversion
                setup()
                db.c.execute("UPDATE "+self.name+" SET latest = $1",(version,))

    def __call__(self,*a,version=0):
        def decorator(go):
            self.versions.append((version,go))
            return staticmethod(go)
        return decorator
