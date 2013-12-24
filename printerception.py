import sys

oldprint = print
def derprint(*a,**kw):
    import traceback
    try: raise ZeroDivisionError
    except:
        sys.stdout.write('\n'.join(traceback.format_stack()[:-1]))
    oldprint(*a,**kw)

__builtins__.print = derprint

print('Print intercepted')
