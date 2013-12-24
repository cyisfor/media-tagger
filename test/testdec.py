from pprint import pprint

def testdec(*a):
    def dec(f):
        pprint([(n,getattr(f,n)) for n in dir(f)])
        return f
    return dec

@testdec(42)
def test1(a,b,c=3):
    print("test1")

class base:
    versions = []

class beep:
    @testdec(23)
    def test2(self,a,b,c=5):
        print("test2")

test1(2,3)
beep().test2(4,2)
