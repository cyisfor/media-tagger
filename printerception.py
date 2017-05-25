import sys

oldprint = print
def derprint(*a,**kw):
    import traceback
    try: raise ZeroDivisionError
    except:
        sys.stdout.write('\n'.join(traceback.format_stack()[:-1]))
    oldprint(*a,**kw)

print(__builtins__)
try:
	__builtins__.print = derprint
except AttributeError:
	# python sucks. arbitraily replaces __builtins__ with __builtins__.__dict__ but only in imported modules
	__builtins__['print'] = derprint


print('Print intercepted')
