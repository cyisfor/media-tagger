import os
if 'debug' in os.environ:
    import sys,time
    modules = set()
    here = os.path.dirname(__file__)
    def setroot(where):
        global here
        here = os.path.dirname(where) 
    def monitor(module=None):
        if module:
            if hasattr(module,'__name__'):
                module = module.__name__
        else:
            module = '__main__'
        modules.add(module)
    if hasattr(sys,'_getframe'):
        def getframe():
            return sys._getframe(2)
    else:
        def getframe():
            tb = sys.exc_info()[2]
            if not tb:
                try: raise Exception
                except Exception as e:
                    tb = e.__traceback__
                while tb.tb_next:
                    tb = tb.tb_next
            return tb.tb_frame.f_back.f_back
    def note(*s):
        f = getframe()
        # function above us
        if f.f_globals['__name__'] not in modules: return

        s = (str(s) for s in s)
        s = ' '.join(s)
        hasret = '\n' in s

        message = '== '+str(time.time())+' '+os.path.relpath(f.f_code.co_filename,here)+':'+str(f.f_lineno)
        if hasret:
            message += '\n'+'-'*60+'\n'
        else:
            message += '\n'
        message += s
        if hasret:
            message += '\n'+'-'*60
        else:
            message += ' '
        message += '\n'
        sys.stderr.write(message)
        sys.stderr.flush()
else:
    def note(*s): pass
    def monitor(mod=None): pass
